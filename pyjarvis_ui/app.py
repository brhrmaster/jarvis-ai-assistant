"""
Main Pygame application with animated digital face
"""

import pygame
import asyncio
import sys
import threading
import os
from typing import Optional
from loguru import logger
from pyjarvis_core import AnimationController
from pyjarvis_shared import VoiceProcessingUpdate, AppConfig
from .face_renderer import FaceRenderer
from .audio_player import AudioPlayer
from .service_client import ServiceClient


class PyJarvisApp:
    """Main PyJarvis application"""
    
    def __init__(self, width: Optional[int] = None, height: Optional[int] = None):
        """
        Create a new PyJarvis application
        
        Args:
            width: Window width (if None, uses robot image dimensions)
            height: Window height (if None, uses robot image dimensions)
        """
        # Load robot face image to determine window size
        robot_image_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "robot-face-2.png")
        
        if os.path.exists(robot_image_path):
            try:
                temp_img = pygame.image.load(robot_image_path)
                img_width, img_height = temp_img.get_size()
                
                # Use image dimensions if not specified, or scale down if too large
                if width is None:
                    # Scale down if larger than 1200px to fit most screens
                    scale_factor = min(1.0, 1200.0 / max(img_width, img_height))
                    self.width = int(img_width * scale_factor)
                    self.height = int(img_height * scale_factor)
                else:
                    self.width = width
                    self.height = height
                    
                logger.info(f"Robot face image loaded: {img_width}x{img_height}, window size: {self.width}x{self.height}")
            except Exception as e:
                logger.warning(f"Failed to load robot image, using defaults: {e}")
                self.width = width or 800
                self.height = height or 600
        else:
            logger.warning(f"Robot face image not found at {robot_image_path}, using defaults")
            self.width = width or 800
            self.height = height or 600
        
        # Initialize Pygame
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("PyJarvis - Your AI Assistant")
        self.clock = pygame.time.Clock()
        
        # Components
        self.animation_controller = AnimationController()
        self.face_renderer = FaceRenderer(self.width, self.height, robot_image_path)
        
        # Get config for audio player
        config = AppConfig()
        self.audio_player = AudioPlayer(
            delete_after_playback=config.audio_delete_after_playback
        )
        
        # Service client
        self.service_client = ServiceClient()
        self.asyncio_thread: Optional[threading.Thread] = None
        self.asyncio_loop: Optional[asyncio.AbstractEventLoop] = None
        
        # State
        self.running = True
        self.input_text = ""
        self.last_frame_time = pygame.time.get_ticks()
        self.connected_to_service = False
        self.reconnect_future = None  # Future from run_coroutine_threadsafe
        self.last_reconnect_attempt = 0.0
        self.reconnect_interval = 3.0  # Try to reconnect every 3 seconds
        
        logger.info("PyJarvis UI initialized")
    
    def _run_asyncio_loop(self) -> None:
        """Run asyncio event loop in a separate thread"""
        self.asyncio_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.asyncio_loop)
        self.asyncio_loop.run_forever()
    
    async def _async_initialize(self) -> None:
        """Async initialization"""
        await self._try_connect_to_service()
    
    async def _try_connect_to_service(self) -> bool:
        """
        Try to connect to the service
        
        Returns:
            True if connected successfully, False otherwise
        """
        if self.connected_to_service:
            return True
            
        logger.info("Connecting to service...")
        try:
            # Check if already connected and disconnect first
            if self.service_client.connected:
                try:
                    await self.service_client.disconnect()
                except:
                    pass
            
            await self.service_client.connect()
            await self.service_client.register_for_broadcasts(self._handle_update)
            self.connected_to_service = True
            logger.info("Connected to service successfully")
            return True
        except Exception as e:
            logger.debug(f"Failed to connect to service: {e}")
            self.connected_to_service = False
            return False
    
    async def _async_reconnect_loop(self) -> None:
        """Background task to periodically try reconnecting to service"""
        import time
        while self.running:
            # Check if connection status has changed (service might have disconnected)
            if self.connected_to_service and not self.service_client.connected:
                logger.info("[UI] Detected connection loss, updating status...")
                self.connected_to_service = False
            
            if not self.connected_to_service:
                current_time = time.time()
                if current_time - self.last_reconnect_attempt >= self.reconnect_interval:
                    self.last_reconnect_attempt = current_time
                    logger.debug("Attempting to reconnect to service...")
                    success = await self._try_connect_to_service()
                    if success:
                        logger.info("[UI] Successfully reconnected to service!")
            
            # Sleep for a bit before checking again
            await asyncio.sleep(1.0)  # Check every second
    
    def _handle_update(self, update: VoiceProcessingUpdate) -> None:
        """
        Handle voice processing update from service
        
        Args:
            update: Voice processing update
        """
        logger.info(f"[UI] Received update: status={update.status}, emotion={update.emotion}")
        
        # Update emotion in animation controller
        if update.emotion:
            self.animation_controller.set_emotion(update.emotion)
        
        # Play audio if available (prefer file path over raw bytes)
        if update.audio_file_path:
            logger.info(f"[UI] Playing audio file: {update.audio_file_path}")
            try:
                self.audio_player.play_file(update.audio_file_path)
            except Exception as e:
                logger.error(f"[UI] Failed to play audio file: {e}")
        elif update.audio_data:
            # Fallback to raw bytes (backward compatibility)
            logger.info(f"[UI] Playing audio from bytes: {len(update.audio_data)} bytes")
            try:
                self.audio_player.play(update.audio_data)
            except Exception as e:
                logger.error(f"[UI] Failed to play audio: {e}")
    
    async def _async_send_text(self, text: str, language: Optional[str] = None) -> None:
        """Send text to service asynchronously"""
        if not self.connected_to_service:
            logger.warning("[UI] Not connected to service, cannot send text")
            return
        
        try:
            await self.service_client.send_text(text, language)
            logger.info(f"[UI] Text sent to service: '{text}'")
        except Exception as e:
            logger.error(f"[UI] Failed to send text to service: {e}")
    
    def run(self) -> None:
        """Run the main application loop"""
        logger.info("Starting PyJarvis UI")
        
        # Start asyncio event loop in separate thread
        self.asyncio_thread = threading.Thread(target=self._run_asyncio_loop, daemon=True)
        self.asyncio_thread.start()
        
        # Wait for event loop to be ready
        while self.asyncio_loop is None:
            import time
            time.sleep(0.01)
        
        # Initialize async components
        asyncio.run_coroutine_threadsafe(self._async_initialize(), self.asyncio_loop)
        
        # Start reconnect task (runs in background)
        self.reconnect_future = asyncio.run_coroutine_threadsafe(self._async_reconnect_loop(), self.asyncio_loop)
        
        # Main game loop
        while self.running:
            dt = self.clock.tick(60) / 1000.0  # Delta time in seconds
            
            # Handle events
            self._handle_events()
            
            # Update
            self._update(dt)
            
            # Render
            self._render()
        
        # Cleanup
        if self.asyncio_loop:
            # Stop reconnect loop by setting running to False (it checks this flag)
            # The reconnect loop will exit naturally
            
            # Disconnect from service
            asyncio.run_coroutine_threadsafe(
                self.service_client.disconnect(),
                self.asyncio_loop
            )
            self.asyncio_loop.call_soon_threadsafe(self.asyncio_loop.stop)
        
        if self.asyncio_thread:
            self.asyncio_thread.join(timeout=1.0)
        
        pygame.quit()
        logger.info("PyJarvis UI closed")
    
    def _handle_events(self) -> None:
        """Handle Pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_RETURN:
                    # Send text to service
                    if self.input_text.strip():
                        text = self.input_text.strip()
                        self.input_text = ""
                        if self.asyncio_loop:
                            asyncio.run_coroutine_threadsafe(
                                self._async_send_text(text),
                                self.asyncio_loop
                            )
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                else:
                    # Add character to input
                    if event.unicode:
                        self.input_text += event.unicode
    
    def _update(self, dt: float) -> None:
        """Update application state"""
        # Update animation controller
        audio_level = self.audio_player.get_current_level() if self.audio_player.is_playing else None
        self.animation_controller.update(dt, audio_level)
    
    def _render(self) -> None:
        """Render the application"""
        # Get current audio level for lip-sync effects
        audio_level = self.audio_player.get_current_level() if self.audio_player.is_playing else None
        is_speaking = audio_level is not None and audio_level > 0.05
        
        # Render face with background image
        self.face_renderer.render(self.screen, self.animation_controller, is_speaking)
        
        # Render input text with background for readability
        font = pygame.font.Font(None, 24)
        if self.input_text:
            text_surface = font.render(self.input_text, True, (255, 255, 255))
            # Add semi-transparent background
            text_bg = pygame.Surface((text_surface.get_width() + 10, text_surface.get_height() + 10))
            text_bg.set_alpha(128)
            text_bg.fill((0, 0, 0))
            self.screen.blit(text_bg, (5, 5))
            self.screen.blit(text_surface, (10, 10))
        
        # Render status with background for readability (moved to right side)
        connection_status = "Connected" if self.connected_to_service else "Disconnected"
        audio_status = "Playing" if self.audio_player.is_playing else "Idle"
        status_text = f"Service: {connection_status} | Audio: {audio_status}"
        status_surface = font.render(status_text, True, (200, 200, 200))
        status_bg = pygame.Surface((status_surface.get_width() + 10, status_surface.get_height() + 10))
        status_bg.set_alpha(128)
        status_bg.fill((0, 0, 0))
        # Position status text on the right side
        status_x = self.width - status_surface.get_width() - 15
        status_y = self.height - 30
        self.screen.blit(status_bg, (status_x - 5, status_y - 5))
        self.screen.blit(status_surface, (status_x, status_y))
        
        # Render connection indicator in center of bottom-left circle
        # Based on image grid: bottom-left circle center is at grid (4.5, 13.5) of (27, 18) grid
        # Original image: 524x600, so per grid unit: x=19.41, y=33.33
        # Original position: (87, 450) scaled to current window size
        original_img_width = 524
        original_img_height = 600
        grid_x_center = 4.5  # Center of bottom-left circle horizontally
        grid_y_center = 13.5  # Center of bottom-left circle vertically
        original_x = (grid_x_center / 25.5) * original_img_width
        original_y = (grid_y_center / 18.81) * original_img_height
        # Scale to current window size
        scale_x = self.width / original_img_width
        scale_y = self.height / original_img_height
        dot_x = int(original_x * scale_x)
        dot_y = int(original_y * scale_y)
        color = (0, 255, 0) if self.connected_to_service else (255, 0, 0)
        pygame.draw.circle(self.screen, color, (dot_x, dot_y), 8)
        
        pygame.display.flip()
    


def main() -> None:
    """Main entry point"""
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
    )
    
    app = PyJarvisApp()
    app.run()


if __name__ == "__main__":
    main()

