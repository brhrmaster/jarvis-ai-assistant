"""
Unit tests for pyjarvis_llama.audio_recorder module
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from pyjarvis_llama.audio_recorder import AudioRecorder
from pyjarvis_shared import AppConfig


class TestAudioRecorder:
    """Tests for AudioRecorder class"""
    
    @pytest.fixture
    def recorder(self, app_config):
        """Create an AudioRecorder instance"""
        return AudioRecorder(app_config)
    
    def test_recorder_initialization(self, recorder, app_config):
        """Test AudioRecorder initialization"""
        assert recorder.config == app_config
    
    @pytest.mark.asyncio
    async def test_start_recording(self, recorder):
        """Test starting audio recording"""
        with patch('sounddevice.InputStream') as mock_stream:
            await recorder.start_recording()
            assert recorder.is_recording() is True
    
    @pytest.mark.asyncio
    async def test_stop_recording(self, recorder):
        """Test stopping audio recording"""
        await recorder.stop_recording()
        assert recorder.is_recording() is False
    
    @pytest.mark.asyncio
    async def test_get_audio_data(self, recorder):
        """Test getting recorded audio data"""
        data = await recorder.get_audio_data()
        assert data is not None
    
    def test_set_language(self, recorder):
        """Test setting recognition language"""
        recorder.set_language("pt")
        assert recorder.language == "pt"


