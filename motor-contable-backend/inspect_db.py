from app.core.config import settings
from app.core.database import engine
from sqlalchemy import text
print('URL', settings.DATABASE_URL)
with engine.connect() as conn:
    print('connection ok')
    result = conn.execute(text("select table_schema, table_name, column_name from information_schema.columns where table_name='empresas' order by ordinal_position"))
    for row in result:
        print(row)
