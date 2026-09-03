import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.domain import HealthOfficial

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Handles automated alerting via SMS/Voice (mocked for development).
    """

    @staticmethod
    async def dispatch_critical_alert(db: AsyncSession, region_id: int, message: str) -> bool:
        """
        Dispatches a critical SMS alert to the registered health official for a region.
        """
        # 1. Fetch the registered health official for the region
        result = await db.execute(select(HealthOfficial).filter(HealthOfficial.region_id == region_id))
        official = result.scalars().first()

        if not official:
            logger.warning(f"No Health Official registered for Region {region_id}. Cannot dispatch alert.")
            return False

        # 2. Simulate Twilio API Call
        logger.info("=" * 60)
        logger.info("🚀 [TWILIO MOCK] DISPATCHING CRITICAL ALERT 🚀")
        logger.info(f"To: {official.name} ({official.contact_number})")
        logger.info(f"Region ID: {region_id}")
        logger.info(f"Message Payload: {message}")
        logger.info("=" * 60)

        # In a production environment, this is where the Twilio SDK would be invoked:
        # from twilio.rest import Client
        # client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        # message = client.messages.create(
        #     body=message,
        #     from_=TWILIO_PHONE_NUMBER,
        #     to=official.contact_number
        # )

        return True
