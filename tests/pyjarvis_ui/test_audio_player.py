"""
Unit tests for pyjarvis_ui.audio_player module
"""
import pytest
from unittest.mock import Mock, patch
from pyjarvis_ui.audio_player import AudioPlayer


class TestAudioPlayer:
    """Tests for AudioPlayer class"""
    
    @pytest.fixture
    def player(self):
        """Create an AudioPlayer instance"""
        return AudioPlayer(sample_rate=44100, channels=1, delete_after_playback=True)
    
    def test_player_initialization(self, player):
        """Test AudioPlayer initialization"""
        assert player.sample_rate == 44100
        assert player.channels == 1
        assert player.delete_after_playback is True
        assert player.is_playing is False
    
    @pytest.mark.asyncio
    async def test_play_audio_file(self, player):
        """Test playing an audio file"""
        import tempfile
        import os
        from pathlib import Path
        
        # Create a temporary WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            # Write minimal WAV header
            import wave
            with wave.open(tmp_path, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(44100)
                wav_file.writeframes(b'\x00' * 1000)  # 1000 frames of silence
        
        try:
            with patch('sounddevice.OutputStream') as mock_stream_class:
                mock_stream = Mock()
                mock_stream.start = Mock()
                mock_stream.stop = Mock()
                mock_stream_class.return_value = mock_stream
                
                # play_file is not async, it starts a thread
                player.play_file(tmp_path)
                # Give thread time to start
                import time
                time.sleep(0.1)
                
                # Verify stream was created
                assert player.current_stream is not None or player._playback_thread is not None
        finally:
            # Clean up
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_stop_audio(self, player):
        """Test stopping audio playback"""
        # stop() is not async
        player.stop()
        assert player.is_playing is False
        assert player.current_stream is None
    
    def test_is_playing(self, player):
        """Test checking if audio is playing"""
        # is_playing is a boolean attribute, not a method
        assert isinstance(player.is_playing, bool)
        player.is_playing = True
        assert player.is_playing is True
        player.is_playing = False
        assert player.is_playing is False


