import asyncio
import random
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.models.domain import Region, DataSource, EnvironmentalData, WaterQualityRecord, DiseaseRecord, CommunityReport
from app.services.providers.simulation import SimulationDataProvider
from app.services.data_quality_service import DataQualityEngine
from app.schemas.ingestion import IngestEnvironmentalData, IngestWaterQualityData, IngestDiseaseData, IngestCommunityReport
from geoalchemy2.elements import WKTElement

async def seed_regions(db: AsyncSession):
    # Northeast India approximate boxes
    regions_data = [
        {"name": "Assam State", "state": "Assam", "type": "State", "wkt": "POLYGON((89.0 24.0, 96.0 24.0, 96.0 28.0, 89.0 28.0, 89.0 24.0))"},
        {"name": "Kamrup Metro", "state": "Assam", "district": "Kamrup", "wkt": "POLYGON((91.5 26.0, 92.0 26.0, 92.0 26.5, 91.5 26.5, 91.5 26.0))"},
        {"name": "Dibrugarh", "state": "Assam", "district": "Dibrugarh", "wkt": "POLYGON((94.5 27.0, 95.5 27.0, 95.5 27.8, 94.5 27.8, 94.5 27.0))"},
        {"name": "Meghalaya State", "state": "Meghalaya", "type": "State", "wkt": "POLYGON((89.8 25.0, 92.8 25.0, 92.8 26.1, 89.8 26.1, 89.8 25.0))"},
        {"name": "East Khasi Hills", "state": "Meghalaya", "district": "East Khasi Hills", "wkt": "POLYGON((91.5 25.2, 92.0 25.2, 92.0 25.6, 91.5 25.6, 91.5 25.2))"},
        {"name": "Manipur State", "state": "Manipur", "type": "State", "wkt": "POLYGON((93.0 23.8, 94.8 23.8, 94.8 25.7, 93.0 25.7, 93.0 23.8))"},
        {"name": "Imphal West", "state": "Manipur", "district": "Imphal West", "wkt": "POLYGON((93.8 24.7, 94.0 24.7, 94.0 25.0, 93.8 25.0, 93.8 24.7))"}
    ]
    
    region_objs = []
    for rd in regions_data:
        geom = WKTElement(rd["wkt"], srid=4326)
        r = Region(name=rd["name"], state=rd["state"], district=rd.get("district"), geometry=geom, population=random.randint(50000, 2000000))
        db.add(r)
        region_objs.append(r)
    
    await db.commit()
    for r in region_objs:
        await db.refresh(r)
    return region_objs

async def seed_data():
    async with AsyncSessionLocal() as db:
        # Create Data Source
        ds = DataSource(
            name="JalRakshak AI Simulation Engine",
            source_type="Simulator",
            data_type="SIMULATED",
            processing_status="COMPLETED",
            data_quality_score=98.5
        )
        db.add(ds)
        await db.commit()
        await db.refresh(ds)
        
        # Seed Regions
        regions = await seed_regions(db)
        
        provider = SimulationDataProvider()
        engine = DataQualityEngine()
        
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=90) # 3 months of historical data
        
        for region in regions:
            # 1. Environmental Data
            env_raw = await provider.fetch_environmental_data(region.id, start_date, end_date)
            env_result = engine.evaluate_batch(env_raw, IngestEnvironmentalData)
            for item in env_result["accepted"]:
                record = EnvironmentalData(
                    region_id=item.region_id,
                    data_source_id=ds.id,
                    timestamp=item.timestamp,
                    temperature=item.temperature,
                    rainfall=item.rainfall,
                    humidity=item.humidity
                )
                db.add(record)
                
            # 2. Water Quality
            wq_raw = await provider.fetch_water_quality_data(region.id, start_date, end_date)
            wq_result = engine.evaluate_batch(wq_raw, IngestWaterQualityData)
            for item in wq_result["accepted"]:
                # Generate a random point inside the bounding box (simplified for demo)
                # We'll just put it near the region center roughly
                lon = 91.5 + random.uniform(-0.5, 0.5)
                lat = 26.0 + random.uniform(-0.5, 0.5)
                pt = WKTElement(f"POINT({lon} {lat})", srid=4326)
                
                record = WaterQualityRecord(
                    region_id=item.region_id,
                    data_source_id=ds.id,
                    timestamp=item.timestamp,
                    turbidity=item.turbidity,
                    ph=item.ph,
                    coliform_presence=item.coliform_presence,
                    location=pt
                )
                db.add(record)
                
            # 3. Disease Data
            dis_raw = await provider.fetch_disease_data(region.id, start_date, end_date)
            dis_result = engine.evaluate_batch(dis_raw, IngestDiseaseData)
            for item in dis_result["accepted"]:
                record = DiseaseRecord(
                    region_id=item.region_id,
                    data_source_id=ds.id,
                    date=item.date,
                    disease_type=item.disease_type,
                    case_count=item.case_count
                )
                db.add(record)
                
            # 4. Community Reports
            cr_raw = await provider.fetch_community_reports(region.id, start_date, end_date)
            cr_result = engine.evaluate_batch(cr_raw, IngestCommunityReport)
            for item in cr_result["accepted"]:
                lon = 91.5 + random.uniform(-0.5, 0.5)
                lat = 26.0 + random.uniform(-0.5, 0.5)
                pt = WKTElement(f"POINT({lon} {lat})", srid=4326)
                
                record = CommunityReport(
                    # reporter_id will be null for anon demo
                    location=pt,
                    text_content=item.text_content,
                    nlp_severity=item.nlp_severity,
                    status="PENDING",
                    created_at=item.timestamp
                )
                db.add(record)
                
        await db.commit()
        print("Demo data seeded successfully.")

if __name__ == "__main__":
    asyncio.run(seed_data())
