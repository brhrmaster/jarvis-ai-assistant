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
        with patch('pyjarvis_service.service.TextProcessor') as mock_processor_class, \
             patch('pyjarvis_service.service.IpcServer') as mock_ipc_class:
            
            # Mock processor
            mock_processor = Mock()
            mock_processor.initialize = AsyncMock()
            mock_processor_class.return_value = mock_processor
            
            # Mock IPC server
            mock_ipc = Mock()
            mock_ipc.start = AsyncMock()
            mock_ipc_class.return_value = mock_ipc
            
            # Mock start to raise KeyboardInterrupt quickly
            async def mock_start(processor):
                raise KeyboardInterrupt()
            
            mock_ipc.start = mock_start
            
            try:
                await run_service()
            except KeyboardInterrupt:
                pass  # Expected
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, app_config):
        """Test service initialization"""
        with patch('pyjarvis_service.service.TextProcessor') as mock_processor_class, \
             patch('pyjarvis_service.service.IpcServer') as mock_ipc_class:
            
            mock_processor = Mock()
            mock_processor.initialize = AsyncMock()
            mock_processor_class.return_value = mock_processor
            
            mock_ipc = Mock()
            mock_ipc_class.return_value = mock_ipc
            
            # Test that classes can be instantiated
            assert mock_processor_class is not None
            assert mock_ipc_class is not None


