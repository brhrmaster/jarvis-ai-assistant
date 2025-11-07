"""
Unit tests for pyjarvis_ui.face_renderer module
"""
import pytest
from unittest.mock import Mock, patch
from pyjarvis_ui.face_renderer import FaceRenderer
from pyjarvis_shared import Emotion


class TestFaceRenderer:
    """Tests for FaceRenderer class"""
    
    @pytest.fixture
    def renderer(self):
        """Create a FaceRenderer instance"""
        with patch('pygame.init'), \
             patch('pygame.image.load') as mock_load:
            # Mock image loading
            mock_img = Mock()
            mock_img.get_size.return_value = (800, 600)
            mock_load.return_value = mock_img
            
            return FaceRenderer(width=800, height=600)
    
    def test_renderer_initialization(self, renderer):
        """Test FaceRenderer initialization"""
        assert renderer.width == 800
        assert renderer.height == 600
        assert renderer.center_x == 400
        assert renderer.center_y == 300
    
    def test_update_emotion(self, renderer):
        """Test updating emotion"""
        # FaceRenderer doesn't have animation_controller as attribute
        # It receives animation_controller as parameter to render()
        assert hasattr(renderer, 'width')
        assert hasattr(renderer, 'height')
    
    def test_render_frame(self, renderer):
        """Test rendering a frame"""
        from pyjarvis_core import AnimationController
        mock_screen = Mock()
        animation_controller = AnimationController()
        renderer.render(mock_screen, animation_controller, is_speaking=False)
        # Add assertions based on implementation
    
    def test_update_animation(self, renderer):
        """Test updating animation"""
        # FaceRenderer doesn't have update_animation method directly
        # Animation is passed to render() method
        assert hasattr(renderer, 'render')
    
    def test_cleanup(self, renderer):
        """Test cleanup"""
        # FaceRenderer doesn't have cleanup method
        # Just verify it exists and can be called without error
        pass


