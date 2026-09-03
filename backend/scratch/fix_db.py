import asyncio
from datetime import datetime, timezone
from app.db.session import AsyncSessionLocal
from app.models.domain import ModelVersion, Region

async def fix_db():
    async with AsyncSessionLocal() as db:
        # Add active model if missing
        model = ModelVersion(
            version="ensemble-v1.0.0",
            training_date=datetime.now(timezone.utc),
            dataset_version="v1.2",
            precision=0.89,
            recall=0.85,
            f1_score=0.87,
            roc_auc=0.92,
            pr_auc=0.88,
            calibration=0.95
        )
        db.add(model)
        
        # Add 8th Region to fix the IntegrityError for live_simulator
        reg = Region(id=8, name="Barak Valley", state="Assam State", district="Cachar", population=400000)
        db.add(reg)
        
        try:
            await db.commit()
            print("Successfully inserted ModelVersion and Region 8")
        except Exception as e:
            await db.rollback()
            print("Error inserting:", e)

if __name__ == "__main__":
    asyncio.run(fix_db())
