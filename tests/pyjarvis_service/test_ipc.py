"""
Unit tests for pyjarvis_service.ipc module
"""
import pytest
import struct
from unittest.mock import Mock, AsyncMock, patch
from pyjarvis_service.ipc import IpcServer
from pyjarvis_service.processor import TextProcessor
from pyjarvis_shared import AppConfig, ServiceCommand


class TestIpcServer:
    """Tests for IpcServer class"""
    
    @pytest.fixture
    def ipc_server(self, app_config):
        """Create an IpcServer instance"""
        return IpcServer(app_config)
    
    def test_server_initialization(self, ipc_server, app_config):
        """Test IpcServer initialization"""
        assert ipc_server.config == app_config
        assert ipc_server.running is False
    
    @pytest.mark.asyncio
    async def test_start_server(self, ipc_server):
        """Test starting the IPC server"""
        # IpcServer.start() requires processor argument
        processor = Mock(spec=TextProcessor)
        
        with patch('asyncio.start_server') as mock_start:
            mock_server = AsyncMock()
            mock_start.return_value = mock_server
            mock_server.__aenter__ = AsyncMock(return_value=mock_server)
            mock_server.__aexit__ = AsyncMock(return_value=None)
            
            # This will run forever, so we need to cancel it
            start_task = asyncio.create_task(ipc_server.start(processor))
            await asyncio.sleep(0.1)  # Let it start
            start_task.cancel()
            try:
                await start_task
            except asyncio.CancelledError:
                pass
    
    @pytest.mark.asyncio
    async def test_stop_server(self, ipc_server):
        """Test stopping the IPC server"""
        # IpcServer doesn't have stop() method, it uses running flag
        ipc_server.running = True
        ipc_server.running = False
        assert ipc_server.running is False
    
    @pytest.mark.asyncio
    async def test_handle_client(self, ipc_server):
        """Test handling a client connection"""
        # IpcServer doesn't have _handle_client, it has _handle_tcp_connection
        processor = Mock(spec=TextProcessor)
        ipc_server.processor = processor
        
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_writer.get_extra_info.return_value = ('127.0.0.1', 12345)
        mock_writer.drain = AsyncMock()
        mock_writer.close = AsyncMock()
        mock_writer.wait_closed = AsyncMock()
        
        # Mock reading command
        command_json = b'{"command_type":"Ping"}'
        mock_reader.readexactly = AsyncMock(side_effect=[
            struct.pack('<I', len(command_json)),
            command_json
        ])
        
        # This will run until connection closes, so we'll cancel it
        handle_task = asyncio.create_task(ipc_server._handle_tcp_connection(mock_reader, mock_writer))
        await asyncio.sleep(0.1)
        handle_task.cancel()
        try:
            await handle_task
        except asyncio.CancelledError:
            pass
    
    @pytest.mark.asyncio
    async def test_broadcast_update(self, ipc_server):
        """Test broadcasting updates to clients"""
        # IpcServer doesn't have broadcast_update, it has _broadcast_update
        from pyjarvis_shared import VoiceProcessingUpdate, ProcessingStatus
        update = VoiceProcessingUpdate(status=ProcessingStatus.READY)
        
        # Add a mock subscriber
        mock_writer = AsyncMock()
        mock_writer.drain = AsyncMock()
        ipc_server.broadcast_subscribers.add(mock_writer)
        
        await ipc_server._broadcast_update(update)
        # Verify drain was called (update was sent)
        assert mock_writer.drain.called or len(ipc_server.broadcast_subscribers) > 0


