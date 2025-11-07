"""
Interactive CLI for PyJarvis LLM integration
"""

import asyncio
import sys
import threading
from typing import Optional
from loguru import logger
from pyjarvis_shared import AppConfig
from .llama_client import OllamaClient
from .personas import PersonaFactory, PersonaStrategy
from .conversation_context import ConversationContext
from .recording_queue import get_recording_queue, RecordingStatus, RecordingResult

# Import CLI client to send text to service
try:
    # Import directly from pyjarvis_cli
    from pyjarvis_cli.client import send_text_to_service
except ImportError as e:
    logger.warning(f"Failed to import pyjarvis_cli: {e}. TTS will be skipped.")
    send_text_to_service = None

# Validate language code (common Whisper languages)
valid_languages = {
    'en', 'english', 'pt', 'portuguese', 'es', 'spanish', 
    'fr', 'french', 'de', 'german', 'it', 'italian',
    'ja', 'japanese', 'ko', 'korean', 'zh', 'chinese',
    'ru', 'russian', 'ar', 'arabic', 'hi', 'hindi',
    'tr', 'turkish', 'pl', 'polish', 'nl', 'dutch',
    'sv', 'swedish', 'fi', 'finnish', 'no', 'norwegian'
}

# Map common language names to codes
lang_map = {
    'english': 'en', 'portuguese': 'pt', 'spanish': 'es',
    'french': 'fr', 'german': 'de', 'italian': 'it',
    'japanese': 'ja', 'korean': 'ko', 'chinese': 'zh',
    'russian': 'ru', 'arabic': 'ar', 'hindi': 'hi',
    'turkish': 'tr', 'polish': 'pl', 'dutch': 'nl',
    'swedish': 'sv', 'finnish': 'fi', 'norwegian': 'no'
}

def show_initial_menu(ollama_client: OllamaClient, persona: PersonaStrategy) -> None:
    divider = "="*60
    print(f"[SUCCESS] Connected to Ollama at {ollama_client.base_url}")
    print(f"- Using model: {ollama_client.model}")
    print(f"- Using persona: {persona.name}")
    print(f"\n{divider}")
    print("PyJarvis AI - Interactive Mode")
    print(divider)
    print("Type your message and press Enter.")
    print("The response will be sent to PyJarvis for voice synthesis.")
    print("Commands:")
    print("  /exit or /quit - Exit the program")
    print("  /clear - Clear the conversation")
    print("  /persona <name> - Change AI persona")
    print("  /lang [code] - Set language for speech recognition (or list available)")
    print("  /m - Record audio from microphone (press Enter to stop)")
    print(f"  Available personas: {', '.join(PersonaFactory.list_available())}")
    print(f"{divider}\n")

def change_persona(persona: PersonaStrategy, user_input: str) -> None:
    parts = user_input.split(maxsplit=1)
    if len(parts) > 1:
        new_persona_name = parts[1].strip()
        try:
            persona = PersonaFactory.create(new_persona_name)
            print(f"[SUCCESS] Changed persona to: {persona.name}\n")
        except Exception as e:
            print(f"[ERROR] Failed to change persona: {e}\n")
            print(f"Available personas: {', '.join(PersonaFactory.list_available())}\n")
    else:
        print(f"Current persona: {persona.name}")
        print(f"Available personas: {', '.join(PersonaFactory.list_available())}\n")
        print(f"Usage: /persona <name>\n")

def change_language(current_stt_language: str, user_input: str) -> None:
    parts = user_input.split(maxsplit=1)
    if len(parts) > 1:
        new_lang = parts[1].strip().lower()
        
        # Normalize language code
        normalized_lang = lang_map.get(new_lang, new_lang)
        
        if normalized_lang in valid_languages:
            current_stt_language = normalized_lang
            print(f"Speech recognition language set to: {current_stt_language.upper()}\n")
        else:
            print(f"Language codes: {new_lang}")
            print(f"   Supported languages: en, pt, es, fr, de, it, ja, ko, zh, ru, ar, hi, tr, pl, nl, sv, fi, no\n")
    else:
        print(f"Current speech recognition language: {current_stt_language.upper()}")
        print(f"   Usage: /lang <code>")
        print(f"   Example: /lang pt (for Portuguese)")
        print(f"   Example: /lang en (for English)")
        print(f"   Supported: en, pt, es, fr, de, it, ja, ko, zh, ru, ar, hi, tr, pl, nl, sv, fi, no\n")

