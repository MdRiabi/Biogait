import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from app.db.session import SessionLocal
from app.models.alert import DetectionAlert
from sqlalchemy.future import select

async def test():
    async with SessionLocal() as db:
        result = await db.execute(select(DetectionAlert).limit(1))
        alert = result.scalars().first()
        print(type(alert.timestamp), alert.timestamp)
        try:
            print(alert.timestamp.strftime("%H:%M:%S"))
        except Exception as e:
            print("ERROR:", e)

if __name__ == "__main__":
    asyncio.run(test())
