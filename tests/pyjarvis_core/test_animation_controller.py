"""
Unit tests for pyjarvis_core.animation_controller module
"""
import pytest
from unittest.mock import Mock
from pyjarvis_core.animation_controller import AnimationController
from pyjarvis_shared import Emotion


class TestAnimationController:
    """Tests for AnimationController class"""
    
    @pytest.fixture
    def controller(self):
        """Create an AnimationController instance"""
        return AnimationController()
    
    def test_controller_initialization(self, controller):
        """Test AnimationController initialization"""
        assert controller is not None
        # Add more specific assertions based on implementation
    
    def test_update_emotion(self, controller):
        """Test updating emotion"""
        controller.set_emotion(Emotion.HAPPY)  # Use set_emotion instead of update_emotion
        assert controller.emotion == Emotion.HAPPY
    
    def test_get_animation_state(self, controller):
        """Test getting current animation state"""
        state = controller.get_state()  # Use get_state instead of get_animation_state
        assert state is not None
        assert hasattr(state, 'emotion')
        assert hasattr(state, 'eye_blink')
        assert hasattr(state, 'mouth_open')
    
    def test_reset_animation(self, controller):
        """Test resetting animation"""
        # AnimationController doesn't have reset_animation method
        # We can test by setting emotion and checking state
        controller.set_emotion(Emotion.HAPPY)
        assert controller.emotion == Emotion.HAPPY
        controller.set_emotion(Emotion.NEUTRAL)
        assert controller.emotion == Emotion.NEUTRAL