async def interactive_loop(config: AppConfig) -> None:
    """
    Interactive loop for LLM chat
    
    Args:
        config: Application configuration
    """
    ollama_client = OllamaClient(config)
    
    # Create persona from configuration
    persona_name = getattr(config, 'ollama_persona', 'jarvis')
    persona = PersonaFactory.create(persona_name)
    
    # Initialize conversation context
    context_manager = ConversationContext()
    
    
    try:
        # Test connection to Ollama
        print("\n[INFO] Testing connection to Ollama server...")
        connected = await ollama_client.test_connection()
        if not connected:
            print("[ERROR] Failed to connect to Ollama server!")
            print(f"   Make sure Ollama is running at {ollama_client.base_url}")
            print("   Start Ollama with: ollama serve")
            return
        
        show_initial_menu(ollama_client, persona)

        # Current STT language (can be changed during session)
        current_stt_language = getattr(config, 'stt_language', 'en')
        
        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() in ['/exit', '/quit']:
                    print("\n👋 Goodbye!")
                    break
                
                if user_input.lower() == '/clear':
                    context_manager.clear_all_contexts()
                    print("Conversation history cleared!\n")
                    continue
                
                # Handle persona change
                if user_input.lower().startswith('/persona'):
                    change_persona(persona, user_input)
                    continue
                
                # Handle language selection for speech recognition
                if user_input.lower().startswith('/lang'):
                    change_language(current_stt_language, user_input)
                    continue
                
                # Handle microphone recording
                if user_input.lower() == '/m':
                    try:
                        await record_and_process_audio(ollama_client, persona, config, current_stt_language, context_manager)
                    except Exception as e:
                        print(f"[ERROR] Error during audio recording: {e}\n")
                        logger.error(f"Audio recording error: {e}")
                    continue
                
                # Use extracted method for LLM processing (Clean Code - DRY principle)
                await _process_user_input_with_llm(
                    user_input=user_input,
                    ollama_client=ollama_client,
                    persona=persona,
                    context_manager=context_manager
                )
                    
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted. Goodbye!")
                break
            except EOFError:
                print("\n👋 Goodbye!")
                break
                
    finally:
        await ollama_client.close()
        # Clear all context files on exit
        context_manager.clear_all_contexts()
        logger.info("[Context] Application ended, contexts cleared")

async def record_and_process_audio(
    ollama_client: OllamaClient,
    persona: PersonaStrategy,
    config: AppConfig,
    stt_language: str = "en",
    context_manager: Optional[ConversationContext] = None
) -> None:
    """
    Record audio from microphone, transcribe it, and process with LLM
    
    Usa fila de processamento para operação síncrona e código limpo
    Aplica princípios de Clean Code e Refatoração (Martin Fowler)
    
    Args:
        ollama_client: Ollama client instance
        persona: Current AI persona
        config: Application configuration
        stt_language: Language code for speech recognition
        context_manager: Conversation context manager (optional)
    """
    # Get recording queue (singleton)
    recording_queue = get_recording_queue()
    
    # Track recording state for UI feedback
    current_status = RecordingStatus.PENDING
    transcribed_chunks = []
    
    def handle_status_update(status: RecordingStatus) -> None:
        """Callback para atualizações de status (Clean Code: função pequena e focada)"""
        nonlocal current_status
        current_status = status
        
        status_messages = {
            RecordingStatus.INITIALIZING: "\nPreparing buffer for recording...",
            RecordingStatus.RECORDING: "\nListening... (Press Enter to stop recording)",
            RecordingStatus.PROCESSING: "\nProcessing transcription...",
            RecordingStatus.COMPLETED: "",  # No message needed
            RecordingStatus.FAILED: "\n[ERROR] Recording failed"
        }
        
        message = status_messages.get(status)
        if message:
            print(message)
    
    def handle_text_chunk(text: str) -> None:
        """Callback para chunks de texto transcrito (Clean Code: função pequena)"""
        if text and text.strip():
            transcribed_chunks.append(text.strip())
            logger.debug(f"[CLI] Received text chunk: {text.strip()}")
    
    # Submit recording task to queue
    task_id = recording_queue.submit_task(
        config=config,
        language=stt_language,
        on_status_update=handle_status_update,
        on_text_chunk=handle_text_chunk
    )
    
    # Wait for recording to start (polling with timeout)
    import time
    max_wait_attempts = 10
    for attempt in range(max_wait_attempts):
        if current_status in [RecordingStatus.RECORDING, RecordingStatus.INITIALIZING]:
            break
        time.sleep(0.5)
    
    # Wait for user to press Enter to stop recording
    try:
        input()  # Block until Enter is pressed
    except (KeyboardInterrupt, EOFError):
        pass
    
    # Signal stop to the recording via queue
    recording_queue.stop_recording(task_id)
    logger.debug(f"[CLI] Stop signal sent for task {task_id}")
    
    # Wait for result with timeout (give enough time for transcription to complete)
    logger.debug(f"[CLI] Waiting for recording result (task_id={task_id})...")
    # Poll for result - the worker thread stores it as soon as transcription completes
    result = None
    max_wait_time = 90.0
    wait_start = time.time()
    
    while (time.time() - wait_start) < max_wait_time:
        result = recording_queue.get_result(task_id, timeout=2.0)  # Short polling intervals
        if result:
            logger.debug(f"[CLI] Received result for task {task_id}")
            break
        time.sleep(0.2)  # Small delay between polls
    
    if not result:
        logger.warning(f"[CLI] Timeout waiting for result after {max_wait_time}s")
    
    # Handle result (Clean Code: early returns, clear error handling)
    if not result:
        print("[WARNING]  Recording timeout or no result received.\n")
        return
    
    if not result.success:
        print(f"[ERROR] Recording error: {result.error_message}\n")
        return
    
    # Combine transcribed text from result and chunks
    transcribed_text = result.transcribed_text or " ".join(transcribed_chunks)
    
    if not transcribed_text or not transcribed_text.strip():
        _print_no_speech_tips()
        return
    
    print(f"[SUCCESS] Transcribed: {transcribed_text}\n")
    
    # Continue with LLM processing using extracted method (Clean Code)
    await _process_user_input_with_llm(
        user_input=transcribed_text.strip(),
        ollama_client=ollama_client,
        persona=persona,
        context_manager=context_manager
    )


