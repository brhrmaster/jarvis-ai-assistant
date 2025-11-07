"""
Unit tests for pyjarvis_shared.messages module
"""
import pytest
from pyjarvis_shared import (
    TextToVoiceRequest,
    VoiceProcessingUpdate,
    ProcessingStatus,
    Emotion,
    Language,
    ServiceCommand,
    ServiceResponse
)


class TestTextToVoiceRequest:
    """Tests for TextToVoiceRequest model"""
    
    def test_text_to_voice_request_creation(self):
        """Test creating a TextToVoiceRequest"""
        request = TextToVoiceRequest(text="Hello, world!")
        assert request.text == "Hello, world!"
        assert request.language is None
        assert request.emotion is None
    
    def test_text_to_voice_request_with_options(self):
        """Test creating a TextToVoiceRequest with language and emotion"""
        request = TextToVoiceRequest(
            text="Hello",
            language=Language.ENGLISH,
            emotion=Emotion.HAPPY
        )
        assert request.text == "Hello"
        assert request.language == Language.ENGLISH
        assert request.emotion == Emotion.HAPPY


class TestVoiceProcessingUpdate:
    """Tests for VoiceProcessingUpdate model"""
    
    def test_voice_processing_update_creation(self):
        """Test creating a VoiceProcessingUpdate"""
        update = VoiceProcessingUpdate(
            status=ProcessingStatus.PROCESSING,
            message="Processing text..."
        )
        assert update.status == ProcessingStatus.PROCESSING
        assert update.message == "Processing text..."
        assert update.audio_file is None
        assert update.subject is None


class TestServiceCommand:
    """Tests for ServiceCommand model"""
    
    def test_service_command_process_text(self):
        """Test creating a ProcessText command"""
        command = ServiceCommand.process_text("Hello, world!")
        assert command.command_type == "ProcessText"
        assert command.text == "Hello, world!"
    
    def test_service_command_ping(self):
        """Test creating a Ping command"""
        command = ServiceCommand.ping()
        assert command.command_type == "Ping"
    
    def test_service_command_serialization(self):
        """Test ServiceCommand JSON serialization"""
        command = ServiceCommand.process_text("Test")
        json_data = command.model_dump()
        assert json_data["command_type"] == "ProcessText"
        assert json_data["text"] == "Test"


class TestServiceResponse:
    """Tests for ServiceResponse model"""
    
    def test_service_response_creation(self):
        """Test creating a ServiceResponse"""
        response = ServiceResponse(
            success=True,
            message="Operation completed"
        )
        assert response.success is True
        assert response.message == "Operation completed"
        assert response.data is None


