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
        with patch('pygame.init'):
            return PyJarvisApp(app_config)
    
    def test_app_initialization(self, app, app_config):
        """Test PyJarvisApp initialization"""
        assert app.config == app_config
    
    @pytest.mark.asyncio
    async def test_run_app(self, app):
        """Test running the app"""
        with patch('pygame.event.get') as mock_events, \
             patch('pygame.quit') as mock_quit:
            # Mock pygame.QUIT constant
            mock_quit_constant = 12  # pygame.QUIT value
            mock_events.return_value = [Mock(type=mock_quit_constant)]
            
            try:
                await app.run()
            except SystemExit:
                pass  # Expected when quitting
    
    @pytest.mark.asyncio
    async def test_handle_update(self, app):
        """Test handling updates"""
        update = Mock()
        await app.handle_update(update)
        # Add assertions based on implementation
    
    def test_cleanup(self, app):
        """Test app cleanup"""
        app.cleanup()
        # Add assertions based on implementation

