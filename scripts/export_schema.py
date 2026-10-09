import sys
from pathlib import Path
from sqlalchemy.schema import CreateTable, CreateIndex
from sqlalchemy.dialects import postgresql
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'backend'))
from app.db import Base
statements=[]
for table in Base.metadata.sorted_tables:
    statements.append(str(CreateTable(table).compile(dialect=postgresql.dialect()))+';')
    statements.extend(str(CreateIndex(i).compile(dialect=postgresql.dialect()))+';' for i in table.indexes)
(root/'docs/architecture/schema.sql').write_text('\n'.join(statements))
