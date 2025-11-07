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
        # TextToVoiceRequest doesn't have emotion field
    
    def test_text_to_voice_request_with_options(self):
        """Test creating a TextToVoiceRequest with language"""
        request = TextToVoiceRequest(
            text="Hello",
            language="en"  # language is Optional[str], not Language enum
        )
        assert request.text == "Hello"
        assert request.language == "en"


class TestVoiceProcessingUpdate:
    """Tests for VoiceProcessingUpdate model"""
    
    def test_voice_processing_update_creation(self):
        """Test creating a VoiceProcessingUpdate"""
        update = VoiceProcessingUpdate(
            status=ProcessingStatus.ANALYZING  # Use ANALYZING instead of PROCESSING
        )
        assert update.status == ProcessingStatus.ANALYZING
        assert update.audio_file_path is None
        assert update.subject is None


class TestServiceCommand:
    """Tests for ServiceCommand model"""
    
    def test_service_command_process_text(self):
        """Test creating a ProcessText command"""
        request = TextToVoiceRequest(text="Hello, world!")
        command = ServiceCommand.process_text(request)
        assert command.command_type == "ProcessText"
        assert command.request is not None
        assert command.request["text"] == "Hello, world!"
    
    def test_service_command_ping(self):
        """Test creating a Ping command"""
        command = ServiceCommand.ping()
        assert command.command_type == "Ping"
    
    def test_service_command_serialization(self):
        """Test ServiceCommand JSON serialization"""
        request = TextToVoiceRequest(text="Test")
        command = ServiceCommand.process_text(request)
        json_data = command.model_dump()
        assert json_data["command_type"] == "ProcessText"
        assert json_data["request"]["text"] == "Test"


class TestServiceResponse:
    """Tests for ServiceResponse model"""
    
    def test_service_response_creation(self):
        """Test creating a ServiceResponse"""
        response = ServiceResponse(
            response_type="Ack"  # ServiceResponse requires response_type
        )
        assert response.response_type == "Ack"
        assert response.update is None
        assert response.error is None


