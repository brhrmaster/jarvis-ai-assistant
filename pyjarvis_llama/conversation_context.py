"""
Conversation context manager for storing and loading conversation history
"""

import re
from pathlib import Path
from datetime import datetime
from typing import Optional
from loguru import logger


class ConversationContext:
    """Manages conversation context storage and retrieval"""
    
    def __init__(self, contexts_dir: str = "./contexts"):
        """
        Initialize conversation context manager
        
        Args:
            contexts_dir: Directory to store context files
        """
        self.contexts_dir = Path(contexts_dir)
        self.context_file: Optional[Path] = None
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize context directory and create current context file"""
        try:
            # Create contexts directory if it doesn't exist
            self.contexts_dir.mkdir(parents=True, exist_ok=True)
            
            # Create new context file with timestamp-based name
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            self.context_file = self.contexts_dir / f"context_{timestamp}.txt"
            
            # Create empty file
            self.context_file.touch()
            
            logger.info(f"[Context] Created new context file: {self.context_file.name}")
        except Exception as e:
            logger.error(f"[Context] Failed to initialize context: {e}")
            raise
    
    def save_request(self, request_text: str) -> None:
        """
        Save a request to the context file
        
        Args:
            request_text: The request/prompt text to save
        """
        if not self.context_file:
            logger.warning("[Context] No context file available")
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            
            with open(self.context_file, 'a', encoding='utf-8') as f:
                f.write("<request>\n")
                f.write(f"<time>{timestamp}</time>\n")
                f.write(f"{request_text}\n")
                f.write("</request>\n")
            
            logger.debug(f"[Context] Saved request at {timestamp}")
        except Exception as e:
            logger.error(f"[Context] Failed to save request: {e}")
    
    def clean_text(self, text: str) -> str:
        """
        Clean text by removing special characters and markdown formatting
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text without special characters
        """
        if not text:
            return text
        
        # Remove markdown formatting (but preserve content)
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Remove **bold** but keep content
        text = re.sub(r'\*([^*]+)\*', r'\1', text)      # Remove *italic* but keep content
        text = re.sub(r'_([^_]+)_', r'\1', text)        # Remove _underline_ but keep content
        text = re.sub(r'`([^`]+)`', r'\1', text)        # Remove `code` but keep content
        text = re.sub(r'#{1,6}\s+', '', text)            # Remove markdown headers
        text = re.sub(r'[1-9]\.\s+', '', text)            # Remove Numbering lists
        text = re.sub(r'- [^\n]+\n', '', text)            # Remove Unordered lists
        text = re.sub(r'> [^\n]+\n', '', text)            # Remove Blockquotes
        text = re.sub(r'\[[^\]]+\]\([^\)]+\)', '', text)            # Remove Links
        text = re.sub(r'!\[[^\]]+\]\([^\)]+\)', '', text)            # Remove Images
        text = re.sub(r'\[[^\]]+\]\([^\)]+\)', '', text)            # Remove Links
        
        # Replace special Unicode characters with ASCII equivalents
        text = text.replace('‑', '-')   # Replace en-dash (U+2011) with regular dash
        text = text.replace('—', '-')   # Replace em-dash (U+2014) with regular dash
        text = text.replace('–', '-')   # Replace en-dash (U+2013) with regular dash
        text = text.replace('"', '"')    # Replace left double quotation mark
        text = text.replace('"', '"')    # Replace right double quotation mark
        
        # Normalize whitespace: replace multiple spaces with single space (but preserve line breaks)
        lines = text.split('\n')
        cleaned_lines = [re.sub(r'\s+', ' ', line).strip() for line in lines]
        text = '\n'.join(cleaned_lines)
        
        # Clean up multiple consecutive line breaks (keep max 2)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def save_response(self, response_text: str) -> None:
        """
        Save a response to the context file
        
        Args:
            response_text: The response text to save
        """
        if not self.context_file:
            logger.warning("[Context] No context file available")
            return
        
        try:
            with open(self.context_file, 'a', encoding='utf-8') as f:
                f.write("<response>\n")
                f.write(f"{response_text}\n")
                f.write("</response>\n")
            
            logger.debug("[Context] Saved and cleaned response")
        except Exception as e:
            logger.error(f"[Context] Failed to save response: {e}")
    
    def load_previous_context(self) -> str:
        """
        Load previous context from the current context file
        
        Returns:
            Previous context as a formatted string, or empty string if no context exists
        """
        if not self.context_file or not self.context_file.exists():
            return ""
        
        try:
            content = self.context_file.read_text(encoding='utf-8').strip()
            if not content:
                return ""
            
            # Return the entire file content wrapped in <previous-context> tags
            return f"<previous-context>\n{content}\n</previous-context>"
        except Exception as e:
            logger.error(f"[Context] Failed to load previous context: {e}")
            return ""
    
    def clear_all_contexts(self) -> None:
        """Clear all context files in the contexts directory"""
        try:
            if self.contexts_dir.exists():
                # Remove all files in the directory
                for file_path in self.contexts_dir.glob("*.txt"):
                    try:
                        file_path.unlink()
                        logger.debug(f"[Context] Removed context file: {file_path.name}")
                    except Exception as e:
                        logger.warning(f"[Context] Failed to remove {file_path.name}: {e}")
                
                logger.info("[Context] Cleared all context files")
        except Exception as e:
            logger.error(f"[Context] Failed to clear contexts: {e}")

