"""
Google Text-to-Speech (gTTS) processor implementation
"""

import asyncio
from pathlib import Path
from typing import Optional
from loguru import logger
from pyjarvis_shared import Language
from .base import TtsProcessor, TtsProcessorResult

try:
    from gtts import gTTS
    import os
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    logger.warning("gTTS not available. Install with: pip install gtts")


class GttsProcessor(TtsProcessor):
    """Google Text-to-Speech processor"""
    
    def __init__(self, output_dir: Path):
        """Initialize gTTS processor"""
        if not GTTS_AVAILABLE:
            raise RuntimeError("gTTS is not installed. Install with: pip install gtts")
        
        super().__init__(output_dir)
        self.sample_rate = 44100  # gTTS typically outputs at 22050, we'll resample if needed
    
    async def initialize(self) -> None:
        """Initialize the processor"""
        if self._initialized:
            return
        
        logger.info("[gTTS] Initializing Google Text-to-Speech processor...")
        # gTTS doesn't require pre-loading models, it's API-based
        self._initialized = True
        logger.info("[gTTS] Processor initialized successfully")
    
    async def synthesize(self, text: str, language: Language) -> TtsProcessorResult:
        """
        Generate speech using Google TTS
        
        Args:
            text: Text to synthesize
            language: Target language
            
        Returns:
            TtsProcessorResult with path to MP3 file
        """
        logger.info(f"[gTTS] Synthesizing text: '{text[:50]}...' (language: {language.value})")
        
        # Map Language enum to gTTS language codes
        lang_code = self._language_to_code(language)
        
        # Generate output path
        output_path = self._get_output_path(text, language)
        
        # Run gTTS in thread pool (it may block)
        loop = asyncio.get_event_loop()
        
        def generate_audio():
            """Generate audio file synchronously"""
            try:
                import tempfile
                import os
                
                # gTTS saves as MP3 by default, we need to convert to WAV
                # Save to temporary MP3 first
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_mp3:
                    tmp_mp3_path = tmp_mp3.name
                
                try:
                    # Generate MP3 using gTTS
                    tts = gTTS(text=text, lang=lang_code, slow=False)
                    tts.save(tmp_mp3_path)
                    
                    # Convert MP3 to WAV using pydub
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
                            raise RuntimeError(
                                "FFmpeg is not installed or not in PATH. "
                                "Install FFmpeg to convert MP3 to WAV. "
                                "See INSTALL_FFMPEG.md for instructions."
                            )
                        
                        # Perform conversion
                        audio = AudioSegment.from_mp3(tmp_mp3_path)
                        audio.export(str(output_path), format="wav")
                        logger.info(f"[gTTS] Audio file converted and saved as WAV: {output_path}")
                    except ImportError:
                        # If pydub not available, raise error
                        raise RuntimeError(
                            "pydub is required to convert MP3 to WAV. "
                            "Install with: pip install pydub. "
                            "Also ensure ffmpeg is installed for MP3 support."
                        )
                    except RuntimeError:
                        # Re-raise RuntimeErrors (ffmpeg check)
                        raise
                    except Exception as e:
                        # If conversion fails, provide helpful error
                        error_msg = str(e).lower()
                        if 'ffmpeg' in error_msg or 'ffprobe' in error_msg or 'avprobe' in error_msg:
                            raise RuntimeError(
                                "FFmpeg is not installed or not in PATH. "
                                "Install FFmpeg to convert MP3 to WAV. "
                                "See INSTALL_FFMPEG.md for instructions. "
                                f"Original error: {e}"
                            )
                        else:
                            logger.error(f"[gTTS] Failed to convert MP3 to WAV: {e}")
                            raise RuntimeError(
                                f"Failed to convert audio to WAV format: {e}"
                            )
                finally:
                    # Clean up temporary MP3 file
                    if os.path.exists(tmp_mp3_path):
                        try:
                            os.unlink(tmp_mp3_path)
                        except:
                            pass
                
                return output_path
            except Exception as e:
                logger.error(f"[gTTS] Failed to generate audio: {e}")
                raise
        
        await loop.run_in_executor(None, generate_audio)
        
        # Calculate duration (estimate based on text length)
        # Average speaking rate: ~150 words per minute
        word_count = len(text.split())
        duration_seconds = (word_count / 150.0) * 60.0
        
        logger.info(f"[gTTS] Generated audio file: {output_path} ({duration_seconds:.2f}s estimated)")
        
        return TtsProcessorResult(
            audio_file_path=output_path,
            sample_rate=self.sample_rate,
            duration_seconds=duration_seconds,
            language=language
        )
    
    def _language_to_code(self, language: Language) -> str:
        """Convert Language enum to gTTS language code"""
        mapping = {
            Language.ENGLISH: "en",
            Language.PORTUGUESE: "pt",
        }
        return mapping.get(language, "en")
    
    @property
    def name(self) -> str:
        """Processor name"""
        return "gTTS"

