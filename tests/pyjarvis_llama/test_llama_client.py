"""
Unit tests for pyjarvis_llama.llama_client module
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from pyjarvis_llama.llama_client import OllamaClient
from pyjarvis_shared import AppConfig


class TestOllamaClient:
    """Tests for OllamaClient class"""
    
    @pytest.fixture
    def client(self, app_config):
        """Create an OllamaClient instance"""
        return OllamaClient(app_config)
    
    def test_client_initialization(self, client, app_config):
        """Test OllamaClient initialization"""
        assert client.config == app_config
    
    @pytest.mark.asyncio
    async def test_generate_response(self, client):
        """Test generating a response"""
        prompt = "Hello, how are you?"
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value={"response": "I'm doing well!"})
            mock_response.__aenter__.return_value = mock_response
            mock_post.return_value = mock_response
            
            result = await client.generate(prompt)
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_generate_with_context(self, client):
        """Test generating with conversation context"""
        prompt = "What did I say before?"
        context = ["Previous message"]
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value={"response": "You said..."})
            mock_response.__aenter__.return_value = mock_response
            mock_post.return_value = mock_response
            
            result = await client.generate(prompt, context=context)
            assert result is not None
    
    def test_build_prompt(self, client):
        """Test building prompt with persona"""
        prompt = client._build_prompt("Hello", persona="jarvis")
        assert prompt is not None
        assert isinstance(prompt, str)


