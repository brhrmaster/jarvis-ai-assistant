"""
IPC communication for service using named pipes (Windows)
"""

import asyncio
import json
import struct
import sys
from typing import Optional, Dict, Set
from loguru import logger
from pyjarvis_shared import (
    ServiceCommand,
    ServiceResponse,
    VoiceProcessingUpdate,
    AppConfig,
    TextToVoiceRequest,
    ProcessingStatus,
)
from .processor import TextProcessor


class IpcServer:
    """IPC server for receiving commands from CLI"""
    
    def __init__(self, config: Optional[AppConfig] = None):
        """Create a new IPC server"""
        self.config = config or AppConfig()
        self.endpoint = self.config.pipe_name
        self.processor: Optional[TextProcessor] = None
        self.broadcast_subscribers: Set[asyncio.StreamWriter] = set()
        self.running = False
    
    async def start(self, processor: TextProcessor) -> None:
        """
        Start the IPC server
        
        Args:
            processor: Text processor instance
        """
        self.processor = processor
        logger.info(f"Starting IPC server using TCP sockets")
        
        # Use TCP sockets for all platforms (simpler and more reliable)
        await self._start_tcp_server()
    
    async def _start_named_pipe_server(self) -> None:
        """Start Windows named pipe server"""
        import win32pipe
        import win32file
        import pywintypes
        
        self.running = True
        logger.info(f"[IPC] Waiting for client connections on: {self.endpoint}")
        
        loop = asyncio.get_event_loop()
        
        while self.running:
            try:
                # Create named pipe - run in thread pool to avoid blocking
                # Use byte mode (not message mode) for simpler communication
                handle = await loop.run_in_executor(
                    None,
                    lambda: win32pipe.CreateNamedPipe(
                        self.endpoint,
                        win32pipe.PIPE_ACCESS_DUPLEX,
                        win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_READMODE_BYTE | win32pipe.PIPE_WAIT,
                        10,  # max instances
                        65536,  # out buffer size
                        65536,  # in buffer size
                        0,  # default timeout
                        None  # security attributes
                    )
                )
                
                logger.info("[IPC] Waiting for client connection...")
                
                # CRITICAL: Spawn handler FIRST, then wait for connection
                # This ensures handler runs even if ConnectNamedPipe blocks
                logger.info(f"[IPC] PRE-SPAWNING handler task for handle {handle} (before ConnectNamedPipe)")
                handler_task = asyncio.create_task(self._handle_named_pipe(handle))
                logger.info(f"[IPC] Handler task PRE-SPAWNED: {handler_task}")
                
                # Now wait for client - blocking call (but in thread pool so it doesn't block event loop)
                try:
                    logger.debug(f"[IPC] Calling ConnectNamedPipe on handle {handle}...")
                    # ConnectNamedPipe blocks until client connects
                    # This will raise ERROR_PIPE_CONNECTED (535) if client connects before we call it
                    try:
                        connect_result = await loop.run_in_executor(
                            None,
                            lambda h=handle: win32pipe.ConnectNamedPipe(h, None)
                        )
                        logger.info(f"[IPC] ConnectNamedPipe returned: {connect_result}")
                        logger.info("[IPC] Client connected successfully (normal flow)")
                    except pywintypes.error as connect_err:
                        logger.info(f"[IPC] ConnectNamedPipe exception: {connect_err} (winerror={connect_err.winerror})")
                        if connect_err.winerror == 535:  # ERROR_PIPE_CONNECTED - client already connected
                            logger.info("[IPC] Client already connected (ERROR_PIPE_CONNECTED - expected)")
                        elif connect_err.winerror == 232:  # ERROR_NO_DATA - client disconnected
                            logger.warning("[IPC] Client disconnected immediately")
                            await loop.run_in_executor(None, lambda h=handle: win32file.CloseHandle(h))
                            continue  # Skip to next iteration
                        else:
                            logger.warning(f"[IPC] Unexpected ConnectNamedPipe error: {connect_err.winerror}, continuing anyway")
                    
                    # Handler is already running, just verify it's still alive
                    logger.info(f"[IPC] Handler task status: done={handler_task.done()}, cancelled={handler_task.cancelled()}")
                    
                    # Small delay to let handler start
                    await asyncio.sleep(0.01)
                    
                except Exception as e:
                    logger.error(f"[IPC] Error in connection setup: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    # Handler should still be running, let it handle errors
                    await asyncio.sleep(0.01)
                        
            except KeyboardInterrupt:
                logger.info("[IPC] Server interrupted")
                self.running = False
                break
            except Exception as e:
                logger.error(f"[IPC] Server error: {e}")
                import traceback
                logger.debug(traceback.format_exc())
                await asyncio.sleep(1)
    
    async def _handle_named_pipe(self, handle: int) -> None:
        """Handle a named pipe connection"""
        import win32file
        import win32pipe
        import pywintypes
        import sys
        
        try:
            loop = asyncio.get_event_loop()
            logger.info(f"[IPC] ========== HANDLER STARTED for handle {handle} ==========")
            logger.info(f"[IPC] Handler task: {asyncio.current_task()}")
            logger.info(f"[IPC] Event loop: {loop}")
            logger.info(f"[IPC] Python version: {sys.version}")
            pipe_closed = False
        except Exception as init_err:
            logger.error(f"[IPC] FATAL: Handler failed to initialize: {init_err}")
            import traceback
            logger.error(traceback.format_exc())
            return
        
        try:
            # Wait for client to connect and write data
            # Try reading with retries since we might start before client connects
            max_retries = 10
            retry_delay = 0.1
            read_success = False
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"[IPC] Attempt {attempt + 1}/{max_retries}: Waiting to read message length (4 bytes)...")
                    result, data = await loop.run_in_executor(
                        None, 
                        lambda h=handle: win32file.ReadFile(h, 4)
                    )
                    logger.info(f"[IPC] ReadFile(length) succeeded: result={result}, data_len={len(data) if data else 0}")
                    read_success = True
                    break
                except pywintypes.error as read_err:
                    if read_err.winerror == 109:  # ERROR_BROKEN_PIPE
                        logger.warning(f"[IPC] Pipe broken, client may have disconnected (attempt {attempt + 1})")
                        return
                    elif read_err.winerror == 232:  # ERROR_NO_DATA - pipe not ready yet
                        logger.debug(f"[IPC] No data yet, waiting {retry_delay}s before retry...")
                        await asyncio.sleep(retry_delay)
                    else:
                        logger.warning(f"[IPC] ReadFile error: {read_err} (winerror={read_err.winerror}), retrying...")
                        await asyncio.sleep(retry_delay)
                except Exception as read_ex:
                    logger.warning(f"[IPC] Unexpected read error: {read_ex}, retrying...")
                    await asyncio.sleep(retry_delay)
            
            if not read_success:
                logger.error(f"[IPC] Failed to read message after {max_retries} attempts")
                return
            
            try:
                logger.info(f"[IPC] ReadFile(length) returned: result={result}, data_len={len(data) if data else 0}")
                
                if result != 0:
                    logger.error(f"[IPC] ReadFile error code: {result}")
                    return
                
                if not data or len(data) != 4:
                    logger.error(f"[IPC] Failed to read message length: got {len(data) if data else 0} bytes, expected 4")
                    return
                    
                length = struct.unpack('<I', data)[0]
                logger.info(f"[IPC] Received message length: {length} bytes")
                
                if length > 1024 * 1024:  # 1MB limit
                    logger.error(f"[IPC] Message too large: {length} bytes")
                    return
                
                # Read message data - run in thread pool
                logger.info(f"[IPC] Reading message data ({length} bytes)...")
                result, data = await loop.run_in_executor(
                    None,
                    lambda h=handle, size=length: win32file.ReadFile(h, size)
                )
                
                if result != 0:
                    logger.error(f"[IPC] ReadFile(data) error code: {result}")
                    return
                    
                logger.info(f"[IPC] ReadFile(data) returned: {len(data) if data else 0} bytes")
                
                if len(data) != length:
                    logger.error(f"[IPC] Incomplete message: got {len(data)}, expected {length}")
                    return
                
                # Deserialize JSON
                logger.debug("[IPC] Deserializing JSON command...")
                command_dict = json.loads(data.decode('utf-8'))
                command = ServiceCommand(**command_dict)
                
                logger.info(f"[IPC] Received command: {command.command_type}")
                
                # Process command
                logger.info("[IPC] Processing command...")
                response = await self._process_command(command)
                logger.info(f"[IPC] Command processed, response type: {response.response_type}")
                
                # Send response
                logger.info("[IPC] Sending response...")
                await self._send_named_pipe_message(handle, response)
                
                logger.info("[IPC] Response sent successfully")
                
                # Flush the pipe to ensure data is sent
                try:
                    await loop.run_in_executor(
                        None,
                        lambda h=handle: win32file.FlushFileBuffers(h)
                    )
                    logger.debug("[IPC] Pipe flushed")
                except Exception as e:
                    logger.warning(f"[IPC] Failed to flush pipe: {e}")
                
                # Give client time to read response before closing
                logger.debug("[IPC] Waiting 0.5s for client to read response...")
                await asyncio.sleep(0.5)
                
                logger.info("[IPC] Command processing complete")
                    
            except pywintypes.error as e:
                logger.error(f"[IPC] Windows error processing message: {e} (winerror={e.winerror})")
                import traceback
                logger.debug(traceback.format_exc())
                pipe_closed = True
            except Exception as e:
                logger.error(f"[IPC] Error processing message: {e}")
                import traceback
                logger.debug(traceback.format_exc())
                pipe_closed = True
            finally:
                if not pipe_closed:
                    logger.debug("[IPC] Closing pipe handle...")
                    try:
                        await loop.run_in_executor(None, lambda h=handle: win32file.CloseHandle(h))
                        logger.debug("[IPC] Pipe handle closed")
                    except Exception as close_err:
                        logger.warning(f"[IPC] Error closing handle: {close_err}")
                    
        except Exception as e:
            logger.error(f"[IPC] Error handling connection: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            if not pipe_closed:
                try:
                    await loop.run_in_executor(None, lambda h=handle: win32file.CloseHandle(h))
                except:
                    pass
            logger.info("[IPC] Client disconnected")
    
    async def _send_named_pipe_message(self, handle: int, response: ServiceResponse) -> None:
        """Send a message through named pipe"""
        import win32file
        import pywintypes
        
        loop = asyncio.get_event_loop()
        
        # Serialize response
        data = json.dumps(response.model_dump()).encode('utf-8')
        length = len(data)
        
        logger.info(f"[IPC] Serialized response: {length} bytes")
        
        try:
            # Send length prefix (4 bytes, little-endian) - run in thread pool
            length_bytes = struct.pack('<I', length)
            logger.debug(f"[IPC] Sending length prefix: {length} bytes")
            result = await loop.run_in_executor(
                None,
                lambda h=handle, lb=length_bytes: win32file.WriteFile(h, lb)
            )
            logger.info(f"[IPC] Length prefix sent, result={result}")
            
            # Send message data - run in thread pool
            logger.debug(f"[IPC] Sending response data: {len(data)} bytes")
            result = await loop.run_in_executor(
                None,
                lambda h=handle, d=data: win32file.WriteFile(h, d)
            )
            logger.info(f"[IPC] Response data sent, result={result}, {len(data)} bytes")
            
        except pywintypes.error as e:
            logger.error(f"[IPC] Windows error sending message: {e} (winerror={e.winerror})")
            raise
        except Exception as e:
            logger.error(f"[IPC] Error sending message: {e}")
            raise
    
    async def _start_tcp_server(self) -> None:
        """Start TCP server"""
        host = self.config.tcp_host
        port = self.config.tcp_port
        
        logger.info(f"[IPC] Starting TCP server on {host}:{port}")
        
        server = await asyncio.start_server(
            self._handle_tcp_connection,
            host,
            port
        )
        
        logger.info(f"[IPC] TCP server listening on {host}:{port}")
        self.running = True
        
        async with server:
            await server.serve_forever()
    
    async def _handle_tcp_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """Handle a TCP client connection"""
        client_addr = writer.get_extra_info('peername')
        logger.info(f"[IPC] Client connected (TCP) from {client_addr}")
        is_ui_client = False
        
        try:
            while self.running:
                # Read message length (4 bytes)
                logger.debug(f"[IPC] Waiting to read message length from {client_addr}...")
                length_bytes = await reader.readexactly(4)
                length = struct.unpack('<I', length_bytes)[0]
                logger.info(f"[IPC] Received message length: {length} bytes from {client_addr}")
                
                if length > 1024 * 1024:  # 1MB limit
                    logger.error(f"[IPC] Message too large: {length} bytes from {client_addr}")
                    break
                
                # Read message data
                logger.debug(f"[IPC] Reading message data ({length} bytes) from {client_addr}...")
                data = await reader.readexactly(length)
                logger.info(f"[IPC] Received {len(data)} bytes from {client_addr}")
                
                # Deserialize JSON
                logger.debug(f"[IPC] Deserializing command from {client_addr}...")
                command_dict = json.loads(data.decode('utf-8'))
                command = ServiceCommand(**command_dict)
                
                logger.info(f"[IPC] Received command: {command.command_type} from {client_addr}")
                
                # Handle UI registration
                if command.command_type == "RegisterUI":
                    logger.info(f"[IPC] Registering UI client from {client_addr}")
                    is_ui_client = True
                    self.broadcast_subscribers.add(writer)
                    response = ServiceResponse.ack()
                    await self._send_tcp_message(writer, response)
                    logger.info(f"[IPC] UI client {client_addr} registered, continuing to listen for broadcasts")
                    # For UI clients, we keep the connection open to send broadcasts
                    continue
                
                # Process command
                logger.info(f"[IPC] Processing command from {client_addr}...")
                try:
                    response = await self._process_command(command)
                    logger.info(f"[IPC] Command processed, response type: {response.response_type}")
                except Exception as proc_err:
                    logger.error(f"[IPC] Error processing command from {client_addr}: {proc_err}")
                    import traceback
                    logger.error(traceback.format_exc())
                    # Send error response instead of crashing
                    response = ServiceResponse.create_error(str(proc_err))
                
                # Send response - CRITICAL: Always send a response
                logger.debug(f"[IPC] Preparing to send response to {client_addr}...")
                try:
                    await self._send_tcp_message(writer, response)
                    logger.info(f"[IPC] Response sent successfully to {client_addr}")
                except Exception as send_err:
                    logger.error(f"[IPC] Failed to send response to {client_addr}: {send_err}")
                    import traceback
                    logger.error(traceback.format_exc())
                    # Don't raise - connection will be closed in finally
                
                # For CLI clients, close after one command
                # For UI clients, keep connection open for broadcasts
                if not is_ui_client:
                    logger.debug(f"[IPC] CLI client {client_addr} done, closing connection")
                    break
                    
        except asyncio.IncompleteReadError:
            logger.debug(f"[IPC] Client {client_addr} disconnected (IncompleteReadError)")
        except ConnectionResetError:
            logger.debug(f"[IPC] Client {client_addr} connection reset")
        except Exception as e:
            logger.error(f"[IPC] Error handling connection from {client_addr}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Try to send error response if connection is still open
            try:
                error_response = ServiceResponse.create_error(f"Internal error: {str(e)}")
                await self._send_tcp_message(writer, error_response)
            except:
                pass  # Connection might be closed
        finally:
            if is_ui_client:
                self.broadcast_subscribers.discard(writer)
                logger.info(f"[IPC] UI client {client_addr} unregistered")
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass
            logger.info(f"[IPC] Client {client_addr} disconnected")
    
    async def _send_tcp_message(self, writer: asyncio.StreamWriter, response: ServiceResponse) -> None:
        """Send a message to TCP client"""
        try:
            # Serialize response
            logger.debug(f"[IPC] Serializing ServiceResponse: type={response.response_type}")
            response_dict = response.model_dump()
            logger.debug(f"[IPC] Response dict keys: {list(response_dict.keys())}")
            
            # Check update size if present
            if response_dict.get('update') and response_dict['update'].get('audio_data'):
                audio_hex_len = len(response_dict['update']['audio_data'])
                logger.info(f"[IPC] Audio data hex length: {audio_hex_len} characters ({audio_hex_len // 2} bytes raw)")
            
            data = json.dumps(response_dict).encode('utf-8')
            length = len(data)
            logger.info(f"[IPC] Serialized response: {length} bytes total")
            
            # Send length prefix (4 bytes, little-endian)
            logger.debug(f"[IPC] Sending length prefix: {length} bytes")
            writer.write(struct.pack('<I', length))
            await writer.drain()
            
            # Send message data in chunks if large
            chunk_size = 64 * 1024  # 64KB chunks
            if length > chunk_size:
                logger.info(f"[IPC] Sending large response in chunks ({chunk_size} bytes per chunk)")
                sent = 0
                while sent < length:
                    chunk = data[sent:sent + chunk_size]
                    writer.write(chunk)
                    await writer.drain()
                    sent += len(chunk)
                    logger.debug(f"[IPC] Sent chunk: {sent}/{length} bytes")
            else:
                writer.write(data)
                await writer.drain()
            
            logger.info(f"[IPC] Response sent: {length} bytes total")
        except Exception as e:
            logger.error(f"[IPC] Error in _send_tcp_message: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    async def _process_command(self, command: ServiceCommand) -> ServiceResponse:
        """Process a service command"""
        if not self.processor:
            return ServiceResponse.create_error("Processor not initialized")
        
        try:
            if command.command_type == "ProcessText":
                # Extract request from command
                request_dict = command.request or {}
                request = TextToVoiceRequest(
                    text=request_dict.get("text", ""),
                    language=request_dict.get("language")
                )
                
                logger.info(f"[IPC] Processing text request: '{request.text}'")
                
                # Process the text
                update = await self.processor.process(request)
                
                # Broadcast to all UI subscribers (non-blocking - don't fail if broadcast fails)
                try:
                    await self._broadcast_update(update)
                except Exception as broadcast_err:
                    logger.warning(f"[IPC] Broadcast failed (non-critical): {broadcast_err}")
                
                logger.info(f"[IPC] Processing complete, status: {update.status}")
                logger.debug(f"[IPC] Creating ServiceResponse with update...")
                try:
                    response = ServiceResponse.create_update(update)
                    logger.debug(f"[IPC] ServiceResponse created successfully: {response.response_type}")
                    return response
                except Exception as resp_err:
                    logger.error(f"[IPC] Failed to create ServiceResponse: {resp_err}")
                    import traceback
                    logger.error(traceback.format_exc())
                    raise
                
            elif command.command_type == "RegisterUI":
                # This is handled in the TCP connection handler, but we keep this for compatibility
                logger.debug("[IPC] RegisterUI command (should be handled in connection handler)")
                return ServiceResponse.ack()
                
            elif command.command_type == "Ping":
                logger.debug("[IPC] Received ping")
                return ServiceResponse.pong()
                
            elif command.command_type == "Shutdown":
                logger.info("[IPC] Received shutdown command")
                self.running = False
                return ServiceResponse.ack()
                
            else:
                logger.warning(f"[IPC] Unknown command type: {command.command_type}")
                return ServiceResponse.create_error(f"Unknown command: {command.command_type}")
                
        except Exception as e:
            logger.error(f"[IPC] Error processing command: {e}")
            return ServiceResponse.create_error(str(e))
    
    async def _broadcast_update(self, update: VoiceProcessingUpdate) -> None:
        """Broadcast update to all registered UI clients"""
        if not self.broadcast_subscribers:
            logger.debug("[IPC] No UI clients subscribed to broadcasts")
            return
        
        response = ServiceResponse.create_update(update)
        disconnected = set()
        
        for writer in self.broadcast_subscribers:
            try:
                await self._send_tcp_message(writer, response)
            except Exception as e:
                logger.debug(f"[IPC] Failed to broadcast to client: {e}")
                disconnected.add(writer)
        
        # Remove disconnected clients
        self.broadcast_subscribers -= disconnected
        
        if self.broadcast_subscribers:
            logger.info(f"[IPC] Broadcasted update to {len(self.broadcast_subscribers)} UI client(s)")
    
    def stop(self) -> None:
        """Stop the IPC server"""
        self.running = False
        logger.info("[IPC] Server stopped")
