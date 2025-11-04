"""
Audio player for playback
"""

import numpy as np
import sounddevice as sd
from pathlib import Path
from typing import Optional
from loguru import logger
import threading
import wave
import soundfile as sf


class AudioPlayer:
    """Audio player for playback"""
    
    def __init__(self, sample_rate: int = 44100, channels: int = 1, delete_after_playback: bool = True):
        """
        Create a new audio player
        
        Args:
            sample_rate: Sample rate in Hz
            channels: Number of audio channels
            delete_after_playback: Whether to delete audio files after playback
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.delete_after_playback = delete_after_playback
        self.is_playing = False
        self.current_stream: Optional[sd.OutputStream] = None
        self.current_samples: Optional[np.ndarray] = None
        self.sample_index = 0
        self.current_audio_file: Optional[Path] = None
        self._playback_thread: Optional[threading.Thread] = None
        logger.debug(f"Audio player created (sample_rate: {sample_rate}, channels: {channels}, delete_after_playback: {delete_after_playback})")
    
    def _stream_callback(self, outdata, frames, time, status):
        """Callback function for audio stream"""
        # Only log status if it's an error, not warnings (underflows can be minor)
        if status:
            # Underflow is expected occasionally, only log if it's frequent or other errors
            if status.output_underflow:
                # Silently handle occasional underflows - they're usually not critical
                pass
            else:
                logger.warning(f"[Audio] Stream status: {status}")
        
        if self.current_samples is None or self.sample_index >= len(self.current_samples):
            # No more data, output silence and stop
            outdata.fill(0)
            if self.is_playing:
                logger.debug("[Audio] Audio playback completed")
                self.is_playing = False
                if self.current_stream:
                    try:
                        self.current_stream.stop()
                    except:
                        pass
                    self.current_stream = None
            return
        
        # Calculate how many samples to copy
        remaining = len(self.current_samples) - self.sample_index
        frames_to_copy = min(frames, remaining)
        
        # Copy samples to output buffer
        if self.channels == 1:
            # Ensure we copy the right shape (1D array for mono)
            samples_slice = self.current_samples[
                self.sample_index:self.sample_index + frames_to_copy
            ]
            # Ensure samples_slice is 1D for proper assignment
            if samples_slice.ndim == 0:
                samples_slice = np.array([samples_slice])
            outdata[:frames_to_copy, 0] = samples_slice.reshape(-1)
            # Fill rest with zeros if needed
            if frames_to_copy < frames:
                outdata[frames_to_copy:, 0] = 0.0
        else:
            # Multi-channel
            samples_slice = self.current_samples[
                self.sample_index:self.sample_index + frames_to_copy
            ]
            if len(samples_slice.shape) == 1:
                # Reshape if needed
                samples_slice = samples_slice.reshape(-1, self.channels)
            outdata[:frames_to_copy] = samples_slice
            if frames_to_copy < frames:
                outdata[frames_to_copy:] = 0
        
        self.sample_index += frames_to_copy
    
    def play(self, audio_data: bytes) -> None:
        """
        Play PCM audio data
        
        Args:
            audio_data: PCM audio data (int16 bytes)
        """
        try:
            # Stop any currently playing audio
            self.stop()
            
            # Convert bytes to numpy array (int16)
            # Ensure proper byte order (little-endian for Windows)
            # Using copy() instead of view to avoid issues with mutable buffers
            samples = np.frombuffer(audio_data, dtype='<i2').copy()  # '<i2' = little-endian int16
            
            # Convert to float32 [-1.0, 1.0]
            # Divide by 32768.0 to convert from int16 range [-32768, 32767] to [-1.0, 1.0]
            samples_float = samples.astype(np.float32) / 32768.0
            
            # Reshape if needed
            if self.channels > 1:
                samples_float = samples_float.reshape(-1, self.channels)
            
            # Store samples for streaming
            self.current_samples = samples_float
            self.sample_index = 0
            self.is_playing = True
            
            # Create output stream with callback
            # Use larger blocksize and higher latency to prevent underflows
            # blocksize: larger = less frequent callbacks but smoother playback
            # latency: 'high' means higher latency priority (more stable)
            blocksize = 8192  # Increased from 4096 for better stability
            latency = 0.1  # 100ms latency for smoother playback
            
            self.current_stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.float32,
                blocksize=blocksize,
                latency=latency,
                callback=self._stream_callback
            )
            
            # Start the stream
            self.current_stream.start()
            
            logger.info(f"[Audio] Playing {len(samples)} samples at {self.sample_rate}Hz, {self.channels} channels")
            
        except Exception as e:
            logger.error(f"[Audio] Failed to play audio: {e}")
            self.is_playing = False
            if self.current_stream:
                try:
                    self.current_stream.stop()
                except:
                    pass
                self.current_stream = None
            raise
    
    def stop(self) -> None:
        """Stop audio playback"""
        if self.current_stream:
            try:
                self.current_stream.stop()
            except:
                pass
            self.current_stream = None
        
        self.is_playing = False
        self.current_samples = None
        self.sample_index = 0
        logger.debug("[Audio] Playback stopped")
    
    def wait_for_completion(self) -> None:
        """Wait for audio playback to complete"""
        if self.current_stream:
            while self.is_playing:
                sd.sleep(10)  # Sleep 10ms at a time
    
    def get_current_level(self) -> float:
        """
        Get current audio level (for mouth sync)
        
        Returns:
            Audio level (0.0 to 1.0)
        """
        if not self.is_playing or self.current_samples is None:
            return 0.0
        
        # Calculate RMS of recent samples for mouth sync
        if self.sample_index < len(self.current_samples):
            # Get a window of recent samples
            window_start = max(0, self.sample_index - 1024)
            window_end = min(len(self.current_samples), self.sample_index)
            if window_end > window_start:
                recent_samples = self.current_samples[window_start:window_end]
                rms = np.sqrt(np.mean(recent_samples ** 2))
                return min(1.0, rms * 2.0)  # Scale to 0-1 range
        
        return 0.5 if self.is_playing else 0.0
    
    def play_file(self, audio_file_path: str) -> None:
        """
        Play audio from file
        
        Args:
            audio_file_path: Path to audio file
        """
        audio_path = Path(audio_file_path)
        if not audio_path.exists():
            logger.error(f"[Audio] Audio file not found: {audio_path}")
            return
        
        logger.info(f"[Audio] Playing audio file: {audio_path}")
        
        # Stop any currently playing audio
        self.stop()
        
        # Store file path for deletion after playback
        self.current_audio_file = audio_path
        
        # Play audio file in a separate thread
        self._playback_thread = threading.Thread(
            target=self._play_file_thread,
            args=(audio_path,),
            daemon=True
        )
        self._playback_thread.start()
    
    def _play_file_thread(self, audio_path: Path) -> None:
        """Play audio file in a separate thread"""
        try:
            self.is_playing = True
            
            # Load audio file based on extension
            audio_ext = audio_path.suffix.lower()
            
            if audio_ext == '.wav':
                # Use wave for WAV files (no external dependencies)
                with wave.open(str(audio_path), 'rb') as wav_file:
                    sample_rate = wav_file.getframerate()
                    channels = wav_file.getnchannels()
                    sample_width = wav_file.getsampwidth()
                    frames = wav_file.readframes(-1)
                    
                    # Convert bytes to numpy array
                    if sample_width == 2:  # 16-bit
                        samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
                    elif sample_width == 4:  # 32-bit
                        samples = np.frombuffer(frames, dtype=np.int32).astype(np.float32) / 2147483648.0
                    else:  # 8-bit
                        samples = (np.frombuffer(frames, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
                    
                    # Convert stereo to mono if needed
                    if channels > 1:
                        samples = samples.reshape(-1, channels).mean(axis=1)
                    
                    # Resample if needed
                    if sample_rate != self.sample_rate:
                        from scipy import signal
                        num_samples = int(len(samples) * (self.sample_rate / sample_rate))
                        samples = signal.resample(samples, num_samples).astype(np.float32)
                        
            elif audio_ext == '.mp3':
                # Try to use soundfile first (requires ffmpeg for MP3)
                try:
                    samples, sample_rate = sf.read(str(audio_path))
                    # Convert to mono if stereo
                    if samples.ndim > 1:
                        samples = samples.mean(axis=1)
                    
                    # Resample if needed
                    if sample_rate != self.sample_rate:
                        from scipy import signal
                        num_samples = int(len(samples) * (self.sample_rate / sample_rate))
                        samples = signal.resample(samples, num_samples).astype(np.float32)
                except Exception as e:
                    logger.error(f"[Audio] Failed to load MP3 file (ffmpeg may not be installed): {e}")
                    logger.error("[Audio] Please install ffmpeg or use WAV format")
                    raise RuntimeError("MP3 playback requires ffmpeg. Install ffmpeg or use WAV format.")
            else:
                # Try soundfile as fallback
                try:
                    samples, sample_rate = sf.read(str(audio_path))
                    if samples.ndim > 1:
                        samples = samples.mean(axis=1)
                    if sample_rate != self.sample_rate:
                        from scipy import signal
                        num_samples = int(len(samples) * (self.sample_rate / sample_rate))
                        samples = signal.resample(samples, num_samples).astype(np.float32)
                except Exception as e:
                    logger.error(f"[Audio] Failed to load audio file {audio_ext}: {e}")
                    raise
            
            # Store samples for streaming
            self.current_samples = samples
            self.sample_index = 0
            
            # Create output stream
            blocksize = 8192
            latency = 0.1
            
            self.current_stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.float32,
                blocksize=blocksize,
                latency=latency,
                callback=self._stream_callback
            )
            
            # Start the stream
            self.current_stream.start()
            
            logger.info(f"[Audio] Playing {len(samples)} samples at {self.sample_rate}Hz")
            
            # Wait for playback to complete
            # Calculate approximate duration
            duration_seconds = len(samples) / self.sample_rate
            import time
            start_time = time.time()
            
            while self.is_playing and self.sample_index < len(samples):
                elapsed = time.time() - start_time
                if elapsed > duration_seconds + 1.0:  # Add 1 second buffer
                    break
                time.sleep(0.1)
            
            logger.info("[Audio] Playback completed")
            
        except Exception as e:
            logger.error(f"[Audio] Failed to play audio file: {e}")
            import traceback
            logger.debug(traceback.format_exc())
        finally:
            self.is_playing = False
            if self.current_stream:
                try:
                    self.current_stream.stop()
                except:
                    pass
                self.current_stream = None
            self.current_samples = None
            
            # Delete file after playback if configured
            if self.delete_after_playback and self.current_audio_file and self.current_audio_file.exists():
                try:
                    self.current_audio_file.unlink()
                    logger.debug(f"[Audio] Deleted audio file: {self.current_audio_file}")
                except Exception as e:
                    logger.warning(f"[Audio] Failed to delete audio file: {e}")
            
            self.current_audio_file = None

