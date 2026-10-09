import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.db import initialize, DB
from app.rag import ingest
initialize()
with DB() as db: print(ingest(db))
