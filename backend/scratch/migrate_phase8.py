import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import engine, AsyncSessionLocal
from app.models.domain import Base, HealthOfficial, InventoryItem, Region
from sqlalchemy import select

async def migrate_and_seed():
    async with engine.begin() as conn:
        # Create all tables (this is safe, existing tables are kept)
        await conn.run_sync(Base.metadata.create_all)
        print("Database tables created.")

    async with AsyncSessionLocal() as db:
        # Check if Inventory Items exist
        result = await db.execute(select(InventoryItem))
        items = result.scalars().all()
        if not items:
            print("Seeding Inventory Items...")
            db.add_all([
                InventoryItem(name="ORS Packets", current_stock=10000, minimum_threshold=1000, unit="packets"),
                InventoryItem(name="Water Purification Tablets", current_stock=25000, minimum_threshold=5000, unit="tablets"),
                InventoryItem(name="Vaccines (Cholera)", current_stock=5000, minimum_threshold=500, unit="vials"),
            ])
            await db.commit()

        # Check if Health Officials exist
        result = await db.execute(select(HealthOfficial))
        officials = result.scalars().all()
        if not officials:
            print("Seeding Health Officials...")
            # Fetch all regions
            reg_result = await db.execute(select(Region))
            regions = reg_result.scalars().all()
            for r in regions:
                db.add(HealthOfficial(
                    region_id=r.id,
                    name=f"Dr. Response ({r.district})",
                    contact_number="+919876543210",
                    email=f"official_{r.id}@jalrakshak.gov.in"
                ))
            await db.commit()

    print("Migration and seeding complete.")

if __name__ == "__main__":
    asyncio.run(migrate_and_seed())
