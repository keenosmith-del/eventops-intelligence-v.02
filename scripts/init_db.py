import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.db import initialize

initialize()
print("Application tables initialized; schema version 1 (additive create_all).")
