import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from app.db.session import engine
from sqlalchemy import text

async def test_pg():
    async with engine.connect() as conn:
        print("Connected to Postgres!")
        result = await conn.execute(text("SELECT count(*) FROM detection_alerts"))
        count = result.scalar()
        print("ALERTS COUNT IN POSTGRES:", count)
        
        result2 = await conn.execute(text("SELECT * FROM detection_alerts LIMIT 1"))
        print("FIRST ROW:", result2.mappings().all())

if __name__ == "__main__":
    asyncio.run(test_pg())
