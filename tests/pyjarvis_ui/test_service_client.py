"""
Unit tests for pyjarvis_ui.service_client module
"""
import pytest
import struct
from unittest.mock import Mock, AsyncMock, patch
from pyjarvis_ui.service_client import ServiceClient
from pyjarvis_shared import AppConfig, ServiceCommand, TextToVoiceRequest


class TestServiceClient:
    """Tests for ServiceClient class"""
    
    @pytest.fixture
    def client(self, app_config):
        """Create a ServiceClient instance"""
        return ServiceClient(app_config)
    
    def test_client_initialization(self, client, app_config):
        """Test ServiceClient initialization"""
        assert client.config == app_config
        assert client.connected is False
    
    @pytest.mark.asyncio
    async def test_connect(self, client):
        """Test connecting to service"""
        with patch('asyncio.open_connection') as mock_conn:
            mock_reader = AsyncMock()
            mock_writer = AsyncMock()
            mock_writer.wait_closed = AsyncMock()
            mock_conn.return_value = (mock_reader, mock_writer)
            
            await client.connect()
            assert client.connected is True  # Use connected attribute, not is_connected()
    
    @pytest.mark.asyncio
    async def test_disconnect(self, client):
        """Test disconnecting from service"""
        # First connect
        with patch('asyncio.open_connection') as mock_conn:
            mock_reader = AsyncMock()
            mock_writer = AsyncMock()
            mock_writer.wait_closed = AsyncMock()
            mock_conn.return_value = (mock_reader, mock_writer)
            await client.connect()
        
        # Then disconnect
        await client.disconnect()
        assert client.connected is False  # Use connected attribute, not is_connected()
    
    @pytest.mark.asyncio
    async def test_send_command(self, client):
        """Test sending a command"""
        # ServiceClient doesn't have send_command, it has send_text
        # But we can test _send_message which is used internally
        request = TextToVoiceRequest(text="Hello")
        command = ServiceCommand.process_text(request)
        
        with patch('asyncio.open_connection') as mock_conn:
            mock_reader = AsyncMock()
            mock_writer = AsyncMock()
            mock_writer.drain = AsyncMock()
            mock_writer.wait_closed = AsyncMock()
            mock_conn.return_value = (mock_reader, mock_writer)
            await client.connect()
            
            await client._send_message(command)
            # Verify writer.write was called
            assert mock_writer.write.called
    
    @pytest.mark.asyncio
    async def test_receive_updates(self, client):
        """Test receiving updates"""
        # ServiceClient doesn't have receive_updates method
        # Updates are received via _listen_for_broadcasts which is called after register_for_broadcasts
        # We can test the connection and registration flow
        with patch('asyncio.open_connection') as mock_conn:
            mock_reader = AsyncMock()
            mock_writer = AsyncMock()
            mock_writer.drain = AsyncMock()
            mock_writer.wait_closed = AsyncMock()
            
            # Mock response for registration
            response_json = b'{"response_type":"Ack"}'
            response_length = len(response_json)
            mock_reader.readexactly = AsyncMock(side_effect=[
                struct.pack('<I', response_length),
                response_json
            ])
            
            mock_conn.return_value = (mock_reader, mock_writer)
            
            callback = Mock()
            await client.register_for_broadcasts(callback)
            assert client.connected is True
            assert client.update_callback == callback


