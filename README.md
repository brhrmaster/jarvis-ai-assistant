[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![Pygame](https://img.shields.io/badge/Pygame-2.5.0-green?logo=python)](https://www.pygame.org/)
[![Edge TTS](https://img.shields.io/badge/Edge%20TTS-6.1.0-blue?logo=microsoft)](https://github.com/rany2/edge-tts)
[![gTTS](https://img.shields.io/badge/gTTS-2.5.0-orange?logo=google)](https://github.com/pndurette/gTTS)
[![RealtimeSTT](https://img.shields.io/badge/RealtimeSTT-0.3.0-yellow)](https://github.com/KoljaB/RealtimeSTT)
[![Ollama](https://img.shields.io/badge/Ollama-Compatible-blueviolet?logo=llama)](https://ollama.ai/)
[![Pydantic](https://img.shields.io/badge/Pydantic-2.5.0%2B-ff69b4?logo=pydantic)](https://docs.pydantic.dev/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.1.0-EE4C2C?logo=pytorch)](https://pytorch.org/)
[![Transformers](https://img.shields.io/badge/Transformers-4.35.0-yellow?logo=huggingface)](https://huggingface.co/transformers/)


# PyJarvis - AI Assistant

A Python implementation of the Jarvis text-to-voice assistant with animated digital face, LLM integration, and speech recognition.

![UI](docs/ui-demo.png)

## Architecture

Modular Python application following Clean Architecture, SOLID principles, and Design Patterns

![UI](docs/Architecture-Overview.png)

### Components

- **pyjarvis_shared**: Shared types, messages, and centralized configuration
- **pyjarvis_core**: Core domain logic (text analysis, TTS processors, audio processing, animations)
- **pyjarvis_service**: Service layer for text-audio processing (TCP IPC)
- **pyjarvis_cli**: CLI application to send text to service
- **pyjarvis_ui**: Desktop UI with animated robot face (Pygame)
- **pyjarvis_llama**: LLM integration with speech recognition (Ollama + RealtimeSTT)

### Components Relationship

![Architecture](docs/architecture.png)

## Requirements

- Python 3.10+
- FFmpeg (for MP3 processing) — see the "Install FFmpeg" section below
- Optional: Ollama (for LLM features)
- See `requirements.txt` for all dependencies

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Full architecture (recommended)

1. Start the service in terminal 1:

```bash
python -m pyjarvis_service
```

2. Start the UI in terminal 2:

```bash
python -m pyjarvis_ui
```

3. Send text from terminal 3:

```bash
python -m pyjarvis_cli "Hello, I am Jarvis"
```

### LLM + Speech Recognition (optional)

1. Start Ollama (if using local LLM):

```bash
ollama serve
```

2. Start the service and UI as above.
3. Start the LLM CLI in another terminal:

```bash
python -m pyjarvis_llama
```

In the LLM CLI you can:
- Type messages and press Enter for text input
- Use `/m` to record audio from microphone (press Enter to stop)
- Use `/lang <code>` to change recognition language
- Use `/persona <name>` to change AI persona

### Standalone UI

The UI can run standalone but is much more useful connected to the service:

```bash
python -m pyjarvis_ui
```


## Project Structure

Top-level layout (canonical):

```
pyJarvis/
├── README.md
├── requirements.txt
├── pyjarvis_shared/
├── pyjarvis_core/
├── pyjarvis_service/
├── pyjarvis_cli/
├── pyjarvis_ui/
├── pyjarvis_llama/
├── audio/
├── assets/
├── models/
└── docs/
```

- `pyjarvis_shared/`: AppConfig, message types and shared utilities
- `pyjarvis_core/`: TextAnalyzer, AnimationController, TTS factory and processors
- `pyjarvis_service/`: IPC server and TextProcessor orchestration
- `pyjarvis_ui/`: Pygame-based UI (FaceRenderer, AudioPlayer, ServiceClient)
- `pyjarvis_llama/`: LLM CLI, Ollama client, STT recorder, personas

## Features

- Animated robot face with lip-sync and emotion-driven effects
- Multiple TTS engines (Edge-TTS default, gTTS available)
- STT integration via RealtimeSTT / Whisper models
- LLM support via Ollama and configurable AI personas
- TCP-based IPC; UI registers for broadcast updates from service

## Configuration

All runtime configuration is centralized in `pyjarvis_shared/config.py` (AppConfig):
- TTS processor selection (`tts_processor`)
- Audio output directory and auto-delete behavior
- Edge-TTS voice mapping (`edge_tts_voices`)
- STT model and language
- Ollama base URL and model


## Text-to-Speech (Quick notes)

- Edge-TTS (Microsoft) is the default high-quality engine. Voice mapping is configurable by language.
- gTTS (Google) is supported as a fallback (requires internet and FFmpeg for MP3→WAV conversion).


## Install FFmpeg

PyJarvis uses FFmpeg (via `pydub`) to convert MP3 audio (e.g., produced by gTTS) to WAV.

Windows options:

- Chocolatey (recommended):

```powershell
choco install ffmpeg
```

- winget:

```powershell
winget install ffmpeg
```

- Manual download:
  1. Download from: https://www.gyan.dev/ffmpeg/builds/
  2. Extract the ZIP and add the `bin` folder to your PATH (e.g. `C:\ffmpeg\bin`).
  3. Restart terminal.

Verify installation:

```powershell
ffmpeg -version
```

If you prefer not to install FFmpeg, use a TTS engine that emits WAV directly.


## Edge-TTS Voice Mapping

Configure voices in `pyjarvis_shared/config.py` (example):

```python
from pyjarvis_shared import AppConfig
config = AppConfig()
config.edge_tts_voices = {
    "pt-br": "pt-BR-HumbertoNeural",
    "pt": "pt-BR-FranciscaNeural",
    "en": "en-US-AriaNeural",
    "en-us": "en-US-GuyNeural",
    "es": "es-ES-ElviraNeural",
    "es-es": "es-ES-ElviraNeural",
    "es-mx": "es-MX-DaliaNeural",
    "es-ar": "es-AR-ElenaNeural"
}
```

### Available Voices

### Portuguese (pt-BR) example voices
- `pt-BR-FranciscaNeural` - female (padrão)
- `pt-BR-HumbertoNeural` - male
- `pt-BR-AntonioNeural` - male
- `pt-BR-BrendaNeural` - female
- `pt-BR-DonatoNeural` - male
- `pt-BR-ElzaNeural` - female
- `pt-BR-FabioNeural` - male
- `pt-BR-GiovannaNeural` - female
- `pt-BR-JulioNeural` - male
- `pt-BR-LeilaNeural` - female
- `pt-BR-LeticiaNeural` - female
- `pt-BR-ManuelaNeural` - female
- `pt-BR-NicolauNeural` - male
- `pt-BR-ThalitaNeural` - female
- `pt-BR-ValerioNeural` - male
- `pt-BR-YaraNeural` - female

### English (en-US) example voices
- `en-US-AriaNeural` - female (padrão)
- `en-US-GuyNeural` - male
- `en-US-JennyNeural` - female
- `en-US-AmberNeural` - female
- `en-US-AnaNeural` - female (child)
- `en-US-AshleyNeural` - female
- `en-US-BrandonNeural` - male
- `en-US-ChristopherNeural` - male
- `en-US-CoraNeural` - female
- `en-US-ElizabethNeural` - female
- `en-US-EricNeural` - male
- `en-US-JacobNeural` - male
- `en-US-JaneNeural` - female
- `en-US-JasonNeural` - male
- `en-US-MichelleNeural` - female
- `en-US-MonicaNeural` - female
- `en-US-NancyNeural` - female
- `en-US-RogerNeural` - male
- `en-US-SaraNeural` - female
- `en-US-TonyNeural` - male

### Spanish (es-ES) example voices
- `es-ES-ElviraNeural` - female (padrão, Bright, Clear)
- `es-ES-AlvaroNeural` - male (Confident, Animated)
- `es-ES-AbrilNeural` - female
- `es-ES-ArabellaMultilingualNeural` - female (Cheerful, Friendly, Casual, Warm, Pleasant)
- `es-ES-ArnauNeural` - male
- `es-ES-DarioNeural` - male
- `es-ES-EliasNeural` - male
- `es-ES-EstrellaNeural` - female
- `es-ES-IreneNeural` - female (Curious, Cheerful)
- `es-ES-IsidoraMultilingualNeural` - female (Cheerful, Friendly, Warm, Casual)
- `es-ES-LaiaNeural` - female
- `es-ES-LiaNeural` - female (Animated, Bright)
- `es-ES-NilNeural` - male
- `es-ES-SaulNeural` - male
- `es-ES-TeoNeural` - male
- `es-ES-TrianaNeural` - female
- `es-ES-VeraNeural` - female
- `es-ES-XimenaNeural` - female

### Spanish (es-MX) example voices
- `es-MX-DaliaNeural` - female (padrão)
- `es-MX-DaliaMultilingualNeural` - female
- `es-MX-BeatrizNeural` - female
- `es-MX-CandelaNeural` - female
- `es-MX-CarlotaNeural` - female
- `es-MX-CecilioNeural` - male
- `es-MX-GerardoNeural` - male
- `es-MX-JorgeNeural` - male
- `es-MX-JorgeMultilingualNeural` - male
- `es-MX-LarissaNeural` - female
- `es-MX-LibertoNeural` - male
- `es-MX-LucianoNeural` - male
- `es-MX-MarinaNeural` - female
- `es-MX-NuriaNeural` - female
- `es-MX-PelayoNeural` - male
- `es-MX-RenataNeural` - female
- `es-MX-YagoNeural` - male

### Spanish (es-AR) example voices
- `es-AR-ElenaNeural` - female (Bright, Clear)
- `es-AR-TomasNeural` - male

### Spanish (es-CO) example voices
- `es-CO-SalomeNeural` - female
- `es-CO-GonzaloNeural` - male

### Other Spanish regional voices
- `es-CL-CatalinaNeural` - female (Chile)
- `es-CL-LorenzoNeural` - male (Chile)
- `es-PE-AlexNeural` - male (Peru)
- `es-PE-CamilaNeural` - female (Peru)
- `es-US-AlonsoNeural` - male (US Spanish)
- `es-US-PalomaNeural` - female (US Spanish)
- `es-UY-MateoNeural` - male (Uruguay)
- `es-UY-ValentinaNeural` - female (Uruguay)
- `es-VE-PaolaNeural` - female (Venezuela)
- `es-VE-SebastianNeural` - male (Venezuela)

For a complete list of all available Spanish voices, run:
```bash
edge-tts --list-voices | grep "^es-"
```

## Testing / Verification

Quick test flow:

1. Start the service: `python -m pyjarvis_service` (should listen on 127.0.0.1:8888)
2. Start the UI: `python -m pyjarvis_ui` (window should open and attempt to connect)
3. Send text via CLI: `python -m pyjarvis_cli "Hello, I am Jarvis"`

Expected: service processes text, generates an audio file in `./audio/`, broadcasts a VoiceProcessingUpdate, and the UI plays the audio while animating the face.

Testing checklist (manual):
- [ ] Service starts without errors
- [ ] UI connects to service
- [ ] CLI can send text
- [ ] Audio is generated and played
- [ ] Robot face animates during speech
- [ ] Audio files are cleaned up (if configured)
- [ ] LLM CLI connects to Ollama (if used)
- [ ] Speech recognition works (`/m` in LLM CLI)