"""
Face renderer for drawing animated digital face
"""

import pygame
import os
import time
import math
from typing import Optional
from pyjarvis_core import AnimationController, AnimationState

class FaceRenderer:
    """Renders the digital face with eyes and mouth"""
    
    # Original image dimensions (reference coordinates)
    ORIGINAL_IMAGE_WIDTH = 524
    ORIGINAL_IMAGE_HEIGHT = 800
    
    # Original eye positions (from actual image measurements)
    ORIGINAL_EYE_X = 399
    ORIGINAL_EYE_Y = 264
    ORIGINAL_EYE_WIDTH = 125
    ORIGINAL_EYE_HEIGHT = 116
    
    def __init__(self, width: int = 800, height: int = 524, robot_image_path: Optional[str] = None):
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
        self.eye_x = int(self.ORIGINAL_EYE_X * self.scale_x)
        self.eye_y = int(self.ORIGINAL_EYE_Y * self.scale_y)
        
        # Eye glow radius based on actual eye dimensions (use average of width/height)
        eye_avg_size = (self.ORIGINAL_EYE_WIDTH + self.ORIGINAL_EYE_HEIGHT) / 2
        self.eye_glow_radius = int(eye_avg_size * max(self.scale_x, self.scale_y) * 0.6)

        # Multi-circle animation position (mid-left circular element)
        # Based on image grid: mid-left circle center is at grid (4.5, 5) of (27, 18) grid
        grid_x_center = 4.5  # Center of mid-left circle horizontally
        grid_y_center = 5.0  # Center of mid-left circle vertically
        original_x = (grid_x_center / 25.5) * self.original_img_width
        original_y = (grid_y_center / 20.5) * self.original_img_height
        self.animation_center_x = int(original_x * self.scale_x)
        self.animation_center_y = int(original_y * self.scale_y)
        
        # Animation timing
        self.animation_start_time = time.time()
    
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
        
        # Draw multi-circle glowing animation (replaces propeller animation)
        self._draw_multi_circle_animation(surface, state, is_speaking)
        
        # Draw lip-sync overlay effects when speaking
        if is_speaking:
            # Draw eye glow effect
            self._draw_eye_glow(surface, state)
    
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

                # Draw glow for eye at actual position
                self._draw_glow_circle(glow_surface, self.eye_x, self.eye_y, layer_radius, layer_color)
            
            # Blit the glow surface onto the main surface
            surface.blit(glow_surface, (0, 0), special_flags=pygame.BLEND_ADD)
    
    def _draw_glow_circle(self, surface: pygame.Surface, x: int, y: int, radius: int, color: tuple) -> None:
        """Draw a glow circle with alpha blending"""
        # Create a temporary surface for this circle
        circle_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(circle_surface, color, (radius, radius), radius)
        surface.blit(circle_surface, (x - radius, y - radius), special_flags=pygame.BLEND_ALPHA_SDL2)

    def _draw_multi_circle_animation(self, surface: pygame.Surface, state: AnimationState, is_speaking: bool) -> None:
        """
        Draw multi-circle glowing animation matching the central element design.
        Creates concentric rings with different patterns (solid, dashed, dotted) that glow.
        """
        current_time = time.time() - self.animation_start_time
        
        # Create animation surface for blending
        anim_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Base glow color (cyan/blue to match the UI theme)
        base_color = (0, 200, 255)  # Cyan
        
        # Calculate pulsing glow intensity (breathing effect)
        pulse_speed = 2.0  # Pulses per second
        pulse_intensity = 0.5 + 0.5 * (1.0 + math.sin(current_time * pulse_speed * 3.14159)) / 2.0
        
        # Enhance glow when speaking
        if is_speaking:
            pulse_intensity = min(1.0, pulse_intensity + 0.3)
        
        # Define multiple concentric rings with different radii and styles
        rings = [
            # (radius, width, style, glow_intensity_multiplier)
            # Inner rings - solid, brighter
            (15, 2, 'solid', 1.0),
            (25, 2, 'solid', 0.8),
            # Middle rings - dashed
            (35, 2, 'dashed', 0.7),
            (45, 2, 'dashed', 0.6),
            # Outer rings - dotted
            (55, 1, 'dotted', 0.5),
            (65, 1, 'dotted', 0.4),
            (75, 1, 'dotted', 0.3),
        ]
        
        # Draw each ring
        for ring_radius, ring_width, style, intensity_mult in rings:
            # Calculate ring glow with pulsing and individual intensity
            ring_glow = pulse_intensity * intensity_mult
            
            # Create color with alpha based on glow
            ring_alpha = int(200 * ring_glow)
            ring_color = (*base_color, ring_alpha)
            
            # Calculate actual radius scaled to screen
            scaled_radius = int(ring_radius * max(self.scale_x, self.scale_y))
            scaled_width = max(1, int(ring_width * max(self.scale_x, self.scale_y)))
            
            # Draw ring based on style
            if style == 'solid':
                # Draw solid circle outline
                self._draw_ring(anim_surface, self.animation_center_x, self.animation_center_y, 
                               scaled_radius, scaled_width, ring_color)
            elif style == 'dashed':
                # Draw dashed circle (8 segments)
                self._draw_dashed_ring(anim_surface, self.animation_center_x, self.animation_center_y,
                                      scaled_radius, scaled_width, ring_color, num_segments=8)
            elif style == 'dotted':
                # Draw dotted circle
                self._draw_dotted_ring(anim_surface, self.animation_center_x, self.animation_center_y,
                                      scaled_radius, scaled_width, ring_color, num_dots=16)
            
            # Add outer glow layer for each ring
            glow_radius = scaled_radius + scaled_width * 2
            glow_alpha = int(ring_alpha * 0.3)
            glow_color = (*base_color, glow_alpha)
            self._draw_glow_circle(anim_surface, self.animation_center_x, self.animation_center_y,
                                  glow_radius, glow_color)
        
        # Blit the animation surface with additive blending for glow effect
        surface.blit(anim_surface, (0, 0), special_flags=pygame.BLEND_ADD)
    
    def _draw_ring(self, surface: pygame.Surface, x: int, y: int, radius: int, width: int, color: tuple) -> None:
        """Draw a solid ring"""
        # Draw multiple circles to create a smooth ring with width
        for i in range(width):
            r = radius - i
            if r > 0:
                # Create circle surface
                circle_size = r * 2 + 2
                circle_surf = pygame.Surface((circle_size, circle_size), pygame.SRCALPHA)
                pygame.draw.circle(circle_surf, color, (r + 1, r + 1), r, 1)
                surface.blit(circle_surf, (x - r - 1, y - r - 1), special_flags=pygame.BLEND_ALPHA_SDL2)
    
    def _draw_dashed_ring(self, surface: pygame.Surface, x: int, y: int, radius: int, width: int, 
                          color: tuple, num_segments: int = 8) -> None:
        """Draw a dashed ring"""
        segment_angle = 2 * math.pi / num_segments
        dash_length = segment_angle * 0.6  # Each dash is 60% of segment
        
        for i in range(num_segments):
            start_angle = i * segment_angle
            end_angle = start_angle + dash_length
            
            # Draw arc for this dash
            points = []
            num_points = 20
            for j in range(num_points + 1):
                angle = start_angle + (end_angle - start_angle) * (j / num_points)
                px = x + radius * math.cos(angle)
                py = y + radius * math.sin(angle)
                points.append((int(px), int(py)))
            
            # Draw lines connecting points to create the dash
            if len(points) > 1:
                for j in range(len(points) - 1):
                    pygame.draw.line(surface, color, points[j], points[j + 1], width)
    
    def _draw_dotted_ring(self, surface: pygame.Surface, x: int, y: int, radius: int, width: int,
                          color: tuple, num_dots: int = 16) -> None:
        """Draw a dotted ring"""
        angle_step = 2 * math.pi / num_dots
        
        for i in range(num_dots):
            angle = i * angle_step
            dot_x = int(x + radius * math.cos(angle))
            dot_y = int(y + radius * math.sin(angle))
            pygame.draw.circle(surface, color, (dot_x, dot_y), width)

