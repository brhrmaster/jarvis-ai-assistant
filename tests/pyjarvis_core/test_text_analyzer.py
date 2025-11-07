"""
Unit tests for pyjarvis_core.text_analyzer module
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from pyjarvis_core.text_analyzer import TextAnalyzer
from pyjarvis_shared import Emotion, Language


class TestTextAnalyzer:
    """Tests for TextAnalyzer class"""
    
    @pytest.fixture
    def analyzer(self):
        """Create a TextAnalyzer instance"""
        return TextAnalyzer()
    
    @pytest.mark.asyncio
    async def test_analyzer_initialization(self, analyzer):
        """Test TextAnalyzer initialization"""
        assert analyzer._language_pipeline is None
        assert analyzer._initialized is False
    
    @pytest.mark.asyncio
    async def test_detect_emotion_basic(self, analyzer):
        """Test basic emotion detection"""
        emotion = await analyzer.detect_emotion("Hello, world!")
        assert isinstance(emotion, Emotion)
    
    @pytest.mark.asyncio
    async def test_detect_emotion_happy_text(self, analyzer):
        """Test emotion detection for happy text"""
        emotion = await analyzer.detect_emotion("I'm so happy today!")
        assert isinstance(emotion, Emotion)
    
    @pytest.mark.asyncio
    async def test_detect_language_basic(self, analyzer):
        """Test basic language detection"""
        language = await analyzer.detect_language("Hello, world!")
        assert isinstance(language, Language)
    
    @pytest.mark.asyncio
    async def test_detect_language_portuguese(self, analyzer):
        """Test language detection for Portuguese text"""
        language = await analyzer.detect_language("Olá, mundo!")
        assert isinstance(language, Language)
    
    @pytest.mark.asyncio
    async def test_initialize_language_detection(self, analyzer):
        """Test language detection model initialization"""
        await analyzer._initialize_language_detection()
        assert analyzer._initialized is True
    
    @pytest.mark.asyncio
    async def test_analyze_text(self, analyzer):
        """Test full text analysis"""
        # TextAnalyzer doesn't have analyze method
        # Test by calling detect_emotion and detect_language separately
        emotion = await analyzer.detect_emotion("Hello, world!")
        language = await analyzer.detect_language("Hello, world!")
        assert emotion is not None
        assert language is not None
        assert isinstance(emotion, Emotion)
        assert isinstance(language, Language)


