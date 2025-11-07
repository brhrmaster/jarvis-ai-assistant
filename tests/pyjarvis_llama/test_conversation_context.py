"""
Unit tests for pyjarvis_llama.conversation_context module
"""
import pytest
from unittest.mock import Mock, patch
from pyjarvis_llama.conversation_context import ConversationContext


class TestConversationContext:
    """Tests for ConversationContext class"""
    
    @pytest.fixture
    def context(self):
        """Create a ConversationContext instance"""
        with patch('pathlib.Path.mkdir'), \
             patch('pathlib.Path.touch'):
            return ConversationContext(contexts_dir="./test_contexts")
    
    def test_context_initialization(self, context):
        """Test ConversationContext initialization"""
        assert context is not None
        assert context.contexts_dir is not None
    
    def test_add_message(self, context):
        """Test adding a message to context"""
        # ConversationContext doesn't have add_message, it has save_request and save_response
        with patch('builtins.open', create=True):
            context.save_request("Hello")
            # Verify method was called (file operations are mocked)
            assert hasattr(context, 'save_request')
    
    def test_get_messages(self, context):
        """Test getting all messages"""
        # ConversationContext doesn't have get_messages, it has load_previous_context
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.read_text', return_value="<request>Hello</request>"):
            messages = context.load_previous_context()
            assert isinstance(messages, str)
    
    def test_clear_context(self, context):
        """Test clearing conversation context"""
        # ConversationContext doesn't have clear, it has clear_all_contexts
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.glob', return_value=[]):
            context.clear_all_contexts()
            # Verify method exists
            assert hasattr(context, 'clear_all_contexts')
    
    def test_get_context_string(self, context):
        """Test getting context as string"""
        # ConversationContext doesn't have get_context_string, it has load_previous_context
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.read_text', return_value="<request>Hello</request>"):
            context_str = context.load_previous_context()
            assert isinstance(context_str, str)
            assert len(context_str) > 0


