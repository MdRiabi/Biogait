import asyncio
import sys
import os

# Ajout du backend au PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.db.session import SessionLocal
from app.models.alert import DetectionAlert

async def test():
    print("Testing DB insertion...")
    try:
        async with SessionLocal() as db:
            db.add(DetectionAlert(
                camera_id='test',
                identified=False,
                username='INCONNU',
                confidence=0.0,
                anonymized_image='data:image/jpeg;base64,1234',
                is_anomaly=True
            ))
            await db.commit()
            print('Success! No DB error.')
    except Exception as e:
        print(f"DB Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
