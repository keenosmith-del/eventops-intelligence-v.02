"""Static workflow wiring checks; credentialed execution still needs a live smoke test."""

import json
from pathlib import Path

for path in (Path(__file__).resolve().parents[1] / "automations/n8n").glob("*.json"):
    w = json.loads(path.read_text())
    names = {n["name"] for n in w["nodes"]}
    assert not w["active"]
    assert any(
        n["type"].endswith("webhook")
        and n["parameters"]["authentication"] == "headerAuth"
        for n in w["nodes"]
    )
    assert any(n["type"].endswith("httpRequest") for n in w["nodes"])
    for a, outputs in w["connections"].items():
        assert a in names
        for branch in outputs["main"]:
            for edge in branch:
                assert edge["node"] in names
    print(path.name + ": wiring and authenticated webhook valid")
