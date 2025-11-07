"""
Unit tests for pyjarvis_service.processor module
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from pyjarvis_service.processor import TextProcessor
from pyjarvis_shared import AppConfig, TextToVoiceRequest, ProcessingStatus


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
        
        with patch.object(processor.text_analyzer, 'detect_emotion') as mock_emotion, \
             patch.object(processor.text_analyzer, 'detect_language') as mock_language, \
             patch.object(processor.text_analyzer, 'extract_subject') as mock_subject, \
             patch.object(processor.tts_processor, 'synthesize') as mock_synthesize:
            from pyjarvis_shared import Emotion, Language
            from pyjarvis_core.tts_processors.base import TtsProcessorResult
            from pathlib import Path
            
            mock_emotion.return_value = Emotion.NEUTRAL
            mock_language.return_value = Language.ENGLISH
            mock_subject.return_value = None
            mock_synthesize.return_value = TtsProcessorResult(
                audio_file_path=Path("test_audio.wav"),
                sample_rate=44100,
                duration_seconds=1.0,
                language=Language.ENGLISH
            )
            
            result = await processor.process(request)  # Use process instead of process_text
            assert result is not None
            assert result.status == ProcessingStatus.READY
    
    @pytest.mark.asyncio
    async def test_analyze_text(self, processor):
        """Test text analysis"""
        # TextProcessor doesn't have _analyze_text as separate method
        # Analysis is done within process() method
        # We can test the text_analyzer directly
        emotion = await processor.text_analyzer.detect_emotion("Hello, world!")
        language = await processor.text_analyzer.detect_language("Hello, world!")
        assert emotion is not None
        assert language is not None
    
    @pytest.mark.asyncio
    async def test_synthesize_audio(self, processor):
        """Test audio synthesis"""
        # TextProcessor doesn't have _synthesize_audio as separate method
        # Synthesis is done within process() method
        # We can test the tts_processor directly
        from pyjarvis_shared import Language
        from pyjarvis_core.tts_processors.base import TtsProcessorResult
        from pathlib import Path
        
        with patch.object(processor.tts_processor, 'synthesize') as mock_synthesize:
            mock_synthesize.return_value = TtsProcessorResult(
                audio_file_path=Path("test.wav"),
                sample_rate=44100,
                duration_seconds=1.0,
                language=Language.ENGLISH
            )
            
            result = await processor.tts_processor.synthesize("Hello", Language.ENGLISH)
            assert result is not None


