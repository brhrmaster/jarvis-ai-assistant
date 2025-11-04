"""
Audio buffer for managing audio data
"""

from typing import Optional
from loguru import logger


class AudioBuffer:
    """Audio buffer for managing audio data"""
    
    def __init__(self, sample_rate: int = 44100, channels: int = 1):
        """
        Create a new audio buffer
        
        Args:
            sample_rate: Sample rate in Hz
            channels: Number of audio channels
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self._buffer: bytearray = bytearray()
        logger.debug(f"Audio buffer created (sample_rate: {sample_rate}, channels: {channels})")
    
    def append(self, data: bytes) -> None:
        """
        Append audio data to the buffer
        
        Args:
            data: Audio data bytes to append
        """
        self._buffer.extend(data)
        logger.debug(f"Appended {len(data)} bytes to buffer. Buffer size: {len(self._buffer)}")
    
    def clear(self) -> None:
        """Clear the audio buffer"""
        self._buffer.clear()
        logger.debug("Audio buffer cleared")
    
    def len(self) -> int:
        """Get the length of the buffer in bytes"""
        return len(self._buffer)
    
    def get_data(self) -> bytes:
        """Get all audio data from the buffer"""
        return bytes(self._buffer)
    
    def pop(self, size: int) -> Optional[bytes]:
        """
        Pop audio data from the buffer
        
        Args:
            size: Number of bytes to pop
            
        Returns:
            Audio data bytes, or None if buffer is empty
        """
        if len(self._buffer) == 0:
            return None
        
        pop_size = min(size, len(self._buffer))
        data = bytes(self._buffer[:pop_size])
        self._buffer = self._buffer[pop_size:]
        return data
    
    def is_empty(self) -> bool:
        """Check if buffer is empty"""
        return len(self._buffer) == 0

