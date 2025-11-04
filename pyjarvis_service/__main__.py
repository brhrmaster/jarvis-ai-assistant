"""Entry point for running as module: python -m pyjarvis_service"""

import asyncio
import sys
from loguru import logger
from .service import run_service

if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
    )
    
    try:
        asyncio.run(run_service())
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Service failed: {e}")
        sys.exit(1)
