"""
TTS Processors - Strategy Pattern implementations
"""

from .base import TtsProcessor, TtsProcessorResult
from .gtts_processor import GttsProcessor
from .edge_tts_processor import EdgeTtsProcessor

__all__ = [
    "TtsProcessor",
    "TtsProcessorResult",
    "GttsProcessor",
    "EdgeTtsProcessor",
]

