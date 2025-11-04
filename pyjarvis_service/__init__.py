"""
Windows Service for text-audio processing
"""

from .service import run_service
from .processor import TextProcessor
from .ipc import IpcServer

__all__ = ["run_service", "TextProcessor", "IpcServer"]

