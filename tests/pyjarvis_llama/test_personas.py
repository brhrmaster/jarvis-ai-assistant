"""
Unit tests for pyjarvis_llama.personas module
"""
import pytest
from unittest.mock import Mock
from pyjarvis_llama.personas import PersonaFactory, PersonaStrategy


class TestPersonaFactory:
    """Tests for PersonaFactory class"""
    
    def test_factory_creation(self):
        """Test PersonaFactory initialization"""
        factory = PersonaFactory()
        assert factory is not None
    
    def test_get_persona(self):
        """Test getting a persona"""
        factory = PersonaFactory()
        persona = factory.get_persona("jarvis")
        assert persona is not None
    
    def test_get_unknown_persona(self):
        """Test getting an unknown persona returns default"""
        factory = PersonaFactory()
        persona = factory.get_persona("unknown")
        assert persona is not None
    
    def test_list_personas(self):
        """Test listing available personas"""
        factory = PersonaFactory()
        personas = factory.list_personas()
        assert isinstance(personas, list)
        assert len(personas) > 0


class TestPersonaStrategy:
    """Tests for PersonaStrategy class"""
    
    def test_persona_strategy_creation(self):
        """Test PersonaStrategy initialization"""
        strategy = PersonaStrategy(name="test", system_prompt="Test prompt")
        assert strategy.name == "test"
        assert strategy.system_prompt == "Test prompt"
    
    def test_format_prompt(self):
        """Test formatting a prompt with persona"""
        strategy = PersonaStrategy(name="test", system_prompt="You are a test assistant.")
        formatted = strategy.format_prompt("Hello")
        assert formatted is not None
        assert isinstance(formatted, str)


