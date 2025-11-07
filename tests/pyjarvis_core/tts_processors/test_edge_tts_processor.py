"""
Unit tests for pyjarvis_core.tts_processors.edge_tts_processor module
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from pyjarvis_core.tts_processors.edge_tts_processor import EdgeTtsProcessor
from pyjarvis_shared import AppConfig


class TestEdgeTtsProcessor:
    """Tests for EdgeTtsProcessor class"""
    
    @pytest.fixture
    def processor(self, app_config):
        """Create an EdgeTtsProcessor instance"""
        return EdgeTtsProcessor(app_config)
    
    def test_processor_initialization(self, processor, app_config):
        """Test EdgeTtsProcessor initialization"""
        assert processor.config == app_config
    
    @pytest.mark.asyncio
    async def test_synthesize_text(self, processor):
        """Test synthesizing text to speech"""
        with patch('edge_tts.Communicate') as mock_communicate:
            mock_communicate.return_value = AsyncMock()
            # Mock the audio stream
            mock_audio = b"mock_audio_data"
            mock_communicate.return_value.__aiter__.return_value = [mock_audio]
            
            result = await processor.synthesize("Hello, world!")
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_synthesize_with_language(self, processor):
        """Test synthesizing with specific language"""
        with patch('edge_tts.Communicate') as mock_communicate:
            mock_communicate.return_value = AsyncMock()
            mock_audio = b"mock_audio_data"
            mock_communicate.return_value.__aiter__.return_value = [mock_audio]
            
            result = await processor.synthesize("Hello", language="en")
            assert result is not None
    
    def test_get_voice_for_language(self, processor):
        """Test getting voice for a specific language"""
        voice = processor._get_voice_for_language("en")
        assert voice is not None
        assert isinstance(voice, str)


