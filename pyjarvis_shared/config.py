"""
Configuration structures
"""

from dataclasses import dataclass, field
from typing import Optional, Dict


@dataclass
class AudioConfig:
    """Audio configuration"""
    sample_rate: int = 44100
    channels: int = 1
    buffer_size: int = 4096
    format: str = "int16"


@dataclass
class AppConfig:
    """Application configuration"""
    pipe_name: str = r"\\.\pipe\pyjarvis"  # Legacy, kept for compatibility
    tcp_host: str = "127.0.0.1"
    tcp_port: int = 8888
    log_level: str = "INFO"
    audio_config: Optional[AudioConfig] = None
    # TTS Configuration
    tts_processor: str = "edge-tts"  # TTS processor to use (gtts, coqui, pyttsx3, etc.)
    audio_output_dir: str = "./audio"  # Directory for generated audio files
    audio_delete_after_playback: bool = True  # Delete audio files after playback
    
    # Ollama LLM Configuration
    ollama_base_url: str = "http://localhost:11434"  # Ollama server URL
    ollama_model: str = "llama3.1:latest" # gpt-oss:20b, llama3.2  Ollama model to use
    ollama_persona: str = "portuguese"  # AI persona to use (jarvis, friendly, professional, portuguese)
    
    # Speech-to-Text (STT) Configuration
    stt_model: str = "base"  # Whisper model to use (base, small, medium, large)
    stt_language: str = "pt"  # Default language for speech-to-text (en, pt, etc.)
    
    # Edge-TTS Configuration
    edge_tts_voices: Dict[str, str] = field(default_factory=lambda: {
        "pt-br": "pt-BR-LeilaNeural",
        "pt": "pt-BR-LeilaNeural",
        "en": "en-US-AnaNeural",
        "en-us": "en-US-AnaNeural",
        "es": "es-ES-ElviraNeural",
        "es-es": "es-ES-ElviraNeural",
        "es-mx": "es-MX-DaliaNeural",
        "es-ar": "es-AR-ElenaNeural",
        "es-co": "es-CO-SalomeNeural"
    })  # Voice mapping by language code
    # for a complete list of voices, execute the following command:
    # edge-tts --list-voices
    
    def __post_init__(self):
        if self.audio_config is None:
            self.audio_config = AudioConfig()

