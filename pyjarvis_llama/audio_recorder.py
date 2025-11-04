"""
Audio recorder using RealtimeSTT for speech-to-text
"""

import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable
from loguru import logger

try:
    from pyjarvis_shared import AppConfig
except ImportError:
    AppConfig = None

try:
    from RealtimeSTT import AudioToTextRecorder
except ImportError as e:
    logger.error(f"Failed to import RealtimeSTT: {e}")
    logger.error("Install with: pip install RealtimeSTT")
    AudioToTextRecorder = None

try:
    import sounddevice as sd
    import soundfile as sf
    import numpy as np
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    logger.warning("sounddevice or soundfile not available, audio saving disabled")

# MP3 encoding with soundfile is faster than OGG, so we don't need pydub for recording


class AudioRecorder:
    """Audio recorder wrapper for RealtimeSTT"""
    
    def __init__(
        self,
        config: Optional[AppConfig] = None,
        model: Optional[str] = None,
        language: Optional[str] = None,
        use_microphone: bool = True,
        on_realtime_update: Optional[Callable[[str], None]] = None,
        audio_output_dir: Optional[str] = None
    ):
        """
        Create a new audio recorder
        
        Args:
            config: Application configuration (preferred source for model, language, audio_output_dir)
            model: Whisper model to use (base, small, medium, large). Overrides config if provided.
            language: Language code (en, pt, etc.). Overrides config if provided.
            use_microphone: Whether to use microphone
            on_realtime_update: Callback for real-time transcription updates
            audio_output_dir: Directory to save audio files temporarily. Overrides config if provided.
        """
        if AudioToTextRecorder is None:
            raise ImportError("RealtimeSTT is not installed. Install with: pip install RealtimeSTT")
        
        # Get values from config or use provided/default values
        if config:
            self.model = model or getattr(config, 'stt_model', 'base')
            self.language = language or getattr(config, 'stt_language', 'en')
            output_dir = audio_output_dir or getattr(config, 'audio_output_dir', './audio')
        else:
            # Fallback to provided values or defaults
            self.model = model or 'base'
            self.language = language or 'en'
            output_dir = audio_output_dir or './audio'
        
        self.use_microphone = use_microphone
        self.on_realtime_update = on_realtime_update
        self.audio_output_dir = Path(output_dir)
        self.recorder: Optional[AudioToTextRecorder] = None
        self._recording = False
        self._stop_event = threading.Event()
        self._current_audio_file: Optional[Path] = None
        
        # Ensure audio directory exists
        self.audio_output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"AudioRecorder initialized: model={self.model}, language={self.language}, output_dir={self.audio_output_dir}")
        
    def record_until_stop(
        self, 
        stop_event: threading.Event, 
        started_event: Optional[threading.Event] = None,
        on_text_chunk: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        Record audio until stop event is set
        
        Args:
            stop_event: Threading event to signal when to stop recording
            started_event: Optional event to signal when recording has actually started
            on_text_chunk: Optional callback for text chunks as they are transcribed
            
        Returns:
            Transcribed text from the recording
        """
        if AudioToTextRecorder is None:
            raise ImportError("RealtimeSTT is not installed")
        
        transcribed_text = ""
        recording_error = None
        
        def recording_worker():
            """Worker thread that performs the actual recording"""
            nonlocal transcribed_text, recording_error
            
            # Use a lock to ensure transcribed_text is safely updated
            import threading
            text_lock = threading.Lock()
            
            # Audio recording variables (declared outside try to be accessible in finally)
            audio_samples = []
            audio_sample_rate = 16000  # Standard sample rate for speech
            audio_stream = None
            
            try:
                self._recording = True
                
                # Generate unique audio file path with format: rec_YYYYMMDD-HHmmss.wav
                timestamp_str = datetime.now().strftime("%Y%m%d-%H%M%S")
                audio_filename = f"rec_{timestamp_str}.wav"
                self._current_audio_file = self.audio_output_dir / audio_filename
                
                # Start parallel audio recording FIRST (before RealtimeSTT initialization)
                # This gives immediate audio capture while RealtimeSTT loads
                if AUDIO_AVAILABLE:
                    def audio_callback(indata, frames, time_info, status):
                        """Callback to capture audio samples"""
                        if status:
                            logger.debug(f"Audio callback status: {status}")
                        audio_samples.append(indata.copy())
                    
                    try:
                        audio_stream = sd.InputStream(
                            samplerate=audio_sample_rate,
                            channels=1,
                            dtype=np.float32,
                            callback=audio_callback,
                            blocksize=4096
                        )
                        audio_stream.start()
                        logger.debug("Started parallel audio recording")
                    except Exception as e:
                        logger.warning(f"Failed to start parallel audio recording: {e}")
                        audio_stream = None
                
                # Signal that audio recording has started (parallel stream)
                if started_event:
                    started_event.set()
                
                # Configure recorder with more lenient settings for better detection
                recorder_config = {
                    "model": self.model,
                    "language": self.language,
                    "use_microphone": self.use_microphone,
                    "webrtc_sensitivity": 1,  # Less aggressive (more sensitive) - detects speech more easily
                    "post_speech_silence_duration": 1.0,  # Wait 1s after speech ends before processing
                    "min_gap_between_recordings": 0.2,
                    "min_length_of_recording": 0.3,  # Shorter minimum recording length
                    "pre_recording_buffer_duration": 0.3,  # Capture audio before VAD triggers
                    "spinner": False,  # Disable spinner to reduce console output
                }
                
                # Add real-time update callback if provided
                if self.on_realtime_update:
                    recorder_config["on_realtime_transcription_update"] = self.on_realtime_update
                
                # Use AudioToTextRecorder as context manager
                # Note: This may take a moment to initialize (load Whisper model)
                # But parallel audio stream is already capturing
                logger.debug("[AudioRecorder] Initializing RealtimeSTT recorder...")
                with AudioToTextRecorder(**recorder_config) as recorder:
                    self.recorder = recorder
                    logger.debug("[AudioRecorder] RealtimeSTT recorder initialized and ready")
                    
                    # Keep recording until stop event is set
                    accumulated_text = []
                    last_text = ""
                    
                    # Collect text using recorder.text() in a loop
                    # The recorder.text() method blocks until text is available
                    # We'll collect chunks and check stop_event periodically
                    import queue
                    text_queue = queue.Queue()
                    collector_done = threading.Event()
                    
                    def text_collector():
                        """Collect text from recorder in a separate thread"""
                        consecutive_empties = 0
                        max_consecutive_empties = 10  # Stop after 10 empty attempts
                        
                        try:
                            # Keep getting text until stop event is set
                            while not stop_event.is_set():
                                try:
                                    # recorder.text() blocks until new text is available
                                    text = recorder.text()
                                    if text and text.strip():
                                        text_queue.put(text.strip())
                                        consecutive_empties = 0  # Reset counter
                                        logger.debug(f"Transcribed chunk: {text.strip()}")
                                        # Call callback if provided
                                        if on_text_chunk:
                                            try:
                                                on_text_chunk(text.strip())
                                            except Exception as e:
                                                logger.debug(f"Error in on_text_chunk callback: {e}")
                                    else:
                                        consecutive_empties += 1
                                except StopIteration:
                                    # End of recording stream
                                    logger.debug("Recorder finished (StopIteration)")
                                    break
                                except Exception as e:
                                    if not stop_event.is_set():
                                        logger.debug(f"Text collector error: {e}")
                                    # Small delay before retrying
                                    if stop_event.wait(timeout=0.1):
                                        break
                            
                            # After stop_event is set, continue collecting for a while
                            # to get any final text from RealtimeSTT's processing buffer
                            logger.debug("Stop event set, continuing to collect final transcription...")
                            final_attempts = 10  # More attempts to get all text
                            
                            for attempt in range(final_attempts):
                                try:
                                    # Wait a bit between attempts, but shorter waits
                                    if attempt > 0:
                                        time.sleep(0.5)
                                    
                                    if hasattr(recorder, 'text'):
                                        try:
                                            # Try to get final text (non-blocking if possible)
                                            # recorder.text() will wait for speech, but we limit it
                                            text = recorder.text()
                                            if text and text.strip():
                                                text_queue.put(text.strip())
                                                consecutive_empties = 0
                                                logger.debug(f"Final transcribed chunk (attempt {attempt+1}): {text.strip()}")
                                                # Call callback if provided
                                                if on_text_chunk:
                                                    try:
                                                        on_text_chunk(text.strip())
                                                    except Exception as e:
                                                        logger.debug(f"Error in on_text_chunk callback: {e}")
                                            else:
                                                consecutive_empties += 1
                                                if consecutive_empties >= 3:
                                                    # No more text coming, stop trying
                                                    logger.debug(f"No more text after {consecutive_empties} attempts, stopping collector")
                                                    break
                                        except StopIteration:
                                            logger.debug("Recorder finished (StopIteration in final attempts)")
                                            break
                                        except Exception as e:
                                            logger.debug(f"Final text collection attempt {attempt+1} error: {e}")
                                            consecutive_empties += 1
                                            if consecutive_empties >= 3:
                                                break
                                except Exception as e:
                                    logger.debug(f"Final text collection attempt {attempt+1} outer error: {e}")
                        except Exception as e:
                            logger.error(f"Text collector thread error: {e}")
                        finally:
                            collector_done.set()
                            logger.debug("Text collector thread finished")
                    
                    # Start text collector thread
                    collector_thread = threading.Thread(target=text_collector, daemon=True)
                    collector_thread.start()
                    
                    # Collect text chunks while recording (with periodic stop_event checks)
                    while not stop_event.is_set():
                        try:
                            # Try to get text from queue with short timeout
                            text = text_queue.get(timeout=0.2)
                            if text and text.strip() and text.strip() != last_text:
                                accumulated_text.append(text.strip())
                                last_text = text.strip()
                                logger.debug(f"Accumulated text so far: {' '.join(accumulated_text)}")
                        except queue.Empty:
                            # No new text, continue checking stop_event
                            continue
                        except Exception as e:
                            if not stop_event.is_set():
                                logger.debug(f"Text collection error: {e}")
                    
                    # When stop_event is detected, give RealtimeSTT time to process buffered audio
                    # before stopping the stream. This ensures we capture all transcribed text.
                    logger.debug("Stop event detected, allowing RealtimeSTT to process buffered audio...")
                    
                    # Give RealtimeSTT time to process the audio already in its buffer
                    # The post_speech_silence_duration is 1.0s, so we wait a bit more
                    time.sleep(2.5)  # Wait for RealtimeSTT to finish processing current buffer
                    
                    # Now stop the audio stream to prevent capturing more silence
                    logger.debug("Stopping audio stream after buffer processing...")
                    if audio_stream:
                        try:
                            audio_stream.stop()
                            audio_stream.close()
                            logger.debug("Stopped parallel audio recording")
                            audio_stream = None  # Mark as stopped
                        except Exception as e:
                            logger.debug(f"Error stopping audio stream: {e}")
                    
                    # Continue collecting text from RealtimeSTT's processed buffer
                    # IMPORTANT: We're still inside the AudioToTextRecorder context manager
                    # Don't exit yet - RealtimeSTT may still be processing
                    logger.debug("Continuing to collect final transcription (still in recorder context)...")
                    time.sleep(2.0)  # Additional time for final processing
                    
                    # Continue collecting from queue while collector is still working
                    # This happens while we're still in the context manager
                    # This helps get text that was already processed
                    collector_timeout_start = time.time()
                    collector_timeout_duration = 10.0  # Max 10 seconds to wait for collector
                    
                    while (time.time() - collector_timeout_start) < collector_timeout_duration:
                        # Check if collector is done
                        if collector_done.is_set():
                            break
                        
                        # Try to get any text that's already in the queue
                        try:
                            text = text_queue.get(timeout=0.5)
                            if text and text.strip() and text.strip() != last_text:
                                accumulated_text.append(text.strip())
                                last_text = text.strip()
                                logger.debug(f"Collected text while waiting: {text.strip()}")
                        except queue.Empty:
                            # No text yet, continue waiting
                            continue
                    
                    # Wait for collector thread to finish collecting final text
                    # Give it more time - sometimes RealtimeSTT processes text slowly
                    logger.debug("Waiting for text collector to finish...")
                    collector_done.wait(timeout=15.0)  # Increased timeout significantly
                    
                    # Additional wait after collector signals done
                    # Sometimes text is still being processed
                    time.sleep(2.0)
                    
                    # Get any remaining text from queue (drain the queue)
                    queue_drained = False
                    max_queue_drain_attempts = 20
                    for _ in range(max_queue_drain_attempts):
                        try:
                            text = text_queue.get_nowait()
                            if text and text.strip() and text.strip() != last_text:
                                accumulated_text.append(text.strip())
                                last_text = text.strip()
                                logger.debug(f"Drained text from queue: {text.strip()}")
                                queue_drained = True
                        except queue.Empty:
                            if not queue_drained:
                                # Give it one more chance with a small delay
                                time.sleep(0.2)
                                try:
                                    text = text_queue.get_nowait()
                                    if text and text.strip() and text.strip() != last_text:
                                        accumulated_text.append(text.strip())
                                        last_text = text.strip()
                                        logger.debug(f"Final drained text: {text.strip()}")
                                except queue.Empty:
                                    break
                            else:
                                break
                    
                    # Try to get any final text using recorder attributes/methods
                    try:
                        # Check for common methods to get final text
                        if hasattr(recorder, 'text'):
                            # Try one more time to get text
                            pass
                        if hasattr(recorder, 'get_final_text'):
                            final_text = recorder.get_final_text()
                            if final_text and final_text.strip():
                                accumulated_text.append(final_text.strip())
                    except:
                        pass
                    
                    # Combine all text chunks and remove duplicates
                    if accumulated_text:
                        # Remove duplicates while preserving order
                        seen = set()
                        unique_chunks = []
                        for chunk in accumulated_text:
                            # Normalize chunk
                            normalized = chunk.strip()
                            if normalized and normalized.lower() not in seen:
                                seen.add(normalized.lower())
                                unique_chunks.append(normalized)
                        final_text_result = " ".join(unique_chunks).strip()
                        with text_lock:
                            transcribed_text = final_text_result
                        logger.info(f"[AudioRecorder] Final transcribed text ({len(unique_chunks)} chunks): {transcribed_text}")
                    else:
                        logger.warning("[AudioRecorder] No accumulated text found after recording")
                        # Give one final chance - wait a bit more and check queue again
                        logger.debug("[AudioRecorder] Waiting additional time for delayed transcription...")
                        time.sleep(3.0)
                        # Check queue one more time
                        try:
                            final_chunks = []
                            while not text_queue.empty():
                                try:
                                    text = text_queue.get_nowait()
                                    if text and text.strip():
                                        final_chunks.append(text.strip())
                                except queue.Empty:
                                    break
                            if final_chunks:
                                with text_lock:
                                    transcribed_text = " ".join(final_chunks).strip()
                                logger.info(f"[AudioRecorder] Delayed transcription received: {transcribed_text}")
                        except Exception as e:
                            logger.debug(f"Error in delayed transcription check: {e}")
                    
                    # Audio stream should already be stopped at this point
                    # But ensure it's stopped if for some reason it wasn't
                    if audio_stream:
                        try:
                            audio_stream.stop()
                            audio_stream.close()
                            logger.debug("Stopped parallel audio recording (final check)")
                        except Exception as e:
                            logger.debug(f"Error stopping audio stream (final check): {e}")
                    
                    # Save recorded audio to file (in background thread for better performance)
                    if audio_samples and AUDIO_AVAILABLE:
                        # Save audio in a separate thread to avoid blocking
                        def save_audio_async():
                            try:
                                # Concatenate all audio samples
                                if audio_samples:
                                    audio_data = np.concatenate(audio_samples, axis=0)
                                    
                                    # Convert float32 to int16 if needed
                                    if audio_data.dtype == np.float32:
                                        # Clamp values to [-1.0, 1.0] range and convert to int16
                                        audio_data = np.clip(audio_data, -1.0, 1.0)
                                        audio_data_int16 = (audio_data * 32767.0).astype(np.int16)
                                    else:
                                        audio_data_int16 = audio_data.astype(np.int16)
                                    
                                    # Save as WAV directly - fastest option (no compression, instant save)
                                    sf.write(str(self._current_audio_file), audio_data_int16, audio_sample_rate)
                                    logger.debug(f"Saved audio recording to WAV: {self._current_audio_file}")
                            except Exception as e:
                                logger.warning(f"Failed to save audio file: {e}")
                        
                        # Start saving in background thread (non-blocking)
                        save_thread = threading.Thread(target=save_audio_async, daemon=True)
                        save_thread.start()
                        logger.debug("Started audio file save in background thread")
                        
            except Exception as e:
                recording_error = e
                logger.error(f"Recording worker error: {e}")
            finally:
                # Stop audio stream if still running
                if audio_stream:
                    try:
                        audio_stream.stop()
                        audio_stream.close()
                    except:
                        pass
                
                self._recording = False
                self.recorder = None
                
                # Delete audio file after transcription is complete
                # Wait a moment to ensure transcription is fully processed
                time.sleep(0.2)
                if self._current_audio_file and self._current_audio_file.exists():
                    try:
                        self._current_audio_file.unlink()
                        logger.debug(f"Deleted audio file: {self._current_audio_file}")
                    except Exception as e:
                        logger.warning(f"Failed to delete audio file {self._current_audio_file}: {e}")
                self._current_audio_file = None
        
        # Start recording in a separate thread
        worker_thread = threading.Thread(target=recording_worker, daemon=True)
        worker_thread.start()
        
        # Wait for stop event (will be set by main thread when Enter is pressed)
        # The worker thread will keep recording until stop_event is set
        
        # Wait for the worker to finish (with timeout to prevent hanging)
        worker_thread.join(timeout=60.0)  # Increased timeout to allow final processing
        
        # Give additional time for any delayed transcription
        # Sometimes RealtimeSTT processes text after the context manager exits
        if not transcribed_text or not transcribed_text.strip():
            logger.debug("[AudioRecorder] No text yet, waiting additional 5 seconds for delayed transcription...")
            import queue
            # Wait a bit more - sometimes text arrives late
            for wait_attempt in range(5):
                time.sleep(1.0)
                # Check if worker thread is still alive (might still be processing)
                if worker_thread.is_alive():
                    logger.debug(f"[AudioRecorder] Worker still alive after stop, attempt {wait_attempt+1}")
                else:
                    logger.debug(f"[AudioRecorder] Worker finished")
                    break
            
            # Final check after waiting
            if not transcribed_text or not transcribed_text.strip():
                logger.warning("[AudioRecorder] Still no text after extended wait")
        
        if recording_error:
            raise recording_error
        
        return transcribed_text
    
    def is_recording(self) -> bool:
        """Check if currently recording"""
        return self._recording

