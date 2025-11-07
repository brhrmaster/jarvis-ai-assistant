"""
Unit tests for pyjarvis_core.tts_processors.base module
"""
import pytest
from unittest.mock import Mock, AsyncMock
from pyjarvis_core.tts_processors.base import TtsProcessor


class TestTtsProcessor:
    """Tests for TtsProcessor base class"""
    
    @pytest.fixture
    def processor(self):
        """Create a mock TtsProcessor instance"""
        # Since TtsProcessor is abstract, we'll test through a concrete implementation
        # or create a mock subclass
        class MockProcessor(TtsProcessor):
            async def synthesize(self, text: str, **kwargs):
                return b"mock_audio_data"
        
        return MockProcessor()
    
    @pytest.mark.asyncio
    async def test_synthesize_abstract_method(self, processor):
        """Test that synthesize method exists and can be called"""
        result = await processor.synthesize("test")
        assert result is not None
    
    def test_processor_interface(self, processor):
        """Test that processor implements required interface"""
        assert hasattr(processor, 'synthesize')
        assert callable(processor.synthesize)


