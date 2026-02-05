# Vibe Coding Helper Context

## Project Overview
**Vibe Coding Helper** is an interactive CLI tool designed to transform vague ideas into structured documentation and executable code using a document-driven, phase-based workflow. It leverages AI (Claude, Gemini, OpenAI) to guide developers through Initialization, Planning, Design, and Implementation phases, ensuring context is preserved throughout the development lifecycle.

## Key Technologies
- **Language**: Python 3.10+ (3.11+ recommended)
- **Package Manager**: `uv`
- **CLI Framework**: `typer`
- **UI**: `rich`
- **AI Providers**: Anthropic (Claude), Google (Gemini), OpenAI (GPT)

## Building and Running
*Note: This project uses `uv` for dependency management.*

### 1. Install Dependencies
```bash
uv sync
```

### 2. Run CLI
```bash
# Run directly via uv
uv run python -m vibe.main --help

# Or if installed as a tool
vibe --help
```

### 3. Run Tests
```bash
uv run pytest
```

## Development Workflow
The project follows a strict 4-phase workflow. Each phase produces specific "Artifacts" that serve as the AI's long-term memory.

### Phase 0: Initialization (`vibe init`)
- **Goal**: Define project personality and rules.
- **Outputs**: `TECH_STACK.md`, `RULES.md`, `.vibe/config.yaml`.

### Phase 1: Planning (`vibe plan`)
- **Goal**: Concrete requirements from vague ideas.
- **Outputs**: `PRD.md`, `USER_STORIES.md`.

### Phase 2: Design (`vibe design`, `vibe scaffold`)
- **Goal**: Technical architecture and file skeleton.
- **Outputs**: `TREE.md`, `SCHEMA.md`, directory structure, `TODO.md`.

### Phase 3: Implementation (`vibe code`)
- **Goal**: Write code based on the plan and design.
- **Outputs**: Source code, updated `TODO.md`, `CONTEXT.md`.

## Project Structure
```
src/vibe/
├── cli/            # Typer CLI app, commands, and UI (Rich)
├── core/           # Core logic: State, Context, Workflow, Config
├── providers/      # AI Provider implementations (Anthropic, Google, OpenAI)
├── handlers/       # File IO, Git operations, Parsers
├── prompts/        # System and Phase-specific prompts
└── templates/      # Jinja2 templates for generating Artifacts (PRD, RULES, etc.)
```

## Key Artifacts (The "Brain")
The system relies on these specific files to maintain context. **Do not delete or modify these manually unless necessary.**
- **Rules**: `TECH_STACK.md`, `RULES.md`
- **Goal**: `PRD.md`, `USER_STORIES.md`
- **Skeleton**: `TREE.md`, `SCHEMA.md`
- **Memory**: `TODO.md`, `CONTEXT.md`
