import asyncio
from app.db.session import AsyncSessionLocal
from app.api.v1.risk import get_current_risk
from app.api.v1.regions import get_regions

async def test():
    db = AsyncSessionLocal()
    try:
        # Get data from backend
        risks_payload = await get_current_risk(db)
        risks = risks_payload.get('data', [])
        regions = await get_regions(db)
        
        region_ids = [r['id'] if isinstance(r, dict) else getattr(r, 'id', None) for r in regions]
        risk_region_ids = [r['region_id'] for r in risks]
        
        print(f"Total Regions in DB: {len(region_ids)} (IDs: {region_ids})")
        print(f"Total Regions with Risk Data: {len(risk_region_ids)} (IDs: {risk_region_ids})")
        
        # Verify intersection
        intersection = set(region_ids).intersection(set(risk_region_ids))
        print(f"Matching Region IDs: {len(intersection)}")
        
        # Verify color assignment logic
        print("\n--- Map Color Assignment Verification ---")
        for risk in risks:
            region_id = risk['region_id']
            # Mimic MapView.tsx score logic
            score = risk.get('estimated_risk_score', risk.get('risk_score', 0))
            
            # Mimic MapView.tsx color logic
            if score >= 80:
                color = "#ef4444"
                state = "Critical (Red)"
            elif score >= 60:
                color = "#f97316"
                state = "High (Orange)"
            elif score >= 40:
                color = "#eab308"
                state = "Moderate (Yellow)"
            else:
                color = "#10b981"
                state = "Guarded/Low (Green)"
                
            print(f"Region ID {region_id:2} | Score: {score:5.1f} | Expected Color: {color} | Risk State: {state}")
            
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(test())
