# AGENTS.md

This file provides context for AI agents working on Vibe Coding Helper codebase.

## Build / Lint / Test Commands

```bash
pytest                              # Run all tests
pytest tests/unit/test_config.py::test_load_config  # Single test
pytest --cov=src/vibe --cov-report=html  # Coverage report
ruff check src/vibe                 # Lint
ruff format src/vibe                # Format
mypy src/vibe                       # Type check
```

## Code Style Guidelines

### Import Order
```python
from __future__ import annotations
# 1. Standard library
import asyncio
from pathlib import Path
from typing import TYPE_CHECKING
# 2. Third party
from pydantic import BaseModel
# 3. Local imports
from vibe.core.config import Config
# 4. TYPE_CHECKING block for circular imports
if TYPE_CHECKING:
    from vibe.providers.base import AIProvider
```

### Naming Conventions
- **Classes**: `PascalCase` (e.g., `AIProvider`, `ContextManager`)
- **Functions/Methods**: `snake_case` (e.g., `load_config`, `generate_response`)
- **Constants**: `SCREAMING_SNAKE_CASE` (e.g., `DEFAULT_MODEL`, `MAX_TOKENS`)
- **Private**: Underscore prefix (e.g., `_internal_helper`)

### Type Hints
All function signatures must have explicit type hints:
```python
def load_config(path: Path | None = None) -> VibeConfig:
    """Load config from file."""
    pass
async def generate(messages: list[Message]) -> Response:
    """Generate AI response."""
    pass
```

### Docstrings
Use Google style docstrings for public APIs:
```python
def generate_prd(description: str, context: ProjectContext) -> str:
    """Generate PRD document.

    Args:
        description: Project description.
        context: Project context (TECH_STACK, RULES included).

    Returns:
        Generated PRD markdown string.

    Raises:
        ProviderError: When API call fails.
        ConfigError: When config is invalid.
    """
```

## Architecture Patterns

### Layer Separation
```
CLI Layer (cli/) → Core Layer (core/) → Provider/Handler Layer (providers/, handlers/)
```

### Dependency Injection
```python
class Workflow:
    def __init__(self, provider: AIProvider, file_handler: FileHandler):
        self.provider = provider
        self.file_handler = file_handler
```

### Error Handling
```python
class VibeError(Exception):
    """Base exception class."""
    pass
class ConfigError(VibeError):
    """Config-related error."""
    pass
def load_config(path: Path) -> Config:
    if not path.exists():
        raise ConfigError(f"Config not found: {path}")
```

## File Structure

```
src/vibe/
├── cli/           # CLI commands, UI components
├── core/          # Controller, context, state, workflow
├── providers/     # AI provider implementations
├── handlers/      # File, git, parser handlers
└── verifiers/     # Code verification by language
tests/
├── unit/          # Unit tests (mocked dependencies)
├── integration/   # Integration tests
└── fixtures/      # Shared test fixtures
```

## Configuration

Use Pydantic for all config/state schemas:
```python
class VibeConfig(BaseModel):
    project_name: str
    project_type: Literal["backend", "frontend", "fullstack"] = "backend"
    model_config = ConfigDict(extra="forbid")
```

Environment variable priority: CLI args → Environment vars → Project config (.vibe/config.yaml) → Global config (~/.config/vibe/config.yaml) → Defaults

## Testing

### Test Naming
```python
def test_load_config_returns_default_when_file_missing():
    pass
async def test_stream_yields_chunks_correctly():
    pass
```

### Fixtures
```python
@pytest.fixture
def mock_provider():
    """Mocked AI Provider."""
    ...
@pytest.fixture
def temp_project(tmp_path):
    """Temporary project directory."""
    ...
```

## Async/Concurrency

All Provider methods are async. Use `asyncio.run()` in CLI entrypoints:
```python
def main():
    asyncio.run(async_main())
```

Use semaphores for rate limiting:
```python
semaphore = asyncio.Semaphore(3)
async def rate_limited_call():
    async with semaphore:
        return await provider.generate(messages)
```

## Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Example:
```
feat: vibe init command implementation

- TECH_STACK.md generation logic
- RULES.md template application
- Interactive interview flow

Closes #12
```

## Security

- Never hardcode API keys. Use environment variables.
- Block access outside project directory (validate with Path.resolve())
- Detect and warn about SQL Injection, XSS patterns in generated code
- Add `.env`, `*.key` to .gitignore

## Tool Configuration

- **Line length**: 100 chars (ruff)
- **Python version**: 3.11+
- **Type checking**: mypy strict mode
- **Test runner**: pytest with asyncio_mode=auto
