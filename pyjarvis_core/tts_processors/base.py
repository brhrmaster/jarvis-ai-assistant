"""
Base TTS Processor interface (Strategy Pattern)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from pathlib import Path
from pyjarvis_shared import Language


@dataclass
class TtsProcessorResult:
    """Result from TTS processing"""
    audio_file_path: Path
    sample_rate: int
    duration_seconds: Optional[float] = None
    language: Optional[Language] = None


class TtsProcessor(ABC):
    """Abstract base class for TTS processors (Strategy Pattern)"""
    
    def __init__(self, output_dir: Path):
        """
        Initialize TTS processor
        
        Args:
            output_dir: Directory to save generated audio files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the processor (load models, etc.)"""
        pass
    
    @abstractmethod
    async def synthesize(self, text: str, language: Language) -> TtsProcessorResult:
        """
        Generate speech from text and save to file
        
        Args:
            text: Text to synthesize
            language: Target language
            
        Returns:
            TtsProcessorResult with path to generated audio file
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Processor name/identifier"""
        pass
    
    @property
    def is_initialized(self) -> bool:
        """Check if processor is initialized"""
        return self._initialized
    
    def _get_output_path(self, text: str, language: Language) -> Path:
        """
        Generate output file path
        
        Args:
            text: Input text (for naming)
            language: Target language
            
        Returns:
            Path to output file
        """
        import hashlib
        import time
        
        # Create filename from text hash and timestamp
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()[:8]
        timestamp = int(time.time() * 1000)  # milliseconds
        lang_code = language.value.lower()[:2]
        filename = f"tts_{lang_code}_{text_hash}_{timestamp}.wav"
        
        return self.output_dir / filename

