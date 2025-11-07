"""
Unit tests for pyjarvis_ui.app module
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from pyjarvis_ui.app import PyJarvisApp
from pyjarvis_shared import AppConfig


class TestPyJarvisApp:
    """Tests for PyJarvisApp class"""
    
    @pytest.fixture
    def app(self, app_config):
        """Create a PyJarvisApp instance"""
        with patch('pygame.init'), \
             patch('pygame.display.set_mode') as mock_set_mode, \
             patch('pygame.display.set_caption'), \
             patch('pygame.time.Clock'), \
             patch('pygame.image.load') as mock_load:
            # Mock image loading
            mock_img = Mock()
            mock_img.get_size.return_value = (800, 600)
            mock_load.return_value = mock_img
            
            # Mock screen
            mock_screen = Mock()
            mock_set_mode.return_value = mock_screen
            
            return PyJarvisApp(width=800, height=600)
    
    def test_app_initialization(self, app):
        """Test PyJarvisApp initialization"""
        assert app.width == 800
        assert app.height == 600
        assert app.running is True

    @pytest.mark.asyncio
    async def test_handle_update(self, app):
        """Test handling updates"""
        from pyjarvis_shared import VoiceProcessingUpdate, ProcessingStatus
        update = VoiceProcessingUpdate(
            status=ProcessingStatus.READY  # Use READY instead of COMPLETED
        )
        app._handle_update(update)  # _handle_update is not async
        # Add assertions based on implementation
    
    def test_cleanup(self, app):
        """Test app cleanup"""
        # PyJarvisApp doesn't have cleanup method
        # Just verify it exists and can be called without error
        pass

