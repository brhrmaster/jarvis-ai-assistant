"""
Audio Recording Queue - Processamento em fila para gravação e transcrição
Aplica princípios de Clean Code e Refatoração (Martin Fowler)
"""

import queue
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Callable
from loguru import logger

from pyjarvis_shared import AppConfig
from .audio_recorder import AudioRecorder


class RecordingStatus(Enum):
    """Status da gravação"""
    PENDING = "pending"
    INITIALIZING = "initializing"
    RECORDING = "recording"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class RecordingTask:
    """Tarefa de gravação (Value Object)"""
    task_id: str
    config: AppConfig
    language: str
    on_status_update: Optional[Callable[[RecordingStatus], None]] = None
    on_text_chunk: Optional[Callable[[str], None]] = None
    created_at: float = 0.0
    
    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()


@dataclass
class RecordingResult:
    """Resultado da gravação (Value Object)"""
    task_id: str
    success: bool
    transcribed_text: str = ""
    error_message: str = ""
    audio_file_path: Optional[str] = None
    duration_seconds: float = 0.0


class AudioRecordingQueue:
    """
    Fila de processamento de gravação
    Aplica padrão Producer-Consumer para processamento assíncrono
    """
    
    def __init__(self):
        """Inicializa a fila de gravação"""
        self._task_queue: queue.Queue[RecordingTask] = queue.Queue()
        self._result_store: dict[str, RecordingResult] = {}
        self._result_lock = threading.Lock()
        self._active_recordings: dict[str, threading.Event] = {}  # task_id -> stop_event
        self._active_recordings_lock = threading.Lock()
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_worker = threading.Event()
        self._is_running = False
    
    def start(self) -> None:
        """Inicia o worker thread de processamento"""
        if self._is_running:
            return
        
        self._is_running = True
        self._stop_worker.clear()
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
        logger.debug("[RecordingQueue] Worker thread started")
    
    def stop(self) -> None:
        """Para o worker thread"""
        if not self._is_running:
            return
        
        self._stop_worker.set()
        if self._worker_thread:
            self._worker_thread.join(timeout=5.0)
        self._is_running = False
        logger.debug("[RecordingQueue] Worker thread stopped")
    
    def submit_task(
        self,
        config: AppConfig,
        language: str,
        on_status_update: Optional[Callable[[RecordingStatus], None]] = None,
        on_text_chunk: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        Submete uma tarefa de gravação para processamento
        
        Args:
            config: Configuração da aplicação
            language: Idioma para reconhecimento de voz
            on_status_update: Callback para atualizações de status
            on_text_chunk: Callback para chunks de texto transcrito
            
        Returns:
            ID da tarefa
        """
        import uuid
        task_id = str(uuid.uuid4())
        
        task = RecordingTask(
            task_id=task_id,
            config=config,
            language=language,
            on_status_update=on_status_update,
            on_text_chunk=on_text_chunk
        )
        
        self._task_queue.put(task)
        logger.debug(f"[RecordingQueue] Task {task_id} submitted")
        return task_id
    
    def stop_recording(self, task_id: str) -> bool:
        """
        Para uma gravação em andamento
        
        Args:
            task_id: ID da tarefa a ser parada
            
        Returns:
            True se a tarefa foi encontrada e sinalizada para parar
        """
        with self._active_recordings_lock:
            if task_id in self._active_recordings:
                stop_event = self._active_recordings[task_id]
                stop_event.set()
                logger.debug(f"[RecordingQueue] Stop signal sent for task {task_id}")
                return True
        return False
    
    def get_result(self, task_id: str, timeout: Optional[float] = None) -> Optional[RecordingResult]:
        """
        Obtém o resultado de uma tarefa
        
        Args:
            task_id: ID da tarefa
            timeout: Timeout em segundos (None = sem timeout)
            
        Returns:
            Resultado da tarefa ou None se não disponível
        """
        start_time = time.time()
        poll_interval = 0.1
        
        while True:
            with self._result_lock:
                if task_id in self._result_store:
                    result = self._result_store[task_id]
                    # Remove from store after retrieval to free memory
                    # self._result_store.pop(task_id, None)  # Keep for now in case of re-read
                    return result
            
            if timeout and (time.time() - start_time) >= timeout:
                logger.warning(f"[RecordingQueue] Timeout waiting for result {task_id} after {timeout}s")
                return None
            
            time.sleep(poll_interval)
    
    def _worker_loop(self) -> None:
        """Loop do worker que processa tarefas da fila"""
        logger.debug("[RecordingQueue] Worker loop started")
        
        while not self._stop_worker.is_set():
            try:
                # Get task with timeout to allow checking stop_worker
                try:
                    task = self._task_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                logger.debug(f"[RecordingQueue] Processing task {task.task_id}")
                result = self._process_recording_task(task)
                
                # Result is already stored in _process_recording_task, just log completion
                logger.debug(f"[RecordingQueue] Task {task.task_id} fully completed: success={result.success}")
                
            except Exception as e:
                logger.error(f"[RecordingQueue] Worker error: {e}")
        
        logger.debug("[RecordingQueue] Worker loop stopped")
    
    def _process_recording_task(self, task: RecordingTask) -> RecordingResult:
        """
        Processa uma tarefa de gravação
        
        Args:
            task: Tarefa de gravação
            
        Returns:
            Resultado da gravação
        """
        start_time = time.time()
        
        try:
            # Update status: initializing
            if task.on_status_update:
                task.on_status_update(RecordingStatus.INITIALIZING)
            
            # Create recorder
            recorder = AudioRecorder(config=task.config, language=task.language)
            
            # Create stop event and register it
            stop_event = threading.Event()
            started_event = threading.Event()
            
            with self._active_recordings_lock:
                self._active_recordings[task.task_id] = stop_event
            
            try:
                # Wrapper para capturar resultado
                result_container = {"text": "", "error": None, "audio_path": None}
                
                def on_transcription_chunk(text: str) -> None:
                    """Callback para chunks de transcrição"""
                    if text and text.strip():
                        # Accumulate text (may receive multiple chunks)
                        current_text = result_container["text"]
                        new_text = text.strip()
                        if current_text:
                            # Combine chunks, avoiding duplicates
                            if new_text not in current_text:
                                result_container["text"] = f"{current_text} {new_text}".strip()
                            else:
                                result_container["text"] = current_text  # Keep existing if duplicate
                        else:
                            result_container["text"] = new_text
                        if task.on_text_chunk:
                            task.on_text_chunk(text.strip())
                
                # Update status: recording
                if task.on_status_update:
                    task.on_status_update(RecordingStatus.RECORDING)
                
                # Record audio (synchronous call, but internally uses threads)
                transcribed_text = recorder.record_until_stop(
                    stop_event=stop_event,
                    started_event=started_event,
                    on_text_chunk=on_transcription_chunk if task.on_text_chunk else None
                )
                logger.debug(f"[RecordingQueue] recorder.record_until_stop returned: '{transcribed_text}'")
            finally:
                # Unregister stop event
                with self._active_recordings_lock:
                    self._active_recordings.pop(task.task_id, None)
            
            # Update status: processing
            if task.on_status_update:
                task.on_status_update(RecordingStatus.PROCESSING)
            
            # Use the transcribed text (from parameter or container)
            # Prioritize the returned text, then container
            final_text = transcribed_text or result_container["text"]
            logger.debug(f"[RecordingQueue] Initial text: transcribed_text='{transcribed_text}', container='{result_container['text']}'")
            
            # If we still don't have text, wait a bit more and check again
            # RealtimeSTT sometimes processes text asynchronously
            if not final_text or not final_text.strip():
                logger.debug(f"[RecordingQueue] No text yet, waiting additional time for delayed transcription...")
                max_wait_attempts = 10  # Wait up to 10 seconds
                for attempt in range(max_wait_attempts):
                    time.sleep(1.0)
                    # Check both sources again
                    if transcribed_text and transcribed_text.strip():
                        final_text = transcribed_text
                        logger.debug(f"[RecordingQueue] Got transcribed_text after wait (attempt {attempt+1}): {final_text}")
                        break
                    elif result_container["text"] and result_container["text"].strip():
                        final_text = result_container["text"]
                        logger.debug(f"[RecordingQueue] Got container text after wait (attempt {attempt+1}): {final_text}")
                        break
            
            duration = time.time() - start_time
            
            # Get audio file path if available
            audio_path = None
            if hasattr(recorder, '_current_audio_file') and recorder._current_audio_file:
                audio_path = str(recorder._current_audio_file)
            
            # Create result BEFORE status update to ensure it's ready
            result = RecordingResult(
                task_id=task.task_id,
                success=True,
                transcribed_text=final_text or "",  # Ensure non-None
                audio_file_path=audio_path,
                duration_seconds=duration
            )
            
            # Store result IMMEDIATELY in the result store (critical!)
            # This makes it available to get_result() even before status update
            with self._result_lock:
                self._result_store[task.task_id] = result
                logger.info(f"[RecordingQueue] Result stored for task {task.task_id}: text_length={len(final_text or '')}, success={result.success}")
            
            # Update status: completed (only after result is stored)
            if task.on_status_update:
                task.on_status_update(RecordingStatus.COMPLETED)
            
            return result
            
        except Exception as e:
            logger.error(f"[RecordingQueue] Task {task.task_id} failed: {e}")
            duration = time.time() - start_time
            
            if task.on_status_update:
                task.on_status_update(RecordingStatus.FAILED)
            
            return RecordingResult(
                task_id=task.task_id,
                success=False,
                error_message=str(e),
                duration_seconds=duration
            )


# Singleton instance
_recording_queue: Optional[AudioRecordingQueue] = None


def get_recording_queue() -> AudioRecordingQueue:
    """Obtém instância singleton da fila de gravação"""
    global _recording_queue
    if _recording_queue is None:
        _recording_queue = AudioRecordingQueue()
        _recording_queue.start()
    return _recording_queue

