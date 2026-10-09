"""Run real Gemini retrieval and generation evaluation; results are never precomputed."""

import argparse
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "backend"))
from app.config import settings
from app.db import DB
from app.rag import ask
from app.schemas import Query

parser = argparse.ArgumentParser()
parser.add_argument("--max-cases", type=int, choices=range(1, 5), default=4)
parser.add_argument(
    "--case-id", action="append", help="Select specific case IDs; repeat as needed"
)
args = parser.parse_args()
cfg = settings()
if (
    cfg.mode != "live"
    or not cfg.gemini_api_key
    or not cfg.external_calls_enabled
    or not cfg.gemini_free_tier_confirmed
):
    sys.exit(
        "Live evaluation requires MODE=live, GEMINI_API_KEY and verified unbilled Gemini policy flags. Fixture doubles cannot establish semantic quality."
    )
cases = json.loads((root / "data/structured/evaluation.json").read_text())
output = root / "docs/testing/live-rag-evaluation.json"
results = json.loads(output.read_text()) if output.exists() else []
completed = {r["id"] for r in results if "error" not in r}
if args.case_id:
    known = {case["id"] for case in cases}
    if set(args.case_id) - known:
        sys.exit("Unknown evaluation case ID")
    cases = [case for case in cases if case["id"] in args.case_id]
else:
    cases = [case for case in cases if case["id"] not in completed]
cases = cases[: args.max_cases]
selected = {case["id"] for case in cases}
results = [r for r in results if r["id"] not in selected]
with DB() as db:
    for case in cases:
        try:
            r = ask(db, settings().demo_username, Query(question=case["question"]))
            retrieved = {e["id"] for e in r["evidence"]}
            expected = set(case["expected_sources"])
            recall = len(retrieved & expected) / len(expected) if expected else None
            results.append(
                {
                    "id": case["id"],
                    "retrieval_recall": recall,
                    "support_correct": r["supported"] == case["supported"],
                    "citation_ids_valid": set(r["citations"]) <= retrieved,
                    "expected_terms_present": all(
                        t.lower() in r["answer"].lower() for t in case["expected_terms"]
                    ),
                    "response": r,
                    "human_grounding_review": "pending",
                }
            )
        except Exception as exc:
            db.rollback()
            results.append({"id": case["id"], "error": str(exc)})
output.write_text(json.dumps(results, indent=2) + "\n")
print(output)
print(
    f"Executed {len(cases)} cases; preserve failures and complete remaining cases within a later quota window."
)
