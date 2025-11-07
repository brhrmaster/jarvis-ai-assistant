# PyJarvis Test Suite

This directory contains the unit test suite for all PyJarvis modules.

## Structure

The test suite mirrors the application module structure:

```
tests/
├── conftest.py                    # Pytest configuration and shared fixtures
├── pyjarvis_shared/              # Tests for shared types and config
│   ├── test_config.py
│   └── test_messages.py
├── pyjarvis_core/                # Tests for core domain logic
│   ├── test_text_analyzer.py
│   ├── test_tts_factory.py
│   ├── test_animation_controller.py
│   ├── test_audio_buffer.py
│   └── tts_processors/
│       ├── test_base.py
│       ├── test_edge_tts_processor.py
│       └── test_gtts_processor.py
├── pyjarvis_service/             # Tests for service layer
│   ├── test_ipc.py
│   ├── test_processor.py
│   └── test_service.py
├── pyjarvis_cli/                 # Tests for CLI client
│   └── test_client.py
├── pyjarvis_ui/                  # Tests for UI components
│   ├── test_service_client.py
│   ├── test_audio_player.py
│   ├── test_face_renderer.py
│   └── test_app.py
└── pyjarvis_llama/               # Tests for LLM integration
    ├── test_llama_client.py
    ├── test_audio_recorder.py
    ├── test_personas.py
    ├── test_conversation_context.py
    ├── test_recording_queue.py
    └── test_cli.py
```

## Running Tests

### Run all tests:
```bash
pytest
```

### Run tests for a specific module:
```bash
pytest tests/pyjarvis_core/
```

### Run a specific test file:
```bash
pytest tests/pyjarvis_shared/test_config.py
```

### Run a specific test:
```bash
pytest tests/pyjarvis_shared/test_config.py::TestAppConfig::test_app_config_default_values
```

### Run with coverage:
```bash
pytest --cov=pyjarvis_shared --cov=pyjarvis_core --cov-report=html
```

### Run async tests:
```bash
pytest -m asyncio
```

## Test Conventions

- Test files are named `test_*.py`
- Test classes are named `Test*`
- Test functions are named `test_*`
- Use pytest fixtures for common setup/teardown
- Use `@pytest.mark.asyncio` for async tests
- Use `unittest.mock` for mocking dependencies

## Fixtures

Common fixtures available in `conftest.py`:
- `app_config`: Default AppConfig instance
- `mock_audio_config`: Mock AudioConfig instance
- `mock_logger`: Mock logger instance
- `event_loop`: Async event loop for tests

## Writing New Tests

1. Create test files matching the source module structure
2. Import the module/class to test
3. Use fixtures from `conftest.py` when possible
4. Follow the existing test patterns
5. Add appropriate assertions
6. Mock external dependencies (network, file I/O, etc.)

## Requirements

Make sure pytest and pytest-asyncio are installed:
```bash
pip install pytest pytest-asyncio pytest-cov
```

Or install test requirements:
```bash
pip install -r tests/requirements.txt
```


