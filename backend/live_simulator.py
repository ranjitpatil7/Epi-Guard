import asyncio
import uuid
import random
from datetime import datetime, timezone
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.realtime.event_bus import EventBus
from app.realtime.event_schema import IntelligenceEvent
from app.db.redis import redis_manager

regions = [1, 2, 3, 4, 5, 6, 7, 8]
event_types = ["RAINFALL_UPDATE", "WATER_QUALITY_UPDATE", "ANOMALY_DETECTED", "RISK_CHANGED", "COMMUNITY_REPORT"]

async def run_simulation():
    print("Starting JalRakshak Live Traffic Simulator...")
    print("Sending synthetic events to the EventBus every 2-4 seconds.")
    
    # Initialize Redis connection
    await redis_manager.connect()
    
    while True:
        try:
            region = random.choice(regions)
            event_type = random.choice(event_types)
            
            payload = {}
            if event_type == "RAINFALL_UPDATE":
                payload = {"rainfall": round(random.uniform(0, 200), 2)}
            elif event_type == "WATER_QUALITY_UPDATE":
                payload = {"wqi": round(random.uniform(10, 100), 2)}
            elif event_type == "ANOMALY_DETECTED":
                payload = {"anomaly_score": round(random.uniform(0.7, 1.0), 2)}
            elif event_type == "RISK_CHANGED":
                payload = {"risk_score": round(random.uniform(0.5, 1.0), 2), "risk_delta": round(random.uniform(0.1, 0.4), 2)}
            elif event_type == "COMMUNITY_REPORT":
                payload = {"severity": round(random.uniform(0, 1), 2), "keyword": random.choice(["fever", "diarrhea", "water", "flood"])}

            event = IntelligenceEvent(
                event_id=f"sim-{uuid.uuid4()}",
                event_type=event_type,
                region_id=region,
                source="live_simulator",
                timestamp=datetime.now(timezone.utc),
                payload=payload,
                correlation_id=f"sim-corr-{uuid.uuid4()}"
            )
            
            await EventBus.publish(event)
            print(f"Published {event_type} for Region {region}")
            
            # Wait for 2 to 4 seconds before sending the next event
            await asyncio.sleep(random.uniform(2, 4))
        except Exception as e:
            print(f"Error publishing event: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(run_simulation())
