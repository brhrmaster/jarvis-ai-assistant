"""
Unit tests for pyjarvis_cli.client module
"""
import pytest
import struct
from unittest.mock import Mock, AsyncMock, patch
from pyjarvis_cli.client import send_text_to_service
from pyjarvis_shared import AppConfig


class TestClient:
    """Tests for CLI client functions"""
    
    @pytest.mark.asyncio
    async def test_send_text_to_service(self, app_config):
        """Test sending text to service"""
        text = "Hello, world!"
        
        with patch('asyncio.open_connection') as mock_conn:
            mock_reader = AsyncMock()
            mock_writer = AsyncMock()  # Make writer async too
            mock_writer.drain = AsyncMock()
            mock_writer.wait_closed = AsyncMock()
            mock_writer.write = Mock()
            mock_writer.close = Mock()
            # Mock the response reading - first 4 bytes for length, then the JSON
            response_json = b'{"response_type":"Ack"}'
            response_length = len(response_json)
            mock_reader.readexactly = AsyncMock(side_effect=[
                struct.pack('<I', response_length),  # First call: length
                response_json  # Second call: data
            ])
            mock_conn.return_value = (mock_reader, mock_writer)
            
            # send_text_to_service doesn't take app_config, it creates its own
            result = await send_text_to_service(text)
            assert result is None  # Function returns None
    
    @pytest.mark.asyncio
    async def test_send_text_connection_error(self, app_config):
        """Test handling connection errors"""
        text = "Hello, world!"
        
        with patch('asyncio.open_connection') as mock_conn:
            mock_conn.side_effect = ConnectionRefusedError("Connection refused")
            
            with pytest.raises(ConnectionError):
                await send_text_to_service(text)  # Doesn't take app_config
    
    def test_client_configuration(self, app_config):
        """Test client configuration"""
        assert app_config.tcp_host == "127.0.0.1"
        assert app_config.tcp_port == 8888


