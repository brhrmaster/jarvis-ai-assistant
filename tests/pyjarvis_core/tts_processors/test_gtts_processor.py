"""
Unit tests for pyjarvis_core.tts_processors.gtts_processor module
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from pyjarvis_core.tts_processors.gtts_processor import GttsProcessor
from pyjarvis_shared import Language


class TestGttsProcessor:
    """Tests for GttsProcessor class"""
    
    @pytest.fixture
    def processor(self):
        """Create a GttsProcessor instance"""
        output_dir = Path("./test_audio")
        return GttsProcessor(output_dir)
    
    def test_processor_initialization(self, processor):
        """Test GttsProcessor initialization"""
        assert processor.output_dir == Path("./test_audio")
        assert processor.sample_rate == 44100
    
    @pytest.mark.asyncio
    async def test_synthesize_text(self, processor):
        """Test synthesizing text to speech"""
        import tempfile
        import os
        
        with patch('gtts.gTTS') as mock_gtts:
            mock_instance = Mock()
            mock_instance.save = Mock()
            mock_gtts.return_value = mock_instance
            
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
                            with patch('pydub.AudioSegment') as mock_audio_segment:
                                mock_audio = Mock()
                                mock_audio.export = Mock()
                                mock_audio_segment.from_mp3.return_value = mock_audio
                                
                                with patch('subprocess.run', return_value=Mock()):
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
        
        with patch('gtts.gTTS') as mock_gtts:
            mock_instance = Mock()
            mock_instance.save = Mock()
            mock_gtts.return_value = mock_instance
            
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
                            with patch('pydub.AudioSegment') as mock_audio_segment:
                                mock_audio = Mock()
                                mock_audio.export = Mock()
                                mock_audio_segment.from_mp3.return_value = mock_audio
                                
                                with patch('subprocess.run', return_value=Mock()):
                                    result = await processor.synthesize("Hello", Language.PORTUGUESE)
                                    assert result is not None
                                    assert result.language == Language.PORTUGUESE
            finally:
                # Clean up
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)


