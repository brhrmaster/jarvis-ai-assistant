"""
Microsoft Edge TTS processor implementation
Uses edge-tts library for high-quality TTS with multiple voices
"""

import asyncio
from pathlib import Path
from typing import Optional, Dict
from loguru import logger
from pyjarvis_shared import Language
from .base import TtsProcessor, TtsProcessorResult

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    logger.warning("edge-tts not available. Install with: pip install edge-tts")


class EdgeTtsProcessor(TtsProcessor):
    """Microsoft Edge TTS processor"""
    
    # Default voice mapping by language (fallback if not in config)
    DEFAULT_VOICE_MAPPING = {
        Language.ENGLISH: "en-US-AriaNeural",  # Default English voice
        Language.PORTUGUESE: "pt-BR-FranciscaNeural",  # Default Portuguese voice
    }
    
    def __init__(self, output_dir: Path, config=None):
        """
        Initialize Edge TTS processor
        
        Args:
            output_dir: Directory to save audio files
            config: Optional AppConfig with voice preferences
        """
        if not EDGE_TTS_AVAILABLE:
            raise RuntimeError("edge-tts is not installed. Install with: pip install edge-tts")
        
        super().__init__(output_dir)
        self.sample_rate = 44100  # Edge TTS typically outputs at 24kHz, we'll resample if needed
        self.config = config
        self.voice_mapping = self._build_voice_mapping()
    
    def _build_voice_mapping(self) -> Dict[Language, str]:
        """
        Build voice mapping from config or use defaults
        
        Returns:
            Dictionary mapping Language to voice name
        """
        mapping = {}
        
        # Get voice config from AppConfig if available
        if self.config:
            config_voices = getattr(self.config, 'edge_tts_voices', None)
            if config_voices and isinstance(config_voices, dict):
                # Map config keys to Language enum
                for lang_code, voice_name in config_voices.items():
                    lang_code_lower = lang_code.lower()
                    if lang_code_lower in ["pt-br", "pt", "portuguese"]:
                        mapping[Language.PORTUGUESE] = voice_name
                    elif lang_code_lower in ["en", "en-us", "english"]:
                        mapping[Language.ENGLISH] = voice_name
        
        # Fill in defaults for missing languages
        for lang in [Language.ENGLISH, Language.PORTUGUESE]:
            if lang not in mapping:
                mapping[lang] = self.DEFAULT_VOICE_MAPPING[lang]
        
        logger.debug(f"[Edge-TTS] Voice mapping: {mapping}")
        return mapping
    
    async def initialize(self) -> None:
        """Initialize the processor"""
        if self._initialized:
            return
        
        logger.info("[Edge-TTS] Initializing Microsoft Edge TTS processor...")
        
        # Test if edge_tts is working
        try:
            # Get available voices as a test
            voices = await edge_tts.list_voices()
            logger.debug(f"[Edge-TTS] Found {len(voices)} available voices")
            
            # Validate configured voices and update if needed
            for lang in [Language.ENGLISH, Language.PORTUGUESE]:
                lang_voices = [v for v in voices if lang.value.lower() in v.get("Locale", "").lower()]
                if lang_voices:
                    configured_voice = self.voice_mapping.get(lang)
                    
                    # Check if configured voice exists
                    voice_exists = any(v.get("Name") == configured_voice for v in lang_voices)
                    
                    if not voice_exists:
                        # Use first available voice for the language
                        self.voice_mapping[lang] = lang_voices[0]["Name"]
                        logger.warning(f"[Edge-TTS] Configured voice '{configured_voice}' not found for {lang.value}. "
                                     f"Using: {self.voice_mapping[lang]}")
                    else:
                        logger.info(f"[Edge-TTS] Using configured voice for {lang.value}: {self.voice_mapping[lang]}")
                    
                    logger.debug(f"[Edge-TTS] Available {lang.value} voices: {len(lang_voices)}")
            
        except Exception as e:
            logger.warning(f"[Edge-TTS] Failed to list voices: {e}")
        
        self._initialized = True
        logger.info("[Edge-TTS] Processor initialized successfully")
    
    async def synthesize(self, text: str, language: Language) -> TtsProcessorResult:
        """
        Generate speech using Edge TTS
        
        Args:
            text: Text to synthesize
            language: Target language
            
        Returns:
            TtsProcessorResult with path to audio file
        """
        logger.info(f"[Edge-TTS] Synthesizing text: '{text[:50]}...' (language: {language.value})")
        
        # Get voice for language
        voice = self.voice_mapping.get(language, self.voice_mapping.get(Language.ENGLISH, self.DEFAULT_VOICE_MAPPING[Language.ENGLISH]))
        logger.debug(f"[Edge-TTS] Using voice: {voice}")
        
        # Generate output path
        output_path = self._get_output_path(text, language)
        
        # Generate audio using Edge TTS
        try:
            # Edge TTS communicate function generates audio
            # Edge TTS saves files based on extension in the path
            # We'll save as MP3 first, then convert to WAV if needed
            communicate = edge_tts.Communicate(text, voice)
            
            # Edge TTS saves as MP3 by default when saving to file
            # We'll save as MP3 and convert to WAV using pydub (like gTTS)
            import tempfile
            import os
            
            # Save to temporary MP3 file first
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_mp3:
                tmp_mp3_path = tmp_mp3.name
            
            try:
                # Save MP3 using Edge TTS
                await communicate.save(tmp_mp3_path)
                
                # Convert MP3 to WAV using pydub (if available)
                try:
                    from pydub import AudioSegment
                    
                    # Check if ffmpeg is available
                    try:
                        import subprocess
                        subprocess.run(['ffmpeg', '-version'], 
                                     stdout=subprocess.DEVNULL, 
                                     stderr=subprocess.DEVNULL,
                                     timeout=2)
                    except (FileNotFoundError, subprocess.TimeoutExpired):
                        # If ffmpeg not available, use MP3 directly (audio_player supports MP3)
                        output_path_final = output_path.with_suffix('.mp3')
                        import shutil
                        shutil.move(tmp_mp3_path, str(output_path_final))
                        logger.info(f"[Edge-TTS] Audio file saved as MP3: {output_path_final} (ffmpeg not available for WAV conversion)")
                        output_path_wav = output_path_final
                    else:
                        # Convert to WAV
                        output_path_wav = output_path.with_suffix('.wav')
                        audio = AudioSegment.from_mp3(tmp_mp3_path)
                        audio.export(str(output_path_wav), format="wav")
                        logger.info(f"[Edge-TTS] Audio file converted and saved as WAV: {output_path_wav}")
                except ImportError:
                    # If pydub not available, use MP3 directly
                    output_path_final = output_path.with_suffix('.mp3')
                    import shutil
                    shutil.move(tmp_mp3_path, str(output_path_final))
                    logger.warning(f"[Edge-TTS] pydub not available, saved as MP3: {output_path_final}")
                    output_path_wav = output_path_final
            finally:
                # Clean up temporary MP3 file
                if os.path.exists(tmp_mp3_path):
                    try:
                        os.unlink(tmp_mp3_path)
                    except:
                        pass
            
            # Calculate duration (estimate based on text length)
            # Edge TTS speaking rate is typically ~150 words per minute
            word_count = len(text.split())
            duration_seconds = (word_count / 150.0) * 60.0
            
            logger.info(f"[Edge-TTS] Generated audio file: {output_path_wav} ({duration_seconds:.2f}s estimated)")
            
            return TtsProcessorResult(
                audio_file_path=output_path_wav,
                sample_rate=self.sample_rate,
                duration_seconds=duration_seconds,
                language=language
            )
            
        except Exception as e:
            logger.error(f"[Edge-TTS] Failed to generate audio: {e}")
            raise RuntimeError(f"Edge TTS synthesis failed: {e}")
    
    @property
    def name(self) -> str:
        """Processor name"""
        return "edge-tts"
    
    @staticmethod
    async def list_available_voices(language: Optional[Language] = None) -> list[dict]:
        """
        List available voices (helper method)
        
        Args:
            language: Optional language filter
            
        Returns:
            List of voice dictionaries
        """
        if not EDGE_TTS_AVAILABLE:
            return []
        
        voices = await edge_tts.list_voices()
        
        if language:
            lang_filter = language.value.lower()
            if language == Language.PORTUGUESE:
                lang_filter = "pt"
            elif language == Language.ENGLISH:
                lang_filter = "en"
            
            voices = [v for v in voices if lang_filter in v.get("Locale", "").lower()]
        
        return voices

