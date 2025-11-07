"""
Unit tests for pyjarvis_ui.service_client module
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from pyjarvis_ui.service_client import ServiceClient
from pyjarvis_shared import AppConfig, ServiceCommand


class TestServiceClient:
    """Tests for ServiceClient class"""
    
    @pytest.fixture
    def client(self, app_config):
        """Create a ServiceClient instance"""
        return ServiceClient(app_config)
    
    def test_client_initialization(self, client, app_config):
        """Test ServiceClient initialization"""
        assert client.config == app_config
    
    @pytest.mark.asyncio
    async def test_connect(self, client):
        """Test connecting to service"""
        with patch('asyncio.open_connection') as mock_conn:
            mock_reader = AsyncMock()
            mock_writer = Mock()
            mock_conn.return_value = (mock_reader, mock_writer)
            
            await client.connect()
            assert client.is_connected() is True
    
    @pytest.mark.asyncio
    async def test_disconnect(self, client):
        """Test disconnecting from service"""
        await client.disconnect()
        assert client.is_connected() is False
    
    @pytest.mark.asyncio
    async def test_send_command(self, client):
        """Test sending a command"""
        command = ServiceCommand.process_text("Hello")
        
        with patch.object(client, 'connect') as mock_connect:
            mock_connect.return_value = AsyncMock()
            await client.send_command(command)
            # Add assertions based on implementation
    
    @pytest.mark.asyncio
    async def test_receive_updates(self, client):
        """Test receiving updates"""
        with patch.object(client, 'connect') as mock_connect:
            mock_connect.return_value = AsyncMock()
            updates = await client.receive_updates()
            assert updates is not None


