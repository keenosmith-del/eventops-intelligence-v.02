import re
import unicodedata
from collections import defaultdict
from .schemas import Attendee, Participant


def normalized(value):
    return " ".join(unicodedata.normalize("NFKC", value or "").strip().split())


def email_key(value):
    return normalized(value).casefold()


def name_key(value):
    return normalized(value).casefold()


def verify(attendees, directory, event_id, failures=()):
    directory = [Participant.model_validate(r).model_dump() for r in directory]
    by_email = defaultdict(list)
    by_id = defaultdict(list)
    for r in directory:
        by_email[email_key(r["email"])].append(r)
        by_id[r["participant_id"]].append(r)
    groups = defaultdict(list)
    id_emails = defaultdict(set)
    for raw in attendees:
        a = Attendee.model_validate(raw).model_dump()
        original = a.copy()
        a["name"] = normalized(a["name"]) or None
        a["email"] = email_key(a["email"]) or None
        a["organization"] = normalized(a["organization"]) or None
        key = a["email"] or (
            "id:" + a["participant_id"]
            if a["participant_id"]
            else "source:" + a["source_id"]
        )
        if a["participant_id"] and a["email"]:
            id_emails[a["participant_id"]].add(a["email"])
        a["_original"] = original
        groups[key].append(a)
    results = []
    for records in groups.values():
        # Registration owns submitted fields; directory never silently replaces them.
        records.sort(key=lambda r: r["source_type"] != "gmail")
        candidate = {k: v for k, v in records[0].items() if k != "_original"}
        reasons = []
        status = "verified"
        emails = {a["email"] for a in records if a["email"]}
        ids = {a["participant_id"] for a in records if a["participant_id"]}
        matches = by_email.get(candidate["email"], []) or (
            by_id.get(candidate["participant_id"], [])
            if candidate["participant_id"]
            else []
        )
        if not candidate["name"]:
            reasons.append("Missing attendee name")
        if not candidate["email"]:
            reasons.append("Missing email")
        elif not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", candidate["email"]):
            reasons.append("Invalid email format")
        if len([r for r in records if r["source_type"] == "gmail"]) > 1:
            reasons.append("Duplicate registration messages")
        if len([r for r in records if r["source_type"] == "calendar"]) > 1:
            reasons.append("Duplicate calendar invitations")
        if any(len(id_emails[pid]) > 1 for pid in ids):
            reasons.append("Participant identifier appears under multiple emails")
        if len(ids) > 1 or len(emails) > 1:
            reasons.append("Conflicting participant identifiers")
        if not any(r["source_type"] == "gmail" for r in records):
            reasons.append("Missing registration evidence")
        if not any(r["source_type"] == "calendar" for r in records):
            reasons.append("Missing calendar invitation")
        if any(a["event_id"] not in (None, event_id) for a in records):
            reasons.append("Source event identifier mismatch")
        authority = matches[0] if len(matches) == 1 else None
        if not authority:
            reasons.append("No unique authoritative directory match")
            status = (
                "unverified"
                if not matches and candidate["email"]
                else "review_required"
            )
        else:
            if not authority["active"]:
                reasons.append("Inactive participant")
            if event_id not in authority["event_ids"]:
                reasons.append("Participant is not eligible for this event")
            for a in records:
                if (
                    a["participant_id"]
                    and a["participant_id"] != authority["participant_id"]
                ):
                    reasons.append("Participant identifier mismatch")
                if a["email"] and a["email"] != email_key(authority["email"]):
                    reasons.append("Email conflicts with directory")
                if a["name"] and name_key(a["name"]) != name_key(authority["name"]):
                    reasons.append("Name conflicts with directory")
                if a["organization"] and name_key(a["organization"]) != name_key(
                    authority["organization"]
                ):
                    reasons.append("Organization conflicts with directory")
            if not candidate["organization"]:
                reasons.append("Missing registration organization")
            if not candidate["participant_id"]:
                reasons.append("Missing registration participant identifier")
        if failures:
            reasons.append("Source information unavailable: " + ", ".join(failures))
        if reasons and status == "verified":
            status = "review_required"
        evidence = [
            {
                "source_type": a["source_type"],
                "source_id": a["source_id"],
                "original": a["_original"],
            }
            for a in records
        ]
        if authority:
            evidence.append(
                {
                    "source_type": "web",
                    "source_id": authority["record_id"],
                    "original": authority,
                }
            )
        results.append(
            {
                "status": status,
                "record": {
                    **candidate,
                    "event_id": event_id,
                    "directory_match": authority,
                },
                "evidence": evidence,
                "reasons": list(dict.fromkeys(reasons))
                or [
                    "Active directory match, consistent invitation and registration evidence"
                ],
            }
        )
    return results
