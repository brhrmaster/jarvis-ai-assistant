"""
Text analysis for context and emotion detection
"""

import asyncio
from typing import Optional
from loguru import logger
from pyjarvis_shared import Emotion, Language

# Try to import langdetect (lightweight and reliable)
try:
    from langdetect import detect, DetectorFactory
    # Set seed for consistent results
    DetectorFactory.seed = 0
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    logger.warning("langdetect not available, using heuristic language detection")


class TextAnalyzer:
    """Text analyzer for extracting context, emotion, and language"""
    
    def __init__(self):
        """Create a new text analyzer"""
        pass
    
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
        Detect language of the text using langdetect or heuristics
        
        Args:
            text: Text to analyze
            
        Returns:
            Detected language
        """
        # Use langdetect if available
        if LANGDETECT_AVAILABLE:
            try:
                # Run detection in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                detected_code = await loop.run_in_executor(
                    None,
                    lambda: detect(text)
                )
                
                logger.debug(f"Detected language code: {detected_code}")
                
                # Map language codes to our Language enum
                if detected_code in ["pt", "pt-BR", "pt-PT"]:
                    return Language.PORTUGUESE
                elif detected_code in ["es", "es-ES", "es-MX", "es-AR", "es-CO", "es-CL", "es-PE", "es-VE", "es-EC", "es-GT", "es-CU", "es-BO", "es-DO", "es-HN", "es-PY", "es-SV", "es-NI", "es-CR", "es-PA", "es-UY"]:
                    return Language.SPANISH
                elif detected_code in ["en", "en-US", "en-GB", "en-CA", "en-AU", "en-NZ", "en-IE", "en-ZA"]:
                    return Language.ENGLISH
                else:
                    # For unknown languages, try heuristic as fallback
                    logger.debug(f"Unknown language code '{detected_code}', trying heuristics")
                    return await self._detect_language_heuristic(text)
                    
            except Exception as e:
                logger.warning(f"Language detection failed: {e}, falling back to heuristics")
        
        # Fallback to heuristic detection
        return await self._detect_language_heuristic(text)
    
    async def _detect_language_heuristic(self, text: str) -> Language:
        """Heuristic-based language detection (fallback)"""
        text_lower = text.lower()
        
        # First check for Portuguese-specific character sequences (strong indicators)
        portuguese_char_indicators = ["ão", "ç", "ã", "õ", "ê", "ô", "â"]
        if any(char_seq in text for char_seq in portuguese_char_indicators):
            logger.debug("Portuguese-specific characters found, detected as Portuguese")
            return Language.PORTUGUESE
        
        # Spanish-specific character sequences (strong indicators)
        spanish_char_indicators = ["ñ", "¿", "¡"]
        if any(char_seq in text for char_seq in spanish_char_indicators):
            logger.debug("Spanish-specific characters found, detected as Spanish")
            return Language.SPANISH
        
        # Portuguese-specific words (more specific, less common in English/Spanish)
        portuguese_strong_indicators = [
            "não", "sim", "são", "está", "estão", "você", "vocês", "também",
            "muito", "mais", "menos", "como", "quando", "onde", "porque",
            "fazer", "dizer", "ter", "ser", "estar", "poder", "querer",
            "na", "no", "nas", "nos", "da", "do", "das", "dos"
        ]
        
        # Spanish-specific words (strong indicators)
        spanish_strong_indicators = [
            "gustaría", "gusta", "gustan", "estoy", "estás", "está", "estamos", "están",
            "tú", "usted", "ustedes", "también", "muy", "más", "menos", "cómo", 
            "cuándo", "dónde", "por qué", "porque", "hacer", "decir", "tener", 
            "ser", "estar", "poder", "querer", "necesito", "necesitas", "necesita",
            "en la", "en el", "de la", "del", "las", "los", "una", "un", "el", "la",
            "que", "con", "por", "para", "consejos", "viaje", "planeo", "hacer",
            "méxico", "méjico", "españa", "argentina", "colombia", "chile", "perú",
            "visitar", "recibir", "ayuda", "planes", "reservas", "recomendable",
            "ciudad", "ruinas", "paisaje", "natural", "interior", "condiciones",
            "seguridad", "salud", "documentos", "importantes", "mantenerse", "conectado"
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
        spanish_score = sum(2 for indicator in spanish_strong_indicators if indicator in text_lower)
        english_score = sum(2 for indicator in english_strong_indicators if indicator in text_lower)
        
        # Portuguese common words (lower weight)
        portuguese_common_words = [
            "que", "com", "por", "para", "uma", "um", "de", "em", "o", "a", "os", "as"
        ]
        
        # Spanish common words (lower weight)
        spanish_common_words = [
            "que", "con", "por", "para", "una", "un", "de", "en", "el", "la", "los", "las",
            "y", "o", "pero", "si", "no", "es", "son", "fue", "fueron"
        ]
        
        # Check for Portuguese common words only if text is short
        if len(text.split()) <= 10:  # For short texts, common words matter more
            portuguese_score += sum(1 for word in portuguese_common_words if word in text_lower)
            spanish_score += sum(1 for word in spanish_common_words if word in text_lower)
        else:
            # For longer texts, check if these appear as full words (not substrings)
            for word in portuguese_common_words:
                # Check as full word (with word boundaries)
                if f" {word} " in f" {text_lower} " or text_lower.startswith(f"{word} ") or text_lower.endswith(f" {word}"):
                    portuguese_score += 0.5
            
            for word in spanish_common_words:
                # Check as full word (with word boundaries)
                if f" {word} " in f" {text_lower} " or text_lower.startswith(f"{word} ") or text_lower.endswith(f" {word}"):
                    spanish_score += 0.5
        
        logger.debug(f"Language detection scores - Portuguese: {portuguese_score}, Spanish: {spanish_score}, English: {english_score}")
        
        # Decide based on scores (need stronger evidence for non-English languages)
        max_score = max(portuguese_score, spanish_score, english_score)
        
        if portuguese_score == max_score and portuguese_score >= 3:
            logger.debug(f"Detected as Portuguese (score: {portuguese_score})")
            return Language.PORTUGUESE
        elif spanish_score == max_score and spanish_score >= 2:
            logger.debug(f"Detected as Spanish (score: {spanish_score})")
            return Language.SPANISH
        elif english_score == max_score and english_score >= 2:
            logger.debug(f"Detected as English (score: {english_score})")
            return Language.ENGLISH
        else:
            # Default to English if scores are too close or too low
            logger.debug(f"Ambiguous detection, defaulting to English (PT: {portuguese_score}, ES: {spanish_score}, EN: {english_score})")
            return Language.ENGLISH
    
    async def extract_subject(self, text: str) -> Optional[str]:
        """
        Extract subject/topic from text
        TODO: Implement subject extraction using NLP
        """
        # Placeholder - return None for now
        return None

