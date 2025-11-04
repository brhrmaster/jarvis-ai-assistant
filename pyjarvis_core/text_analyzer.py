"""
Text analysis for context and emotion detection
"""

import asyncio
from typing import Optional
from loguru import logger
from pyjarvis_shared import Emotion, Language

# Try to import transformers
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("transformers not available, using heuristic language detection")


class TextAnalyzer:
    """Text analyzer for extracting context, emotion, and language"""
    
    def __init__(self):
        """Create a new text analyzer"""
        self._language_pipeline = None
        self._initialized = False
    
    async def _initialize_language_detection(self):
        """Initialize language detection model asynchronously"""
        if self._initialized:
            return
        
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("Transformers library not available, using heuristic detection")
            self._initialized = True
            return
        
        try:
            logger.info("Loading language detection model...")
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self._language_pipeline = await loop.run_in_executor(
                None,
                lambda: pipeline(
                    "text-classification",
                    model="onnx-community/language_detection-ONNX",
                )
            )
            logger.info("Language detection model loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load language detection model: {e}, using heuristic detection")
            self._language_pipeline = None
        
        self._initialized = True
    
    async def detect_emotion(self, text: str) -> Emotion:
        """
        Analyze text to extract emotion
        TODO: Implement emotion detection using ML model or heuristic rules
        """
        text_lower = text.lower()
        
        if "?" in text_lower:
            return Emotion.QUESTIONING
        elif any(word in text_lower for word in ["happy", "great", "excellent", "wonderful"]):
            return Emotion.HAPPY
        elif any(word in text_lower for word in ["sad", "sorry", "unhappy", "disappointed"]):
            return Emotion.SAD
        elif "!" in text_lower or "excited" in text_lower:
            return Emotion.EXCITED
        elif any(word in text_lower for word in ["calm", "peace", "relax", "quiet"]):
            return Emotion.CALM
        else:
            return Emotion.NEUTRAL
    
    async def detect_language(self, text: str) -> Language:
        """
        Detect language of the text using ML model or heuristics
        
        Args:
            text: Text to analyze
            
        Returns:
            Detected language
        """
        # Initialize model if needed
        await self._initialize_language_detection()
        
        # Use ML model if available
        if self._language_pipeline:
            try:
                # Run inference in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: self._language_pipeline(text)
                )
                
                # Handle both single result and list of results
                if isinstance(result, list) and len(result) > 0:
                    result = result[0]
                
                # Extract language label
                if isinstance(result, dict):
                    language_label = result.get("label", "").lower()
                    confidence = result.get("score", 0)
                    logger.debug(f"Detected language: {language_label} (confidence: {confidence:.3f})")
                    
                    # Map common language labels to our Language enum
                    if "pt" in language_label or "portuguese" in language_label or "português" in language_label:
                        return Language.PORTUGUESE
                    elif "en" in language_label or "english" in language_label or "inglês" in language_label:
                        return Language.ENGLISH
                    else:
                        # Default to Portuguese if it's a Romance language or unknown
                        if any(c in language_label for c in ["es", "fr", "it", "ro"]):  # Spanish, French, Italian, Romanian
                            logger.debug("Romance language detected, defaulting to Portuguese")
                            return Language.PORTUGUESE
                        # Default to English for other languages
                        logger.debug(f"Unknown language '{language_label}', defaulting to English")
                        return Language.ENGLISH
                        
            except Exception as e:
                logger.warning(f"Language detection model failed: {e}, falling back to heuristics")
        
        # Fallback to heuristic detection
        return await self._detect_language_heuristic(text)
    
    async def _detect_language_heuristic(self, text: str) -> Language:
        """Heuristic-based language detection (fallback)"""
        text_lower = text.lower()
        
        # First check for Portuguese-specific character sequences (strong indicators)
        portuguese_char_indicators = ["ão", "ç", "ã", "õ", "ê", "ô", "â", "ú", "í", "á", "ó", "é"]
        if any(char_seq in text for char_seq in portuguese_char_indicators):
            logger.debug("Portuguese-specific characters found, detected as Portuguese")
            return Language.PORTUGUESE
        
        # Portuguese-specific words (more specific, less common in English)
        portuguese_strong_indicators = [
            "não", "sim", "são", "está", "estão", "você", "vocês", "também",
            "muito", "mais", "menos", "como", "quando", "onde", "porque",
            "fazer", "dizer", "ter", "ser", "estar", "poder", "querer",
            "na", "no", "nas", "nos", "da", "do", "das", "dos"
        ]
        
        # English-specific words (to balance detection)
        english_strong_indicators = [
            "the", "is", "are", "was", "were", "this", "that", "these", "those",
            "have", "has", "had", "will", "would", "could", "should", "can",
            "and", "but", "or", "not", "with", "from", "about", "into", "onto",
            "you", "your", "they", "their", "them", "what", "when", "where", "why", "how"
        ]
        
        # Count indicators
        portuguese_score = sum(2 for indicator in portuguese_strong_indicators if indicator in text_lower)
        english_score = sum(2 for indicator in english_strong_indicators if indicator in text_lower)
        
        # Portuguese common words (lower weight)
        portuguese_common_words = [
            "que", "com", "por", "para", "uma", "um", "de", "em", "o", "a", "os", "as"
        ]
        
        # Check for Portuguese common words only if text is short
        if len(text.split()) <= 10:  # For short texts, common words matter more
            portuguese_score += sum(1 for word in portuguese_common_words if word in text_lower)
        else:
            # For longer texts, check if these appear as full words (not substrings)
            for word in portuguese_common_words:
                # Check as full word (with word boundaries)
                if f" {word} " in f" {text_lower} " or text_lower.startswith(f"{word} ") or text_lower.endswith(f" {word}"):
                    portuguese_score += 0.5
        
        logger.debug(f"Language detection scores - Portuguese: {portuguese_score}, English: {english_score}")
        
        # Decide based on scores (need stronger evidence for Portuguese since English is default)
        if portuguese_score > english_score and portuguese_score >= 3:
            logger.debug(f"Detected as Portuguese (score: {portuguese_score} vs {english_score})")
            return Language.PORTUGUESE
        elif english_score > portuguese_score and english_score >= 2:
            logger.debug(f"Detected as English (score: {english_score} vs {portuguese_score})")
            return Language.ENGLISH
        else:
            # Default to English if scores are too close or too low
            logger.debug(f"Ambiguous detection, defaulting to English (PT: {portuguese_score}, EN: {english_score})")
            return Language.ENGLISH
    
    async def extract_subject(self, text: str) -> Optional[str]:
        """
        Extract subject/topic from text
        TODO: Implement subject extraction using NLP
        """
        # Placeholder - return None for now
        return None

