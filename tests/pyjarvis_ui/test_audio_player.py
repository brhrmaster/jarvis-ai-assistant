"""
Unit tests for pyjarvis_ui.audio_player module
"""
import pytest
from unittest.mock import Mock, patch
from pyjarvis_ui.audio_player import AudioPlayer
from pyjarvis_shared import AppConfig


class TestAudioPlayer:
    """Tests for AudioPlayer class"""
    
    @pytest.fixture
    def player(self, app_config):
        """Create an AudioPlayer instance"""
        return AudioPlayer(app_config)
    
    def test_player_initialization(self, player, app_config):
        """Test AudioPlayer initialization"""
        assert player.config == app_config
    
    @pytest.mark.asyncio
    async def test_play_audio_file(self, player):
        """Test playing an audio file"""
        audio_file = "test_audio.wav"
        
        with patch('pygame.mixer') as mock_mixer:
            mock_mixer.music.load = Mock()
            mock_mixer.music.play = Mock()
            
            await player.play_audio(audio_file)
            mock_mixer.music.load.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_audio(self, player):
        """Test stopping audio playback"""
        with patch('pygame.mixer') as mock_mixer:
            mock_mixer.music.stop = Mock()
            
            await player.stop()
            mock_mixer.music.stop.assert_called_once()
    
    def test_is_playing(self, player):
        """Test checking if audio is playing"""
        with patch('pygame.mixer') as mock_mixer:
            mock_mixer.music.get_busy.return_value = True
            assert player.is_playing() is True


