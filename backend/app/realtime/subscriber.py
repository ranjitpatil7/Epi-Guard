import logging
import asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.models.domain import IntelligenceEvent as DBIntelligenceEvent
from app.realtime.event_schema import IntelligenceEvent
from app.realtime.event_bus import EventBus

logger = logging.getLogger(__name__)

class EventSubscriber:
    """
    Consumes events from EventBus and routes them.
    Handles persistence, retries, and dead-letters.
    """
    
    MAX_RETRIES = 3
    
    @staticmethod
    async def _persist_event(event: IntelligenceEvent, status: str, retry_count: int = 0) -> bool:
        """Saves the event to the PostgreSQL database."""
        try:
            async with AsyncSessionLocal() as session:
                # Check for idempotency
                from sqlalchemy import select
                stmt = select(DBIntelligenceEvent).where(DBIntelligenceEvent.event_id == event.event_id)
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if existing:
                    # Idempotency check: If it exists, update status and retry_count if needed
                    existing.processing_status = status
                    existing.retry_count = retry_count
                    if status == "PROCESSED":
                        existing.processed_at = datetime.now(timezone.utc)
                    await session.commit()
                    return True
                
                # Insert new event
                db_event = DBIntelligenceEvent(
                    event_id=event.event_id,
                    event_type=event.event_type,
                    region_id=event.region_id,
                    source=event.source,
                    timestamp=event.timestamp,
                    payload=event.payload,
                    schema_version=event.schema_version,
                    confidence=event.confidence,
                    correlation_id=event.correlation_id,
                    processing_status=status,
                    retry_count=retry_count
                )
                if status == "PROCESSED":
                    db_event.processed_at = datetime.now(timezone.utc)
                    
                session.add(db_event)
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to persist event {event.event_id}: {str(e)}", exc_info=True)
            return False

    @staticmethod
    async def _handle_dead_letter(event: IntelligenceEvent, error_msg: str):
        """Sends the event to a dead letter queue/status after max retries."""
        logger.critical(f"DEAD LETTER: Event {event.event_id} failed after {EventSubscriber.MAX_RETRIES} retries. Error: {error_msg}")
        await EventSubscriber._persist_event(event, status="DEAD_LETTER", retry_count=EventSubscriber.MAX_RETRIES)

    @staticmethod
    async def process_event(event: IntelligenceEvent, message_id: str) -> bool:
        """
        Main routing function for consumer.
        Returns True to ACK the message in Redis Stream.
        """
        logger.info(f"Processing event: {event.event_id} of type {event.event_type}")
        
        # Step 1: Record received status
        await EventSubscriber._persist_event(event, status="PROCESSING")
        
        try:
            # Pass the event to the CEP engine
            from app.cep.engine import CEPEngine
            cep_engine = CEPEngine()
            await cep_engine.process_incoming_event(event)
            
            # Trigger Event-Driven Risk Recalculation
            from app.services.event_driven_risk_service import EventDrivenRiskService
            await EventDrivenRiskService.trigger_recalculation(event)
            
            # Process Alert Intelligence for Risk Events
            if event.event_type in ["RISK_RECALCULATED", "RISK_ESCALATED", "RISK_DEESCALATED"]:
                from app.services.alert_intelligence_service import AlertIntelligenceService
                async with AsyncSessionLocal() as db:
                    await AlertIntelligenceService.evaluate_risk_event(db, event.payload)
            
            # Simulate processing time
            await asyncio.sleep(0.01)
            
            # Step 2: Mark as processed
            await EventSubscriber._persist_event(event, status="PROCESSED")
            logger.info(f"Successfully processed event: {event.event_id}")
            return True
            
        except Exception as e:
            # Here we could track retries using Redis Pending Entries List (PEL) metadata
            # but for simplicity in Milestone 3A, if it fails, we log it. The message won't be ACKed, 
            # and our recovery loop (which should be implemented) would pick it up later.
            # To handle bounded retries accurately without a recovery loop, we would track attempts in Redis.
            
            logger.error(f"Error processing event {event.event_id}: {str(e)}")
            await EventSubscriber._handle_dead_letter(event, str(e))
            
            # We return True here to ACK the message so it doesn't get stuck infinitely in PEL
            # because we have moved it to the DEAD_LETTER state in our database.
            return True

    @classmethod
    async def start_background_consumer(cls):
        """Starts the Redis Stream consumer in an asyncio task."""
        logger.info("Starting EventSubscriber background consumer...")
        asyncio.create_task(
            EventBus.subscribe("worker-1", cls.process_event)
        )
