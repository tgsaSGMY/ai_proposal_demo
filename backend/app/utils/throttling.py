import asyncio
import logging
from app.config import THROTTLING_DELAY_SECONDS

logger = logging.getLogger(__name__)

async def apply_throttling_if_needed(needs_throttling: bool, user_id: str):
    """
    If the user has exceeded the project creation threshold for today,
    apply a delay to slow down their AI generation requests.
    """
    if needs_throttling:
        logger.info(f"Applying {THROTTLING_DELAY_SECONDS}s throttling for user {user_id}")
        await asyncio.sleep(THROTTLING_DELAY_SECONDS)
