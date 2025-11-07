"""
Unit tests for pyjarvis_llama.recording_queue module
"""
import pytest
from unittest.mock import Mock, AsyncMock
from pyjarvis_llama.recording_queue import (
    AudioRecordingQueue,
    RecordingStatus,
    RecordingTask,
    RecordingResult
)


class TestRecordingQueue:
    """Tests for AudioRecordingQueue class"""
    
    @pytest.fixture
    def queue(self):
        """Create an AudioRecordingQueue instance"""
        return AudioRecordingQueue()
    
    def test_queue_initialization(self, queue):
        """Test AudioRecordingQueue initialization"""
        assert queue is not None
    
    @pytest.mark.asyncio
    async def test_add_task(self, queue):
        """Test adding a recording task"""
        task = RecordingTask(audio_data=b"test", language="en")
        await queue.add_task(task)
        assert queue.has_tasks() is True
    
    @pytest.mark.asyncio
    async def test_process_task(self, queue):
        """Test processing a recording task"""
        task = RecordingTask(audio_data=b"test", language="en")
        await queue.add_task(task)
        
        result = await queue.process_next()
        assert result is not None
        assert isinstance(result, RecordingResult)
    
    def test_get_status(self, queue):
        """Test getting queue status"""
        status = queue.get_status()
        assert status is not None
        assert isinstance(status, RecordingStatus)


class TestRecordingTask:
    """Tests for RecordingTask class"""
    
    def test_task_creation(self):
        """Test creating a RecordingTask"""
        task = RecordingTask(audio_data=b"test", language="en")
        assert task.audio_data == b"test"
        assert task.language == "en"


class TestRecordingResult:
    """Tests for RecordingResult class"""
    
    def test_result_creation(self):
        """Test creating a RecordingResult"""
        result = RecordingResult(text="Hello", success=True)
        assert result.text == "Hello"
        assert result.success is True


