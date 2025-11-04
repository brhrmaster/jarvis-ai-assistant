"""
Animation controller for facial expressions
"""

import time
from dataclasses import dataclass
from typing import Optional
from pyjarvis_shared import Emotion


@dataclass
class AnimationState:
    """Animation state for the digital face"""
    eye_blink: float = 0.0  # 0.0 = open, 1.0 = fully closed
    mouth_open: float = 0.0  # 0.0 = closed, 1.0 = fully open
    emotion: Emotion = Emotion.NEUTRAL
    last_blink: float = 0.0
    is_blinking: bool = False


class AnimationController:
    """Animation controller for managing facial animations"""
    
    def __init__(self, blink_interval: float = 3.0, blink_duration: float = 0.15):
        """
        Create a new animation controller
        
        Args:
            blink_interval: Seconds between blinks
            blink_duration: Duration of a blink in seconds
        """
        self.state = AnimationState()
        self.blink_interval = blink_interval
        self.blink_duration = blink_duration
        self._start_time = time.time()
    
    def update(self, dt: float, audio_level: Optional[float] = None) -> None:
        """
        Update animation state (should be called every frame)
        
        Args:
            dt: Delta time in seconds
            audio_level: Current audio level (0.0 to 1.0) for mouth sync
        """
        self._update_blink(dt)
        self._update_mouth(audio_level)
    
    def _update_blink(self, dt: float) -> None:
        """Update blink animation"""
        current_time = time.time() - self._start_time
        elapsed_since_blink = current_time - self.state.last_blink
        
        if not self.state.is_blinking:
            # Check if it's time to blink
            if elapsed_since_blink >= self.blink_interval:
                self.state.is_blinking = True
                self.state.last_blink = current_time
        else:
            # Blinking animation
            blink_progress = elapsed_since_blink / self.blink_duration
            if blink_progress < 0.5:
                # Closing eyes
                self.state.eye_blink = blink_progress * 2.0
            elif blink_progress < 1.0:
                # Opening eyes
                self.state.eye_blink = 1.0 - (blink_progress - 0.5) * 2.0
            else:
                # Blink complete
                self.state.eye_blink = 0.0
                self.state.is_blinking = False
                self.state.last_blink = current_time
    
    def _update_mouth(self, audio_level: Optional[float]) -> None:
        """Update mouth animation based on audio"""
        if audio_level is not None:
            # Map audio level to mouth opening (with smoothing)
            self.state.mouth_open = min(
                max(self.state.mouth_open * 0.7 + audio_level * 0.3, 0.0), 
                1.0
            )
        else:
            # No audio, gradually close mouth
            self.state.mouth_open *= 0.9
    
    def set_emotion(self, emotion: Emotion) -> None:
        """Set emotion for expression adjustments"""
        self.state.emotion = emotion
    
    def get_state(self) -> AnimationState:
        """Get current animation state"""
        return self.state
    
    @property
    def eye_blink(self) -> float:
        """Get current eye blink value (0.0 = open, 1.0 = closed)"""
        return self.state.eye_blink
    
    @property
    def mouth_open(self) -> float:
        """Get current mouth opening (0.0 = closed, 1.0 = open)"""
        return self.state.mouth_open
    
    @property
    def emotion(self) -> Emotion:
        """Get current emotion"""
        return self.state.emotion

