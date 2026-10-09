"""Export credential-free, bounded, read-only n8n API workflows."""

import json
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]


def node(name, kind, parameters, x, version=1, credentials=None):
    n = {
        "id": name.lower().replace(" ", "-"),
        "name": name,
        "type": "n8n-nodes-base." + kind,
        "typeVersion": version,
        "position": [x, 0],
        "parameters": parameters,
    }
    if credentials:
        n["credentials"] = credentials
    return n


def code(name, js, x):
    return node(name, "code", {"jsCode": js}, x, 2)


def http(name, url, x, credential=None, query=None):
    p = {"url": url, "options": {"timeout": 20000}}
    if query:
        p.update(
            {
                "sendQuery": True,
                "queryParameters": {
                    "parameters": [{"name": k, "value": v} for k, v in query.items()]
                },
            }
        )
    if credential:
        p.update(
            {
                "authentication": "predefinedCredentialType",
                "nodeCredentialType": credential,
            }
        )
    n = node(
        name,
        "httpRequest",
        p,
        x,
        4.2,
        {
            credential: {
                "id": "ASSIGN_IN_N8N",
                "name": "Dedicated synthetic Google account",
            }
        }
        if credential
        else None,
    )
    n.update({"retryOnFail": True, "maxTries": 3, "waitBetweenTries": 1000})
    return n


for tool in ["calendar", "gmail", "web"]:
    webhook = node(
        "Authenticated webhook",
        "webhook",
        {
            "httpMethod": "POST",
            "path": "eventops-" + tool,
            "authentication": "headerAuth",
            "responseMode": "responseNode",
            "options": {},
        },
        0,
        2,
        {"httpHeaderAuth": {"id": "ASSIGN_IN_N8N", "name": "EventOps webhook key"}},
    )
    validate = code(
        "Validate event",
        "const ZERO_COST_APPROVED=false; if(!ZERO_COST_APPROVED) throw new Error('External calls disabled by zero-cost policy'); const e=$json.body?.event_id; if(!/^EVT-(101|102|103)$/.test(e||'')) throw new Error('Event is not allowed'); return [{json:{event_id:e}}];",
        220,
    )
    nodes = [webhook, validate]
    links = [("Authenticated webhook", "Validate event")]
    if tool == "calendar":
        nodes.append(
            http(
                "Read calendar",
                "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                440,
                "googleCalendarOAuth2Api",
                {
                    "q": "={{ $json.event_id }}",
                    "maxResults": "100",
                    "singleEvents": "true",
                },
            )
        )
        nodes.append(
            code(
                "Envelope",
                "if(($json.items||[]).length>100 || $json.nextPageToken) throw new Error('Calendar result limit exceeded'); const e=$('Validate event').first().json.event_id; const data=($json.items||[]).filter(x=>(x.summary||'').includes(e)||(x.description||'').includes(e)); return [{json:{data,complete:true}}];",
                660,
            )
        )
        links += [("Validate event", "Read calendar"), ("Read calendar", "Envelope")]
    elif tool == "web":
        nodes.append(
            http(
                "Read directory",
                "https://REPLACE_WITH_VERCEL_HOST/reference/directory.json",
                440,
            )
        )
        nodes.append(
            code(
                "Envelope",
                "const data=$input.all().map(i=>i.json); if(data.length>500 || data.some(r=>!r.record_id || !r.email || !r.participant_id || !Array.isArray(r.event_ids))) throw new Error('Invalid directory'); return [{json:{data,complete:true}}];",
                660,
            )
        )
        links += [("Validate event", "Read directory"), ("Read directory", "Envelope")]
    else:
        nodes.append(
            http(
                "Search registrations",
                "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                440,
                "gmailOAuth2",
                {"q": "={{ 'subject:(' + $json.event_id + ')' }}", "maxResults": "20"},
            )
        )
        nodes.append(
            code(
                "Bound message IDs",
                "if($json.nextPageToken) throw new Error('Mailbox result limit exceeded'); const messages=$json.messages||[]; if(messages.length>20) throw new Error('Mailbox record limit exceeded'); return messages.length?messages.map(m=>({json:{id:m.id,has_messages:true}})):[{json:{has_messages:false}}];",
                660,
            )
        )
        nodes.append(
            node(
                "Has messages",
                "if",
                {
                    "conditions": {
                        "options": {"caseSensitive": True, "typeValidation": "strict"},
                        "conditions": [
                            {
                                "id": "has",
                                "leftValue": "={{ $json.has_messages }}",
                                "rightValue": True,
                                "operator": {
                                    "type": "boolean",
                                    "operation": "true",
                                    "singleValue": True,
                                },
                            }
                        ],
                        "combinator": "and",
                    },
                    "options": {},
                },
                880,
                2.2,
            )
        )
        nodes.append(
            http(
                "Read message",
                "={{ 'https://gmail.googleapis.com/gmail/v1/users/me/messages/' + $json.id }}",
                1100,
                "gmailOAuth2",
                {"format": "full"},
            )
        )
        nodes.append(
            code(
                "Envelope",
                "function body(p){if(p.parts)return p.parts.filter(x=>x.mimeType!=='text/html').map(body).join('\\n').slice(0,20000);return p.mimeType==='text/plain'?Buffer.from(p.body?.data||'', 'base64url').toString('utf8').slice(0,20000):'';}const data=$input.all().map(i=>{const m=i.json,p=m.payload||{};return {id:m.id,subject:(p.headers||[]).find(h=>h.name.toLowerCase()==='subject')?.value||'',body:body(p)};});return [{json:{data,complete:true}}];",
                1320,
            )
        )
        nodes.append(
            code("Empty envelope", "return [{json:{data:[],complete:true}}];", 1100)
        )
        links += [
            ("Validate event", "Search registrations"),
            ("Search registrations", "Bound message IDs"),
            ("Bound message IDs", "Has messages"),
            ("Has messages", "Read message"),
            ("Read message", "Envelope"),
        ]
    nodes.append(
        node(
            "Respond",
            "respondToWebhook",
            {"respondWith": "json", "responseBody": "={{ $json }}", "options": {}},
            1540,
            1.4,
        )
    )
    links.append(("Envelope", "Respond"))
    connections = {
        a: {"main": [[{"node": b, "type": "main", "index": 0}]]} for a, b in links
    }
    if tool == "gmail":
        connections["Has messages"]["main"].append(
            [{"node": "Empty envelope", "type": "main", "index": 0}]
        )
        connections["Empty envelope"] = {
            "main": [[{"node": "Respond", "type": "main", "index": 0}]]
        }
    workflow = {
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, "eventops-" + tool)),
        "versionId": str(uuid.uuid5(uuid.NAMESPACE_URL, "eventops-" + tool + "-v1")),
        "name": "EventOps read " + tool,
        "nodes": nodes,
        "connections": connections,
        "active": False,
        "settings": {
            "executionOrder": "v1",
            "executionTimeout": 600,
            "saveDataErrorExecution": "all",
            "saveDataSuccessExecution": "none",
            "saveManualExecutions": False,
        },
        "pinData": {},
        "tags": [],
    }
    (root / "automations/n8n" / f"{tool}.json").write_text(
        json.dumps(workflow, indent=2) + "\n"
    )
