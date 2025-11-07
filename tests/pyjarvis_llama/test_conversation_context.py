"""
Unit tests for pyjarvis_llama.conversation_context module
"""
import pytest
from unittest.mock import Mock
from pyjarvis_llama.conversation_context import ConversationContext


class TestConversationContext:
    """Tests for ConversationContext class"""
    
    @pytest.fixture
    def context(self):
        """Create a ConversationContext instance"""
        return ConversationContext()
    
    def test_context_initialization(self, context):
        """Test ConversationContext initialization"""
        assert context is not None
    
    def test_add_message(self, context):
        """Test adding a message to context"""
        context.add_message("user", "Hello")
        assert len(context.messages) > 0
    
    def test_get_messages(self, context):
        """Test getting all messages"""
        context.add_message("user", "Hello")
        context.add_message("assistant", "Hi there!")
        
        messages = context.get_messages()
        assert len(messages) == 2
    
    def test_clear_context(self, context):
        """Test clearing conversation context"""
        context.add_message("user", "Hello")
        context.clear()
        assert len(context.messages) == 0
    
    def test_get_context_string(self, context):
        """Test getting context as string"""
        context.add_message("user", "Hello")
        context_str = context.get_context_string()
        assert isinstance(context_str, str)
        assert len(context_str) > 0


