"""
Face renderer for drawing animated digital face
"""

import pygame
import os
from typing import Optional
from pyjarvis_core import AnimationController, AnimationState


class FaceRenderer:
    """Renders the digital face with eyes and mouth"""
    
    # Original image dimensions (reference coordinates)
    ORIGINAL_IMAGE_WIDTH = 524
    ORIGINAL_IMAGE_HEIGHT = 600
    
    # Original eye positions (from actual image measurements)
    ORIGINAL_LEFT_EYE_X = 153
    ORIGINAL_LEFT_EYE_Y = 270
    ORIGINAL_RIGHT_EYE_X = 367
    ORIGINAL_RIGHT_EYE_Y = 270
    ORIGINAL_EYE_WIDTH = 125
    ORIGINAL_EYE_HEIGHT = 116
    
    # Original mouth position
    ORIGINAL_MOUTH_X = 260
    ORIGINAL_MOUTH_Y = 477
    ORIGINAL_MOUTH_HEIGHT = 10
    ORIGINAL_MOUTH_WIDTH = 100  # Estimated based on typical proportions
    
    def __init__(self, width: int = 800, height: int = 600, robot_image_path: Optional[str] = None):
        """
        Create a new face renderer
        
        Args:
            width: Screen width
            height: Screen height
            robot_image_path: Path to robot face background image
        """
        self.width = width
        self.height = height
        self.center_x = width // 2
        self.center_y = height // 2
        
        # Load robot face background image
        self.background_image = None
        self.original_img_width = self.ORIGINAL_IMAGE_WIDTH
        self.original_img_height = self.ORIGINAL_IMAGE_HEIGHT
        
        if robot_image_path and os.path.exists(robot_image_path):
            try:
                self.background_image = pygame.image.load(robot_image_path)
                # Get original image dimensions
                self.original_img_width, self.original_img_height = self.background_image.get_size()
                # Scale image to fit window
                self.background_image = pygame.transform.scale(self.background_image, (width, height))
            except Exception as e:
                print(f"Warning: Failed to load robot face image: {e}")
        
        # Calculate scale factors for positioning effects
        self.scale_x = width / self.original_img_width
        self.scale_y = height / self.original_img_height
        
        # Calculate scaled eye positions and dimensions
        self.left_eye_x = int(self.ORIGINAL_LEFT_EYE_X * self.scale_x)
        self.left_eye_y = int(self.ORIGINAL_LEFT_EYE_Y * self.scale_y)
        self.right_eye_x = int(self.ORIGINAL_RIGHT_EYE_X * self.scale_x)
        self.right_eye_y = int(self.ORIGINAL_RIGHT_EYE_Y * self.scale_y)
        
        # Eye glow radius based on actual eye dimensions (use average of width/height)
        eye_avg_size = (self.ORIGINAL_EYE_WIDTH + self.ORIGINAL_EYE_HEIGHT) / 2
        self.eye_glow_radius = int(eye_avg_size * max(self.scale_x, self.scale_y) * 0.6)
        
        # Calculate scaled mouth position
        self.mouth_x = int(self.ORIGINAL_MOUTH_X * self.scale_x)
        self.mouth_y = int(self.ORIGINAL_MOUTH_Y * self.scale_y)
        self.mouth_base_width = int(self.ORIGINAL_MOUTH_WIDTH * self.scale_x)
        self.mouth_base_height = int(self.ORIGINAL_MOUTH_HEIGHT * self.scale_y)
        
        self.mouth_glow_intensity = 0.0
    
    def render(self, surface: pygame.Surface, animation_controller: AnimationController, is_speaking: bool = False) -> None:
        """
        Render the face on the given surface
        
        Args:
            surface: Pygame surface to render on
            animation_controller: Animation controller with current state
            is_speaking: Whether the robot is currently speaking (for glow effects)
        """
        state = animation_controller.get_state()
        
        # Draw background image if available, otherwise use solid color
        if self.background_image:
            surface.blit(self.background_image, (0, 0))
        else:
            # Fallback to solid color background
            surface.fill((20, 20, 30))
        
        # Draw lip-sync overlay effects when speaking
        if is_speaking:
            # Draw eye glow effect
            self._draw_eye_glow(surface, state)
            
            # Draw mouth illumination
            self._draw_mouth_illumination(surface, state)
    
    def _draw_eye_glow(self, surface: pygame.Surface, state: AnimationState) -> None:
        """Draw glowing effect on eyes when speaking using actual eye positions"""
        # Don't draw glow if eyes are mostly closed
        if state.eye_blink > 0.7:
            return
        
        # Create a temporary surface for blending
        glow_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Calculate glow intensity based on mouth_open (indicating speech activity)
        glow_intensity = min(1.0, state.mouth_open * 1.5)
        
        if glow_intensity > 0.1:
            # Cyan/teal glow color (0, 200, 255) similar to the robot's eyes in the image
            glow_color = (0, int(200 * glow_intensity), int(255 * glow_intensity), int(180 * glow_intensity))
            
            # Draw multiple circles for glow effect (outer layers)
            num_layers = 3
            for layer in range(num_layers):
                layer_alpha = int(glow_color[3] * (1.0 - layer * 0.3))
                layer_radius = int(self.eye_glow_radius * (1.0 + layer * 0.5))
                
                # Create glow color with alpha
                layer_color = (glow_color[0], glow_color[1], glow_color[2], max(0, layer_alpha))
                
                # Draw glow for left eye at actual position
                self._draw_glow_circle(glow_surface, self.left_eye_x, self.left_eye_y, layer_radius, layer_color)
                
                # Draw glow for right eye at actual position
                self._draw_glow_circle(glow_surface, self.right_eye_x, self.right_eye_y, layer_radius, layer_color)
            
            # Blit the glow surface onto the main surface
            surface.blit(glow_surface, (0, 0), special_flags=pygame.BLEND_ADD)
    
    def _draw_glow_circle(self, surface: pygame.Surface, x: int, y: int, radius: int, color: tuple) -> None:
        """Draw a glow circle with alpha blending"""
        # Create a temporary surface for this circle
        circle_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(circle_surface, color, (radius, radius), radius)
        surface.blit(circle_surface, (x - radius, y - radius), special_flags=pygame.BLEND_ALPHA_SDL2)
    
    def _draw_mouth_illumination(self, surface: pygame.Surface, state: AnimationState) -> None:
        """Draw internal illumination effect on mouth when speaking using actual mouth position"""
        mouth_open = max(0.0, min(1.0, state.mouth_open))
        
        # Only draw if mouth is open enough
        if mouth_open < 0.1:
            return
        
        # Calculate illumination intensity
        illumination_intensity = min(1.0, mouth_open * 1.2)
        
        # Create a temporary surface for blending
        illum_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # White/cyan glow color for mouth illumination
        illum_color = (
            int(255 * illumination_intensity),
            int(255 * illumination_intensity),
            int(255 * illumination_intensity),
            int(120 * illumination_intensity)
        )
        
        # Calculate mouth dimensions based on opening (use base dimensions scaled by opening)
        mouth_width = max(10, int(self.mouth_base_width * (0.5 + mouth_open * 0.5)))
        mouth_height = max(2, int(self.mouth_base_height * (1.0 + mouth_open * 2.0)))
        
        # Draw illuminated mouth shape at actual position
        mouth_rect = pygame.Rect(
            int(self.mouth_x - mouth_width // 2),
            int(self.mouth_y - mouth_height // 2),
            mouth_width,
            mouth_height
        )
        
        # Draw multiple layers for better glow effect
        for i in range(2):
            layer_intensity = illumination_intensity * (1.0 - i * 0.4)
            layer_color = (
                int(illum_color[0] * layer_intensity),
                int(illum_color[1] * layer_intensity),
                int(illum_color[2] * layer_intensity),
                int(illum_color[3] * layer_intensity)
            )
            
            # Draw ellipse with alpha
            ellipse_surface = pygame.Surface((mouth_rect.width + i * 10, mouth_rect.height + i * 10), pygame.SRCALPHA)
            pygame.draw.ellipse(
                ellipse_surface,
                layer_color,
                pygame.Rect(0, 0, ellipse_surface.get_width(), ellipse_surface.get_height())
            )
            illum_surface.blit(
                ellipse_surface,
                (mouth_rect.x - i * 5, mouth_rect.y - i * 5),
                special_flags=pygame.BLEND_ALPHA_SDL2
            )
        
        # Blit the illumination surface onto the main surface
        surface.blit(illum_surface, (0, 0), special_flags=pygame.BLEND_ADD)

