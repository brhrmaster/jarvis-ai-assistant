"""
Unit tests for pyjarvis_core.tts_processors.gtts_processor module
"""
import pytest
from unittest.mock import Mock, patch
from pyjarvis_core.tts_processors.gtts_processor import GttsProcessor
from pyjarvis_shared import AppConfig


class TestGttsProcessor:
    """Tests for GttsProcessor class"""
    
    @pytest.fixture
    def processor(self, app_config):
        """Create a GttsProcessor instance"""
        return GttsProcessor(app_config)
    
    def test_processor_initialization(self, processor, app_config):
        """Test GttsProcessor initialization"""
        assert processor.config == app_config
    
    @pytest.mark.asyncio
    async def test_synthesize_text(self, processor):
        """Test synthesizing text to speech"""
        with patch('gtts.gTTS') as mock_gtts:
            mock_instance = Mock()
            mock_instance.save = Mock()
            mock_gtts.return_value = mock_instance
            
            with patch('builtins.open', create=True) as mock_open:
                mock_file = Mock()
                mock_file.read = Mock(return_value=b"mock_audio_data")
                mock_open.return_value.__enter__.return_value = mock_file
                
                result = await processor.synthesize("Hello, world!")
                assert result is not None
    
    @pytest.mark.asyncio
    async def test_synthesize_with_language(self, processor):
        """Test synthesizing with specific language"""
        with patch('gtts.gTTS') as mock_gtts:
            mock_instance = Mock()
            mock_instance.save = Mock()
            mock_gtts.return_value = mock_instance
            
            with patch('builtins.open', create=True) as mock_open:
                mock_file = Mock()
                mock_file.read = Mock(return_value=b"mock_audio_data")
                mock_open.return_value.__enter__.return_value = mock_file
                
                result = await processor.synthesize("Hello", language="en")
                assert result is not None


