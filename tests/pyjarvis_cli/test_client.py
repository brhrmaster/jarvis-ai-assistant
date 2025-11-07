"""
Unit tests for pyjarvis_cli.client module
"""
import pytest
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
            mock_writer = Mock()
            mock_reader.read = AsyncMock(return_value=b'{"success": true}')
            mock_conn.return_value = (mock_reader, mock_writer)
            
            result = await send_text_to_service(text, app_config)
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_send_text_connection_error(self, app_config):
        """Test handling connection errors"""
        text = "Hello, world!"
        
        with patch('asyncio.open_connection') as mock_conn:
            mock_conn.side_effect = ConnectionError("Connection failed")
            
            with pytest.raises(ConnectionError):
                await send_text_to_service(text, app_config)
    
    def test_client_configuration(self, app_config):
        """Test client configuration"""
        assert app_config.tcp_host == "127.0.0.1"
        assert app_config.tcp_port == 8888


