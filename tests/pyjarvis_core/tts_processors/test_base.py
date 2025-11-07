"""
Unit tests for pyjarvis_core.tts_processors.base module
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from pyjarvis_core.tts_processors.base import TtsProcessor, TtsProcessorResult
from pyjarvis_shared import Language


class TestTtsProcessor:
    """Tests for TtsProcessor base class"""
    
    @pytest.fixture
    def processor(self):
        """Create a mock TtsProcessor instance"""
        # Since TtsProcessor is abstract, we'll create a concrete mock subclass
        class MockProcessor(TtsProcessor):
            async def initialize(self) -> None:
                self._initialized = True
            
            async def synthesize(self, text: str, language: Language) -> TtsProcessorResult:
                output_path = self._get_output_path(text, language)
                return TtsProcessorResult(
                    audio_file_path=output_path,
                    sample_rate=44100,
                    duration_seconds=1.0,
                    language=language
                )
            
            @property
            def name(self) -> str:
                return "mock"
        
        return MockProcessor(Path("./test_audio"))
    
    @pytest.mark.asyncio
    async def test_synthesize_abstract_method(self, processor):
        """Test that synthesize method exists and can be called"""
        result = await processor.synthesize("test", Language.ENGLISH)
        assert result is not None
        assert isinstance(result, TtsProcessorResult)
    
    def test_processor_interface(self, processor):
        """Test that processor implements required interface"""
        assert hasattr(processor, 'synthesize')
        assert callable(processor.synthesize)
        assert hasattr(processor, 'initialize')
        assert hasattr(processor, 'name')


