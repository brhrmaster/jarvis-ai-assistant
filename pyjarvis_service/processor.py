"""
Text processing orchestration
"""

from pathlib import Path
from loguru import logger
from pyjarvis_shared import (
    TextToVoiceRequest,
    VoiceProcessingUpdate,
    ProcessingStatus,
    Language,
    AppConfig,
)
from pyjarvis_core import TextAnalyzer
from pyjarvis_core.tts_factory import TtsProcessorFactory


class TextProcessor:
    """Text processor that orchestrates text analysis and TTS generation"""
    
    def __init__(self, config: AppConfig = None):
        """Create a new text processor"""
        self.config = config or AppConfig()
        self.text_analyzer = TextAnalyzer()
        
        # Create TTS processor using factory
        output_dir = Path(self.config.audio_output_dir).resolve()
        self.tts_processor = TtsProcessorFactory.create(self.config, output_dir)
    
    async def initialize(self) -> None:
        """Initialize the processor and TTS engine"""
        logger.info("Initializing text processor")
        logger.debug("Initializing TTS processor...")
        await self.tts_processor.initialize()
        logger.debug("TTS processor initialized")
        logger.debug("Text processor initialized successfully")
    
    async def process(self, request: TextToVoiceRequest) -> VoiceProcessingUpdate:
        """
        Process text to voice
        
        Args:
            request: Text processing request
            
        Returns:
            Voice processing update with audio data
        """
        logger.info("[PIPELINE] Starting text processing pipeline")
        logger.info(f"[PIPELINE] Input text: '{request.text}'")
        logger.debug(f"[PIPELINE] Request language: {request.language}")
        
        # Step 1: Analyze text
        logger.debug("[PIPELINE] Step 1: Analyzing text...")
        emotion = await self.text_analyzer.detect_emotion(request.text)
        logger.debug(f"[PIPELINE] Detected emotion: {emotion}")
        
        # Detect or use provided language
        if request.language:
            lang_code = request.language.lower()
            if lang_code in ["pt-br", "pt", "portuguese"]:
                language = Language.PORTUGUESE
            elif lang_code in ["es", "es-es", "es-mx", "espanol", "spanish", "español"]:
                language = Language.SPANISH
            elif lang_code in ["en", "en-us", "en-gb", "english"]:
                language = Language.ENGLISH
            else:
                # If language code is provided but not recognized, try to detect from text
                logger.warning(f"[PIPELINE] Unknown language code '{lang_code}', detecting from text")
                language = await self.text_analyzer.detect_language(request.text)
        else:
            language = await self.text_analyzer.detect_language(request.text)
        
        logger.info(f"[PIPELINE] Detected language: {language.value}")
        
        subject = await self.text_analyzer.extract_subject(request.text)
        logger.debug(f"[PIPELINE] Extracted subject: {subject}")
        
        # Step 2: Generate speech
        logger.debug("[PIPELINE] Step 2: Generating speech...")
        logger.info(f"[PIPELINE] Generating speech for language: {language}")
        
        # Generate audio file using TTS processor
        result = await self.tts_processor.synthesize(request.text, language)
        logger.info(f"[PIPELINE] Generated audio file: {result.audio_file_path}")
        
        logger.info("[PIPELINE] Text processing complete")
        
        # Return update with file path (not bytes)
        return VoiceProcessingUpdate(
            status=ProcessingStatus.READY,
            audio_file_path=str(result.audio_file_path),
            emotion=emotion,
            subject=subject,
        )

