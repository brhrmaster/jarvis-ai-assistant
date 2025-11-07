"""
Unit tests for pyjarvis_core.tts_processors.edge_tts_processor module
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from pyjarvis_core.tts_processors.edge_tts_processor import EdgeTtsProcessor
from pyjarvis_shared import AppConfig, Language


class TestEdgeTtsProcessor:
    """Tests for EdgeTtsProcessor class"""
    
    @pytest.fixture
    def processor(self, app_config):
        """Create an EdgeTtsProcessor instance"""
        output_dir = Path("./test_audio")
        return EdgeTtsProcessor(output_dir, config=app_config)
    
    def test_processor_initialization(self, processor, app_config):
        """Test EdgeTtsProcessor initialization"""
        assert processor.config == app_config
        assert processor.output_dir == Path("./test_audio")
    
    @pytest.mark.asyncio
    async def test_synthesize_text(self, processor):
        """Test synthesizing text to speech"""
        import tempfile
        import os
        
        with patch('edge_tts.Communicate') as mock_communicate_class:
            mock_communicate = AsyncMock()
            mock_communicate_class.return_value = mock_communicate
            mock_communicate.save = AsyncMock()
            
            # Create a real temporary file path
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                tmp_path = tmp_file.name
            
            try:
                with patch('tempfile.NamedTemporaryFile') as mock_temp:
                    mock_file = Mock()
                    mock_file.name = tmp_path
                    mock_file.__enter__ = Mock(return_value=mock_file)
                    mock_file.__exit__ = Mock(return_value=None)
                    mock_temp.return_value = mock_file
                    
                    with patch('os.path.exists', return_value=True):
                        with patch('os.unlink'):
                            with patch('shutil.move'):
                                result = await processor.synthesize("Hello, world!", Language.ENGLISH)
                                assert result is not None
                                assert result.language == Language.ENGLISH
            finally:
                # Clean up
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
    
    @pytest.mark.asyncio
    async def test_synthesize_with_language(self, processor):
        """Test synthesizing with specific language"""
        import tempfile
        import os
        
        with patch('edge_tts.Communicate') as mock_communicate_class:
            mock_communicate = AsyncMock()
            mock_communicate_class.return_value = mock_communicate
            mock_communicate.save = AsyncMock()
            
            # Create a real temporary file path
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                tmp_path = tmp_file.name
            
            try:
                with patch('tempfile.NamedTemporaryFile') as mock_temp:
                    mock_file = Mock()
                    mock_file.name = tmp_path
                    mock_file.__enter__ = Mock(return_value=mock_file)
                    mock_file.__exit__ = Mock(return_value=None)
                    mock_temp.return_value = mock_file
                    
                    with patch('os.path.exists', return_value=True):
                        with patch('os.unlink'):
                            with patch('shutil.move'):
                                result = await processor.synthesize("Hello", Language.PORTUGUESE)
                                assert result is not None
                                assert result.language == Language.PORTUGUESE
            finally:
                # Clean up
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
    
    def test_get_voice_for_language(self, processor):
        """Test getting voice for a specific language"""
        # The method is private, but we can test through voice_mapping
        assert Language.ENGLISH in processor.voice_mapping
        assert Language.PORTUGUESE in processor.voice_mapping
        voice_en = processor.voice_mapping[Language.ENGLISH]
        assert voice_en is not None
        assert isinstance(voice_en, str)


