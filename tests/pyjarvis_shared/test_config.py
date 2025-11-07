"""
Unit tests for pyjarvis_shared.config module
"""
import pytest
from pyjarvis_shared import AppConfig, AudioConfig


class TestAudioConfig:
    """Tests for AudioConfig dataclass"""
    
    def test_audio_config_default_values(self):
        """Test AudioConfig with default values"""
        config = AudioConfig()
        assert config.sample_rate == 22050
        assert config.channels == 1
        assert config.format == "int16"
    
    def test_audio_config_custom_values(self):
        """Test AudioConfig with custom values"""
        config = AudioConfig(
            sample_rate=44100,
            channels=2,
            format="float32"
        )
        assert config.sample_rate == 44100
        assert config.channels == 2
        assert config.format == "float32"


class TestAppConfig:
    """Tests for AppConfig dataclass"""
    
    def test_app_config_default_values(self, app_config):
        """Test AppConfig with default values"""
        assert app_config.tcp_host == "127.0.0.1"
        assert app_config.tcp_port == 8888
        assert app_config.log_level == "DEBUG"
        assert app_config.tts_processor == "edge-tts"
        assert app_config.audio_config is not None
    
    def test_app_config_custom_values(self):
        """Test AppConfig with custom values"""
        config = AppConfig(
            tcp_host="0.0.0.0",
            tcp_port=9999,
            log_level="INFO",
            tts_processor="gtts"
        )
        assert config.tcp_host == "0.0.0.0"
        assert config.tcp_port == 9999
        assert config.log_level == "INFO"
        assert config.tts_processor == "gtts"
    
    def test_app_config_audio_config_initialization(self):
        """Test that audio_config is initialized if None"""
        config = AppConfig(audio_config=None)
        assert config.audio_config is not None
        assert isinstance(config.audio_config, AudioConfig)
    
    def test_app_config_edge_tts_voices(self, app_config):
        """Test edge_tts_voices configuration"""
        assert "pt-br" in app_config.edge_tts_voices
        assert "en" in app_config.edge_tts_voices
        assert app_config.edge_tts_voices["pt-br"] == "pt-BR-AntonioNeural"
        assert app_config.edge_tts_voices["en"] == "en-US-DerekMultilingualNeural"


