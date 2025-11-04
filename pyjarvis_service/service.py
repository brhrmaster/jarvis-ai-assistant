"""
Windows Service implementation
"""

import asyncio
from loguru import logger
from .processor import TextProcessor
from .ipc import IpcServer


async def run_service() -> None:
    """Main service entry point"""
    logger.info("Initializing PyJarvis Service")
    logger.debug("Creating text processor...")
    
    # Initialize text processor with config
    from pyjarvis_shared import AppConfig
    config = AppConfig()
    processor = TextProcessor(config)
    await processor.initialize()
    logger.debug("Text processor initialized successfully")
    
    # Start IPC server
    logger.info("Starting IPC server...")
    ipc_server = IpcServer()
    
    try:
        # Start IPC server (this will run until stopped)
        await ipc_server.start(processor)
    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
        ipc_server.stop()
    except Exception as e:
        logger.error(f"Service error: {e}")
        ipc_server.stop()
        raise
    
    logger.info("Service started successfully")
    logger.info("Service is running. Press Ctrl+C to stop.")


if __name__ == "__main__":
    # Configure logging
    from loguru import logger
    import sys
    
    logger.remove()
    logger.add(
        sys.stdout,
        level="DEBUG",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
    )
    
    # Run service
    asyncio.run(run_service())

