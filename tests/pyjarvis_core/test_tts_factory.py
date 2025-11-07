"""
Unit tests for pyjarvis_core.tts_factory module
"""
import pytest
from unittest.mock import Mock, patch
from pyjarvis_core.tts_factory import TtsProcessorFactory
from pyjarvis_shared import AppConfig


class TestTtsProcessorFactory:
    """Tests for TtsProcessorFactory class"""
    
    @pytest.fixture
    def factory(self, app_config):
        """Create a TtsProcessorFactory instance"""
        return TtsProcessorFactory(app_config)
    
    def test_factory_creation(self, factory, app_config):
        """Test TtsProcessorFactory initialization"""
        assert factory.config == app_config
    
    def test_create_edge_tts_processor(self, factory):
        """Test creating an Edge-TTS processor"""
        processor = factory.create_processor("edge-tts")
        assert processor is not None
        # Add more specific assertions based on implementation
    
    def test_create_gtts_processor(self, factory):
        """Test creating a gTTS processor"""
        processor = factory.create_processor("gtts")
        assert processor is not None
        # Add more specific assertions based on implementation
    
    def test_create_default_processor(self, factory):
        """Test creating default processor"""
        processor = factory.create_processor()
        assert processor is not None
    
    def test_create_unknown_processor(self, factory):
        """Test creating an unknown processor raises error"""
        with pytest.raises(ValueError):
            factory.create_processor("unknown-processor")


