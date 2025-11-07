"""
Unit tests for pyjarvis_llama.personas module
"""
import pytest
from unittest.mock import Mock
from pyjarvis_llama.personas import PersonaFactory, PersonaStrategy, JarvisPersona


class TestPersonaFactory:
    """Tests for PersonaFactory class"""
    
    def test_factory_creation(self):
        """Test PersonaFactory is a class with static methods"""
        # PersonaFactory is a class with static methods, not instantiable
        assert hasattr(PersonaFactory, 'create')
        assert hasattr(PersonaFactory, 'list_available')
    
    def test_get_persona(self):
        """Test getting a persona"""
        persona = PersonaFactory.create("jarvis")  # Use create instead of get_persona
        assert persona is not None
        assert persona.name == "jarvis"
    
    def test_get_unknown_persona(self):
        """Test getting an unknown persona returns default"""
        persona = PersonaFactory.create("unknown")  # Use create instead of get_persona
        assert persona is not None
        # Should default to jarvis
        assert persona.name == "jarvis"
    
    def test_list_personas(self):
        """Test listing available personas"""
        personas = PersonaFactory.list_available()  # Use list_available instead of list_personas
        assert isinstance(personas, list)
        assert len(personas) > 0
        assert "jarvis" in personas


class TestPersonaStrategy:
    """Tests for PersonaStrategy class"""
    
    def test_persona_strategy_creation(self):
        """Test PersonaStrategy initialization"""
        # PersonaStrategy is abstract, can't be instantiated directly
        # Use a concrete implementation instead
        strategy = JarvisPersona()  # Use concrete class instead of abstract base
        assert strategy.name == "jarvis"
        assert hasattr(strategy, 'persona')
        assert hasattr(strategy, 'context')
    
    def test_format_prompt(self):
        """Test formatting a prompt with persona"""
        strategy = JarvisPersona()  # Use concrete class
        formatted = strategy.build_prompt("Hello")  # Use build_prompt instead of format_prompt
        assert formatted is not None
        assert isinstance(formatted, str)
        assert "Hello" in formatted


