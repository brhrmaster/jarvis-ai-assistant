"""
Unit tests for pyjarvis_service.processor module
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from pyjarvis_service.processor import TextProcessor
from pyjarvis_shared import AppConfig, TextToVoiceRequest


class TestTextProcessor:
    """Tests for TextProcessor class"""
    
    @pytest.fixture
    def processor(self, app_config):
        """Create a TextProcessor instance"""
        return TextProcessor(app_config)
    
    def test_processor_initialization(self, processor, app_config):
        """Test TextProcessor initialization"""
        assert processor.config == app_config
    
    @pytest.mark.asyncio
    async def test_process_text(self, processor):
        """Test processing text to voice"""
        request = TextToVoiceRequest(text="Hello, world!")
        
        with patch.object(processor, '_analyze_text') as mock_analyze, \
             patch.object(processor, '_synthesize_audio') as mock_synthesize:
            mock_analyze.return_value = AsyncMock()
            mock_synthesize.return_value = AsyncMock(return_value="test_audio.wav")
            
            result = await processor.process_text(request)
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_analyze_text(self, processor):
        """Test text analysis"""
        text = "Hello, world!"
        result = await processor._analyze_text(text)
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_synthesize_audio(self, processor):
        """Test audio synthesis"""
        text = "Hello, world!"
        result = await processor._synthesize_audio(text)
        assert result is not None