def _print_no_speech_tips() -> None:
    """Print tips when no speech is detected (Extract Method refactoring)"""
    print("[WARNING] No speech detected or transcription failed.")
    print("   Tips:")
    print("   - Make sure your microphone is working")
    print("   - Speak clearly and at a normal volume")
    print("   - Wait a moment after speaking before pressing Enter")
    print("   - Check microphone permissions\n")
    logger.warning("No transcribed text received from recorder")


async def _process_user_input_with_llm(
    user_input: str,
    ollama_client: OllamaClient,
    persona: PersonaStrategy,
    context_manager: Optional[ConversationContext] = None
) -> None:
    """
    Process user input with LLM (Extract Method refactoring)
    
    Args:
        user_input: User input text
        ollama_client: Ollama client instance
        persona: Current AI persona
        context_manager: Conversation context manager
    """
    # Build prompt using persona strategy
    base_prompt = persona.build_prompt(user_input)
    
    # Load previous context and prepend to prompt
    if context_manager:
        previous_context = context_manager.load_previous_context()
        if previous_context:
            prompt = f"{previous_context}\n\n{base_prompt}"
        else:
            prompt = base_prompt
        
        # Save request to context
        context_manager.save_request(user_input)
    else:
        prompt = base_prompt
    
    # Show thinking indicator
    print("🤔 Thinking...", end="", flush=True)
    
    # Generate response from Ollama
    try:
        response = await ollama_client.generate(prompt)
        
        # Save response to context
        if context_manager:
            context_manager.save_response(response)
        print("\r" + " "*20 + "\r", end="")  # Clear "Thinking..." line

        # Send response to PyJarvis for TTS
        if send_text_to_service:
            print("Processing...", end="", flush=True)
            try:
                # Clean the response text before saving
                cleaned_text = context_manager.clean_text(response) if context_manager else response
                await send_text_to_service(cleaned_text)
                print("\r[SUCCESS] Sent to PyJarvis!" + " "*30 + "\n")
            except Exception as e:
                print(f"\r[WARNING] Failed to send to PyJarvis: {e}\n")
                logger.error(f"Failed to send to PyJarvis: {e}")
        else:
            print("[WARNING] pyjarvis_cli not available, skipping TTS\n")
            logger.warning("pyjarvis_cli not available, skipping TTS")
    except Exception as e:
        print(f"\r[ERROR] Error: {e}\n")
        logger.error(f"Ollama generation error: {e}")

def main() -> None:
    """Main entry point"""
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
    )
    
    # Load configuration
    config = AppConfig()
    
    # Run interactive loop
    try:
        asyncio.run(interactive_loop(config))
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
