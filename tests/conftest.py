"""
Pytest configuration and shared fixtures for PyJarvis tests
"""
import pytest
import asyncio
from typing import Generator
from unittest.mock import Mock, MagicMock

from pyjarvis_shared import AppConfig, AudioConfig


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def app_config() -> AppConfig:
    """Provide a default AppConfig for testing."""
    return AppConfig(
        tcp_host="127.0.0.1",
        tcp_port=8888,
        log_level="DEBUG",
        audio_config=AudioConfig(
            sample_rate=22050,
            channels=1,
            format="int16"
        ),
        tts_processor="edge-tts",
        audio_output_dir="./test_audio",
        audio_delete_after_playback=True,
        ollama_base_url="http://localhost:11434",
        ollama_model="test-model",
        ollama_persona="jarvis",
        stt_model="base",
        stt_language="en"
    )


@pytest.fixture
def mock_audio_config() -> AudioConfig:
    """Provide a mock AudioConfig for testing."""
    return AudioConfig(
        sample_rate=22050,
        channels=1,
        format="int16"
    )


@pytest.fixture
def mock_logger():
    """Provide a mock logger for testing."""
    logger = MagicMock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.debug = Mock()
    logger.exception = Mock()
    return logger


