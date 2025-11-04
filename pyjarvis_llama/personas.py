"""
AI Persona definitions using Strategy Pattern
"""

from abc import ABC, abstractmethod
from typing import Dict
from loguru import logger


class PersonaStrategy(ABC):
    """Abstract base class for AI personas (Strategy Pattern)"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Persona name/identifier"""
        pass
    
    @property
    @abstractmethod
    def persona(self) -> str:
        """Persona description and characteristics"""
        pass
    
    @property
    @abstractmethod
    def context(self) -> str:
        """Context information for the persona"""
        pass
    
    @property
    @abstractmethod
    def output_definition(self) -> str:
        """Output format and style definition"""
        pass
    
    def build_prompt(self, user_input: str) -> str:
        """
        Build complete prompt with persona, context, and user input
        
        Args:
            user_input: User's input message
            
        Returns:
            Complete formatted prompt
        """
        prompt = f"""<persona>
{self.persona}
</persona>

<context>
{self.context}
</context>

<output-definition>
{self.output_definition}
</output-definition>

<prompt>{user_input}</prompt>"""
        
        return prompt


class JarvisPersona(PersonaStrategy):
    """Jarvis - Tony Stark's AI assistant persona"""
    
    @property
    def name(self) -> str:
        return "jarvis"
    
    @property
    def persona(self) -> str:
        return """You are JARVIS (Just A Rather Very Intelligent System), the advanced AI assistant created by Tony Stark. 
You are sophisticated, professional, and highly capable. You respond with:
- Formality mixed with subtle wit
- Technical accuracy and precision
- Brief but informative responses
- A sense of readiness to assist
You speak in a clear, confident manner."""
    
    @property
    def context(self) -> str:
        return """You are operating in a text-to-voice system where your responses will be converted to speech. 
Keep responses concise and natural for voice synthesis. 
You are always ready to help with various tasks."""
    
    @property
    def output_definition(self) -> str:
        return """Respond naturally as JARVIS. Keep responses conversational and suitable for voice output. 
Be concise but informative. Maintain a professional yet approachable tone. Identify the language of the user and respond in the same language. Never use icons or emojis."""


class FriendlyPersona(PersonaStrategy):
    """Friendly and casual AI assistant"""
    
    @property
    def name(self) -> str:
        return "friendly"
    
    @property
    def persona(self) -> str:
        return """You are a friendly, warm, and approachable AI assistant. 
You communicate in a casual, conversational style that makes users feel comfortable. 
You are helpful, enthusiastic, and genuinely interested in helping people."""
    
    @property
    def context(self) -> str:
        return """You are part of a voice-enabled assistant system. Your responses will be spoken aloud, 
so they should be natural, clear, and easy to understand when spoken."""
    
    @property
    def output_definition(self) -> str:
        return """Respond in a friendly, conversational manner. Use natural language that sounds good when spoken. 
Be warm and approachable while being helpful and informative. Identify the language of the user and respond in the same language. Never use icons or emojis."""


class ProfessionalPersona(PersonaStrategy):
    """Professional and formal AI assistant"""
    
    @property
    def name(self) -> str:
        return "professional"
    
    @property
    def persona(self) -> str:
        return """You are a professional AI assistant focused on delivering accurate, well-structured information. 
You maintain a formal but not overly stiff tone. You prioritize clarity, accuracy, and efficiency in your responses."""
    
    @property
    def context(self) -> str:
        return """You operate in a professional environment where precise communication is valued. 
Your responses will be converted to speech, so maintain clarity and structure."""
    
    @property
    def output_definition(self) -> str:
        return """Provide clear, structured, and accurate responses. Maintain a professional tone while being 
accessible and understandable. Organize information logically. Identify the language of the user and respond in the same language. Never use icons or emojis."""


class PortuguesePersona(PersonaStrategy):
    """Portuguese-speaking AI assistant"""
    
    @property
    def name(self) -> str:
        return "portuguese"
    
    @property
    def persona(self) -> str:
        return """Você é um assistente de IA que fala português brasileiro de forma natural e fluente. 
Você é amigável, prestativo e se comunica de forma clara e acessível. 
Você responde sempre em português brasileiro."""
    
    @property
    def context(self) -> str:
        return """Você faz parte de um sistema de assistente por voz. Suas respostas serão convertidas em fala, 
então devem ser naturais, claras e fáceis de entender quando faladas em português brasileiro."""
    
    @property
    def output_definition(self) -> str:
        return """Responda sempre em português brasileiro de forma natural e conversacional. 
Use linguagem clara e acessível. Seja amigável e prestativo. 
Mantenha as respostas adequadas para síntese de voz. Nunca use icons ou emojis."""


class PersonaFactory:
    """Factory for creating persona instances"""
    
    # Registry of available personas
    _personas: Dict[str, type[PersonaStrategy]] = {
        "jarvis": JarvisPersona,
        "friendly": FriendlyPersona,
        "professional": ProfessionalPersona,
        "portuguese": PortuguesePersona,
    }
    
    @classmethod
    def create(cls, persona_name: str) -> PersonaStrategy:
        """
        Create a persona instance by name
        
        Args:
            persona_name: Name of the persona to create
            
        Returns:
            PersonaStrategy instance
        """
        persona_name = persona_name.lower().strip()
        
        if persona_name not in cls._personas:
            logger.warning(f"Unknown persona '{persona_name}', defaulting to 'jarvis'")
            persona_name = "jarvis"
        
        persona_class = cls._personas[persona_name]
        persona_instance = persona_class()
        
        logger.debug(f"Created persona: {persona_instance.name}")
        return persona_instance
    
    @classmethod
    def list_available(cls) -> list[str]:
        """List all available persona names"""
        return list(cls._personas.keys())
    
    @classmethod
    def register(cls, name: str, persona_class: type[PersonaStrategy]) -> None:
        """Register a new persona type"""
        cls._personas[name.lower()] = persona_class
        logger.info(f"Registered persona: {name}")

