"""
TTS Processor Factory (Factory Pattern)
"""

from pathlib import Path
from typing import Optional
from loguru import logger
from pyjarvis_shared import AppConfig
from .tts_processors.base import TtsProcessor
from .tts_processors.gtts_processor import GttsProcessor
from .tts_processors.edge_tts_processor import EdgeTtsProcessor


class TtsProcessorFactory:
    """Factory for creating TTS processors"""
    
    # Registry of available processors
    _processors = {
        "gtts": GttsProcessor,
        "edge-tts": EdgeTtsProcessor,
        "edgetts": EdgeTtsProcessor,  # Alias
        # Add more processors here as they are implemented
        # "coqui": CoquiProcessor,
        # "pyttsx3": Pyttsx3Processor,
    }
    
    @classmethod
    def create(cls, config: AppConfig, output_dir: Optional[Path] = None) -> TtsProcessor:
        """
        Create a TTS processor based on configuration
        
        Args:
            config: Application configuration
            output_dir: Optional output directory (defaults to ./audio)
            
        Returns:
            TTS processor instance
        """
        # Get processor type from config (default to gTTS)
        processor_type = getattr(config, 'tts_processor', 'gtts')
        processor_type = processor_type.lower()
        
        if processor_type not in cls._processors:
            logger.warning(f"Unknown processor type '{processor_type}', falling back to 'gtts'")
            processor_type = 'gtts'
        
        # Determine output directory
        if output_dir is None:
            output_dir = Path("./audio").resolve()
        
        # Get processor class
        processor_class = cls._processors[processor_type]
        
        logger.info(f"Creating TTS processor: {processor_type}")
        
        try:
            # Pass config to processor if it supports it (for voice configuration, etc.)
            if processor_type in ["edge-tts", "edgetts"]:
                processor = processor_class(output_dir, config=config)
            else:
                processor = processor_class(output_dir)
            logger.info(f"TTS processor '{processor_type}' created successfully")
            return processor
        except Exception as e:
            logger.error(f"Failed to create processor '{processor_type}': {e}")
            raise RuntimeError(f"Failed to create TTS processor: {e}")
    
    @classmethod
    def list_available(cls) -> list[str]:
        """List available processor types"""
        return list(cls._processors.keys())
    
    @classmethod
    def register(cls, name: str, processor_class: type[TtsProcessor]) -> None:
        """Register a new processor type"""
        cls._processors[name.lower()] = processor_class
        logger.info(f"Registered TTS processor: {name}")

