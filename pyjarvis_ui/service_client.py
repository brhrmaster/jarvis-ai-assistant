"""
Service client for UI to connect to pyjarvis_service
"""

import asyncio
import json
import struct
from typing import Optional, Callable
from loguru import logger
from pyjarvis_shared import (
    ServiceCommand,
    ServiceResponse,
    TextToVoiceRequest,
    VoiceProcessingUpdate,
    ProcessingStatus,
    Emotion,
    AppConfig,
)


class ServiceClient:
    """Client for connecting to pyjarvis_service"""
    
    def __init__(self, config: Optional[AppConfig] = None):
        """Create a new service client"""
        self.config = config or AppConfig()
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.update_callback: Optional[Callable[[VoiceProcessingUpdate], None]] = None
        self.listening_task: Optional[asyncio.Task] = None
        self.connected = False
        
    async def connect(self) -> None:
        """Connect to the service"""
        if self.connected:
            return
        
        # Close any existing connections first
        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except:
                pass
            self.writer = None
            self.reader = None
            
        logger.info(f"[UI] Connecting to service at {self.config.tcp_host}:{self.config.tcp_port}...")
        try:
            # Use a short timeout for connection attempt
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(
                    self.config.tcp_host,
                    self.config.tcp_port
                ),
                timeout=2.0
            )
            self.connected = True
            logger.info("[UI] Connected to service")
        except asyncio.TimeoutError:
            logger.debug(f"[UI] Connection timeout")
            self.connected = False
            raise ConnectionError("Connection timeout - service may not be running")
        except Exception as e:
            logger.debug(f"[UI] Failed to connect to service: {e}")
            self.connected = False
            raise
    
    async def register_for_broadcasts(self, update_callback: Callable[[VoiceProcessingUpdate], None]) -> None:
        """
        Register as a UI client to receive broadcast updates
        
        Args:
            update_callback: Callback function to call when updates are received
        """
        self.update_callback = update_callback
        
        # Ensure connected
        if not self.connected:
            await self.connect()
        
        # Send RegisterUI command
        logger.info("[UI] Registering as UI client...")
        command = ServiceCommand.register_ui()
        await self._send_message(command)
        
        # Receive acknowledgment
        response = await self._receive_message()
        if response.response_type == "Ack":
            logger.info("[UI] Registered as UI client successfully")
            # Start listening for broadcasts
            self.listening_task = asyncio.create_task(self._listen_for_broadcasts())
        else:
            logger.error(f"[UI] Failed to register: {response}")
            raise ConnectionError(f"Failed to register as UI client: {response}")
    
    async def send_text(self, text: str, language: Optional[str] = None) -> None:
        """
        Send text to service for processing
        
        Args:
            text: Text to process
            language: Optional language code
        """
        if not self.connected:
            await self.connect()
        
        logger.info(f"[UI] Sending text to service: '{text}'")
        request = TextToVoiceRequest(text=text, language=language)
        command = ServiceCommand.process_text(request)
        await self._send_message(command)
        logger.debug("[UI] Text sent to service - waiting for broadcast update")
        # Note: We don't read the direct response here because:
        # 1. The service broadcasts updates to all UI clients (including us)
        # 2. Our _listen_for_broadcasts task will receive the update
        # 3. Reading here would conflict with the broadcast listener
    
    async def _listen_for_broadcasts(self) -> None:
        """Listen for broadcast updates from service"""
        logger.info("[UI] Listening for broadcast updates...")
        
        try:
            while self.connected and self.reader:
                try:
                    # Read message length (4 bytes)
                    length_bytes = await self.reader.readexactly(4)
                    length = struct.unpack('<I', length_bytes)[0]
                    
                    # Read message data in chunks if large
                    data = await self._read_chunked(length)
                    
                    # Deserialize JSON
                    response_dict = json.loads(data.decode('utf-8'))
                    response = ServiceResponse(**response_dict)
                    
                    # Handle update
                    if response.response_type == "Update" and response.update and self.update_callback:
                        update = self._parse_update(response.update)
                        logger.info(f"[UI] Received update: {update.status}")
                        self.update_callback(update)
                    
                except asyncio.IncompleteReadError:
                    logger.debug("[UI] Connection closed by server")
                    break
                except ConnectionError as e:
                    logger.debug(f"[UI] Connection error: {e}")
                    break
                except Exception as e:
                    logger.error(f"[UI] Error reading broadcast: {e}")
                    import traceback
                    logger.debug(traceback.format_exc())
                    break
                    
        except Exception as e:
            logger.error(f"[UI] Broadcast listener error: {e}")
            import traceback
            logger.debug(traceback.format_exc())
        finally:
            self.connected = False
            # Notify callback that connection was lost
            if self.update_callback:
                try:
                    # Create a dummy update to signal connection loss
                    # The UI should check service_client.connected to update status
                    pass
                except:
                    pass
            logger.info("[UI] Stopped listening for broadcasts - connection lost")
    
    async def _read_chunked(self, length: int) -> bytes:
        """Read data in chunks"""
        chunk_size = 64 * 1024  # 64KB
        if length > chunk_size:
            data = b""
            bytes_read = 0
            while bytes_read < length:
                chunk = await self.reader.readexactly(min(chunk_size, length - bytes_read))
                data += chunk
                bytes_read += len(chunk)
            return data
        else:
            return await self.reader.readexactly(length)
    
    async def _send_message(self, command: ServiceCommand) -> None:
        """Send a message to the service"""
        if not self.writer:
            raise ConnectionError("Not connected to service")
        
        data = json.dumps(command.model_dump()).encode('utf-8')
        length = len(data)
        
        # Send length prefix
        self.writer.write(struct.pack('<I', length))
        self.writer.write(data)
        await self.writer.drain()
    
    async def _receive_message(self) -> ServiceResponse:
        """Receive a message from the service"""
        if not self.reader:
            raise ConnectionError("Not connected to service")
        
        # Read length
        length_bytes = await self.reader.readexactly(4)
        length = struct.unpack('<I', length_bytes)[0]
        
        # Read data
        data = await self._read_chunked(length)
        
        # Deserialize
        response_dict = json.loads(data.decode('utf-8'))
        return ServiceResponse(**response_dict)
    
    def _parse_update(self, update_dict: dict) -> VoiceProcessingUpdate:
        """Parse update dictionary to VoiceProcessingUpdate"""
        # Parse status
        status_str = update_dict.get("status", "Ready")
        status = ProcessingStatus(status_str) if status_str in [s.value for s in ProcessingStatus] else ProcessingStatus.READY
        
        # Parse audio_file_path (preferred)
        audio_file_path = update_dict.get("audio_file_path")
        
        # Parse audio_data (hex string) - backward compatibility
        audio_data = None
        if not audio_file_path:  # Only use audio_data if file_path not available
            audio_hex = update_dict.get("audio_data")
            if audio_hex:
                try:
                    audio_data = bytes.fromhex(audio_hex)
                except Exception as e:
                    logger.warning(f"[UI] Failed to parse audio_data: {e}")
        
        # Parse emotion
        emotion = None
        emotion_str = update_dict.get("emotion")
        if emotion_str:
            try:
                emotion = Emotion(emotion_str)
            except:
                pass
        
        # Parse subject
        subject = update_dict.get("subject")
        
        return VoiceProcessingUpdate(
            status=status,
            audio_data=audio_data,  # Deprecated
            audio_file_path=audio_file_path,  # Preferred
            emotion=emotion,
            subject=subject
        )
    
    async def disconnect(self) -> None:
        """Disconnect from service"""
        if self.listening_task:
            self.listening_task.cancel()
            try:
                await self.listening_task
            except asyncio.CancelledError:
                pass
        
        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except:
                pass
        
        self.connected = False
        logger.info("[UI] Disconnected from service")

