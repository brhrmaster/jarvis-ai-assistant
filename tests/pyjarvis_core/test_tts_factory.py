"""
Unit tests for pyjarvis_core.tts_factory module
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from pyjarvis_core.tts_factory import TtsProcessorFactory
from pyjarvis_shared import AppConfig


class TestTtsProcessorFactory:
    """Tests for TtsProcessorFactory class"""
    
    def test_factory_creation(self, app_config):
        """Test TtsProcessorFactory is a class with static methods"""
        # TtsProcessorFactory is a class with static methods, not instantiable
        assert hasattr(TtsProcessorFactory, 'create')
        assert hasattr(TtsProcessorFactory, 'list_available')
    
    def test_create_edge_tts_processor(self, app_config):
        """Test creating an Edge-TTS processor"""
        output_dir = Path("./test_audio")
        processor = TtsProcessorFactory.create(app_config, output_dir=output_dir)
        assert processor is not None
        assert processor.name == "edge-tts"
    
    def test_create_gtts_processor(self, app_config):
        """Test creating a gTTS processor"""
        output_dir = Path("./test_audio")
        # Temporarily change processor type
        app_config.tts_processor = "gtts"
        processor = TtsProcessorFactory.create(app_config, output_dir=output_dir)
        assert processor is not None
        assert processor.name == "gTTS"
    
    def test_create_default_processor(self, app_config):
        """Test creating default processor"""
        output_dir = Path("./test_audio")
        processor = TtsProcessorFactory.create(app_config, output_dir=output_dir)
        assert processor is not None
    
    def test_create_unknown_processor(self, app_config):
        """Test creating an unknown processor falls back to default"""
        output_dir = Path("./test_audio")
        # Unknown processor should fall back to default (gtts)
        app_config.tts_processor = "unknown-processor"
        processor = TtsProcessorFactory.create(app_config, output_dir=output_dir)
        assert processor is not None
        # Should fall back to gtts
        assert processor.name == "gTTS"


