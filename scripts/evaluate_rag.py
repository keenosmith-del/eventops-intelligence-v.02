"""Run real Gemini retrieval and generation evaluation; results are never precomputed."""

import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "backend"))
from app.config import settings
from app.db import DB
from app.rag import ask
from app.schemas import Query

if settings().mode != "live" or not settings().gemini_api_key:
    sys.exit(
        "Live evaluation requires MODE=live and GEMINI_API_KEY. Fixture doubles cannot establish semantic quality."
    )
cases = json.loads((root / "data/structured/evaluation.json").read_text())
results = []
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
            results.append({"id": case["id"], "error": str(exc)})
output = root / "docs/testing/live-rag-evaluation.json"
output.write_text(json.dumps(results, indent=2) + "\n")
print(output)
