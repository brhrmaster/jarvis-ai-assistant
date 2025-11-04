"""
PyJarvis LLM Integration Module
Provides CLI for interacting with Ollama LLM and sending responses to PyJarvis
"""

from .llama_client import OllamaClient
from .cli import main
from .personas import PersonaFactory, PersonaStrategy
from .conversation_context import ConversationContext
from .recording_queue import AudioRecordingQueue, get_recording_queue, RecordingStatus, RecordingTask, RecordingResult

__all__ = [
    "OllamaClient",
    "main",
    "PersonaFactory",
    "PersonaStrategy",
    "ConversationContext",
    "AudioRecordingQueue",
    "get_recording_queue",
    "RecordingStatus",
    "RecordingTask",
    "RecordingResult",
]

