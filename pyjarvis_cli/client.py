"""
IPC client for CLI
"""

import asyncio
import json
import struct
import sys
from typing import Optional
from loguru import logger
from pyjarvis_shared import TextToVoiceRequest, ServiceCommand, ServiceResponse, AppConfig

async def send_text_to_service(text: str, language: Optional[str] = None) -> None:
    """
    Send text to the voice service via IPC
    
    Args:
        text: Text to convert to voice
        language: Optional language code (e.g., "en", "pt-BR")
    """
    #logger.info("[CLI] Connecting to service...")
    logger.debug(f"[CLI] Target text: '{text}'")
    logger.debug(f"[CLI] Language override: {language}")
    
    config = AppConfig()
    request = TextToVoiceRequest(text=text, language=language)
    command = ServiceCommand.process_text(request)
    
    # Use TCP sockets for all platforms (simpler and more reliable)
    await _send_via_tcp(command, config)

async def _send_via_tcp(command: ServiceCommand, config: AppConfig) -> None:
    """Send command via TCP"""
    host = config.tcp_host
    port = config.tcp_port
    
    #logger.info(f"[CLI] Connecting to service via TCP at {host}:{port}...")
    try:
        reader, writer = await asyncio.open_connection(host, port)
        #logger.info("[CLI] Connected to service (TCP)")
        
        # Send command
        data = json.dumps(command.model_dump()).encode('utf-8')
        length = len(data)
        
        # Send length prefix
        writer.write(struct.pack('<I', length))
        writer.write(data)
        await writer.drain()
        
        #logger.info("[CLI] Command sent successfully")
        
        # Receive response
        #logger.debug("[CLI] Reading response length (4 bytes)...")
        length_bytes = await reader.readexactly(4)
        length = struct.unpack('<I', length_bytes)[0]
        #logger.info(f"[CLI] Response length: {length} bytes")
        
        # Read response data in chunks if large
        #logger.debug(f"[CLI] Reading response data ({length} bytes)...")
        chunk_size = 64 * 1024  # 64KB chunks
        if length > chunk_size:
            #logger.info(f"[CLI] Reading large response in chunks ({chunk_size} bytes per chunk)")
            data = b""
            bytes_read = 0
            while bytes_read < length:
                chunk = await reader.readexactly(min(chunk_size, length - bytes_read))
                data += chunk
                bytes_read += len(chunk)
                #logger.debug(f"[CLI] Read chunk: {bytes_read}/{length} bytes")
            #logger.info(f"[CLI] Read complete response: {len(data)} bytes")
        else:
            data = await reader.readexactly(length)
            #logger.info(f"[CLI] Read response: {len(data)} bytes")
        
        # Deserialize JSON
       # logger.debug("[CLI] Deserializing response JSON...")
        response_dict = json.loads(data.decode('utf-8'))
        response = ServiceResponse(**response_dict)
        #logger.info(f"[CLI] Response deserialized: {response.response_type}")
        
        # Handle response
        _handle_response(response)
        
        writer.close()
        await writer.wait_closed()
        #logger.debug("[CLI] Communication complete")
        
    except ConnectionRefusedError:
        logger.error(f"[CLI] Service not found. Is pyjarvis_service running?")
        raise ConnectionError("Service not found. Please start pyjarvis_service first.")
    except Exception as e:
        logger.error(f"[CLI] TCP connection error: {e}")
        raise

def _handle_response(response: ServiceResponse) -> None:
    if response.response_type == "Error":
        error_msg = response.error or "Unknown error"
        logger.error(f"[CLI] Service returned error: {error_msg}")
        raise RuntimeError(f"Service error: {error_msg}")
    elif response.response_type == "Pong":
        logger.debug("[CLI] Received Pong response")

def main() -> None:
    """CLI entry point"""
    import click
    
    @click.command()
    @click.argument('text')
    @click.option('--language', '-l', help='Language code (en, pt-BR)')
    def cli_main(text: str, language: Optional[str]):
        """Send text to PyJarvis service for voice synthesis"""
        try:
            asyncio.run(send_text_to_service(text, language))
            logger.info("[CLI] Text sent successfully")
        except Exception as e:
            logger.error(f"[CLI] Failed to send text: {e}")
            sys.exit(1)
    
    cli_main()

if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
    )
    
    main()
