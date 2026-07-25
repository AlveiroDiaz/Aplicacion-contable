from sqlalchemy import text
from app.core.database import engine

with engine.connect() as conn:
    conn.execute(text("ALTER TABLE empresas ADD COLUMN IF NOT EXISTS dv VARCHAR"))
    conn.commit()
    result = conn.execute(text("select column_name from information_schema.columns where table_name='empresas' order by ordinal_position"))
    print('empresas columns:')
    for row in result:
        print(row[0])
