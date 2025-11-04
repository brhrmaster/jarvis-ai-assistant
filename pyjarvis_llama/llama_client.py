"""
Ollama LLM client for generating responses
"""

import aiohttp
import json
from typing import Optional, Dict, Any
from loguru import logger
from pyjarvis_shared import AppConfig


class OllamaClient:
    """Client for interacting with Ollama LLM server"""
    
    def __init__(self, config: Optional[AppConfig] = None):
        """
        Initialize Ollama client
        
        Args:
            config: Application configuration (optional)
        """
        self.config = config or AppConfig()
        self.base_url = getattr(self.config, 'ollama_base_url', 'http://localhost:11434')
        self.model = getattr(self.config, 'ollama_model', 'llama3.2')
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _ensure_session(self) -> None:
        """Ensure HTTP session is created"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
    
    async def close(self) -> None:
        """Close HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def generate(self, prompt: str, stream: bool = False) -> str:
        """
        Generate text response from Ollama
        
        Args:
            prompt: Input prompt
            stream: Whether to stream the response (not implemented yet)
            
        Returns:
            Generated text response
        """
        await self._ensure_session()
        
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream
        }
        
        logger.debug(f"[Ollama] Sending request to {url} with model {self.model}")
        logger.debug(f"[Ollama] Prompt: {prompt[:100]}...")
        
        try:
            async with self._session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Ollama API error {response.status}: {error_text}")
                
                data = await response.json()
                
                if "response" in data:
                    response_text = data["response"]
                    #logger.info(f"[Ollama] Generated response ({len(response_text)} chars)")
                    return response_text
                else:
                    raise RuntimeError(f"Unexpected response format: {data}")
                    
        except aiohttp.ClientError as e:
            logger.error(f"[Ollama] Connection error: {e}")
            raise RuntimeError(f"Failed to connect to Ollama server at {self.base_url}. "
                             f"Is Ollama running? Error: {e}")
        except Exception as e:
            logger.error(f"[Ollama] Error generating response: {e}")
            raise
    
    async def test_connection(self) -> bool:
        """
        Test connection to Ollama server
        
        Returns:
            True if connection successful, False otherwise
        """
        await self._ensure_session()
        
        url = f"{self.base_url}/api/tags"
        
        try:
            async with self._session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get("models", [])
                    logger.info(f"[Ollama] Connected! Available models: {[m.get('name', '?') for m in models]}")
                    
                    # Check if requested model is available
                    model_names = [m.get('name', '') for m in models]
                    if self.model not in model_names:
                        logger.warning(f"[Ollama] Model '{self.model}' not found. Available: {model_names}")
                        if model_names:
                            logger.info(f"[Ollama] Using first available model: {model_names[0]}")
                            self.model = model_names[0]
                    
                    return True
                else:
                    logger.error(f"[Ollama] Connection test failed with status {response.status}")
                    return False
        except Exception as e:
            logger.error(f"[Ollama] Connection test failed: {e}")
            return False

