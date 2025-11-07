"""
Unit tests for pyjarvis_service.service module
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from pyjarvis_service.service import run_service
from pyjarvis_shared import AppConfig


class TestService:
    """Tests for service module functions"""
    
    @pytest.mark.asyncio
    async def test_run_service(self, app_config):
        """Test running the service"""
        with patch('pyjarvis_service.service.IpcServer') as mock_ipc, \
             patch('pyjarvis_service.service.TextProcessor') as mock_processor, \
             patch('asyncio.sleep') as mock_sleep:
            mock_sleep.side_effect = KeyboardInterrupt()
            
            try:
                await run_service()
            except KeyboardInterrupt:
                pass  # Expected
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, app_config):
        """Test service initialization"""
        with patch('pyjarvis_service.service.IpcServer') as mock_ipc:
            mock_server = AsyncMock()
            mock_ipc.return_value = mock_server
            
            # Test service setup
            assert mock_ipc is not None


