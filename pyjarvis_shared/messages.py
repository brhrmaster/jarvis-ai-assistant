"""
IPC message types for communication between components
"""

from enum import Enum
from typing import Optional
from dataclasses import dataclass, field
from pydantic import BaseModel


class ProcessingStatus(str, Enum):
    """Processing status"""
    ANALYZING = "Analyzing"
    GENERATING = "Generating"
    READY = "Ready"
    ERROR = "Error"


class Emotion(str, Enum):
    """Detected emotions for facial expressions"""
    NEUTRAL = "Neutral"
    HAPPY = "Happy"
    SAD = "Sad"
    EXCITED = "Excited"
    CALM = "Calm"
    QUESTIONING = "Questioning"


class Language(str, Enum):
    """Supported languages"""
    ENGLISH = "English"
    PORTUGUESE = "Portuguese"
    SPANISH = "Spanish"


@dataclass
class TextToVoiceRequest:
    """Message sent from CLI to Service"""
    text: str
    language: Optional[str] = None


@dataclass
class VoiceProcessingUpdate:
    """Message sent from Service to UI"""
    status: ProcessingStatus
    audio_data: Optional[bytes] = None  # Deprecated: use audio_file_path instead
    audio_file_path: Optional[str] = None  # Path to audio file (preferred)
    emotion: Optional[Emotion] = None
    subject: Optional[str] = None


class ServiceCommand(BaseModel):
    """Service command messages"""
    command_type: str
    request: Optional[dict] = None
    
    @classmethod
    def process_text(cls, request: TextToVoiceRequest) -> "ServiceCommand":
        """Create a ProcessText command"""
        return cls(
            command_type="ProcessText",
            request={
                "text": request.text,
                "language": request.language
            }
        )
    
    @classmethod
    def register_ui(cls) -> "ServiceCommand":
        """Create a RegisterUI command"""
        return cls(command_type="RegisterUI")
    
    @classmethod
    def shutdown(cls) -> "ServiceCommand":
        """Create a Shutdown command"""
        return cls(command_type="Shutdown")
    
    @classmethod
    def ping(cls) -> "ServiceCommand":
        """Create a Ping command"""
        return cls(command_type="Ping")


class ServiceResponse(BaseModel):
    """Service response messages"""
    response_type: str
    update: Optional[dict] = None
    error: Optional[str] = None
    
    @classmethod
    def ack(cls) -> "ServiceResponse":
        """Create an Ack response"""
        return cls(response_type="Ack")
    
    @classmethod
    def pong(cls) -> "ServiceResponse":
        """Create a Pong response"""
        return cls(response_type="Pong")
    
    @classmethod
    def create_update(cls, update: VoiceProcessingUpdate) -> "ServiceResponse":
        """Create an Update response"""
        # Convert status
        status_str = update.status.value if hasattr(update.status, 'value') else str(update.status)
        
        # Convert audio_data to hex string if present
        audio_data_hex = None
        if update.audio_data:
            try:
                audio_data_hex = update.audio_data.hex()
            except Exception as e:
                # If conversion fails, log but continue
                import logging
                logging.warning(f"Failed to convert audio_data to hex: {e}")
        
        # Convert emotion
        emotion_str = None
        if update.emotion:
            emotion_str = update.emotion.value if hasattr(update.emotion, 'value') else str(update.emotion)
        
        # Include audio_file_path if present (preferred over audio_data)
        audio_file_path = None
        if update.audio_file_path:
            audio_file_path = str(update.audio_file_path)
        
        update_dict = {
            "status": status_str,
            "audio_data": audio_data_hex,  # Deprecated, kept for backward compatibility
            "audio_file_path": audio_file_path,  # Preferred
            "emotion": emotion_str,
            "subject": update.subject,
        }
        return cls(response_type="Update", update=update_dict)
    
    @classmethod
    def create_error(cls, error_msg: str) -> "ServiceResponse":
        """Create an Error response"""
        return cls(response_type="Error", error=error_msg)
    
    # Keep old names for backward compatibility (but they won't work with Pydantic v2)
    # Use create_update and create_error instead
