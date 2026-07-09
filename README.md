# Alipin AI Assistant

Alipin is an early-stage learning project for building a personal AI assistant that can listen for a wake name, understand spoken commands, open allowed apps, search the web for current answers, and save spontaneous notes.

## Current repository state

This iteration adds a text-first command-line prototype so the assistant flow can be tried before audio, wake-word detection, or hosted model calls are added:

- `alipin/router.py` routes text commands with deterministic rules.
- `alipin/notes.py` saves timestamped Markdown notes in `notes/`.
- `alipin/apps.py` supports an allowlisted app launcher with dry-run mode enabled by default.
- `alipin/cli.py` exposes the prototype through the `alipin` command.
- `setup.sh` creates a virtual environment and local `alipin` command wrapper.
- `tests/` covers the initial router and note-taking behavior.

The foundational documentation remains in place:

- `AGENTS.md` defines repository guidance for future AI coding agents.
- `SKILLS.md` defines the assistant capabilities and safety boundaries.
- `docs/THINKING_PROCESS.md` explains the architecture decisions and model research.
- `notes/` is reserved for local note-taking output and should not contain committed personal notes.

## Try it locally

From the repository root, run:

```bash
./setup.sh
source .venv/bin/activate
alipin take a note remember to test the prototype
alipin open browser
alipin "what is Alipin?"
```

By default, app launching is a dry run. To actually launch allowlisted apps, pass `--launch-apps`:

```bash
alipin --launch-apps open browser
```

## Planned architecture

```text
Wake name listener
        ↓
Speech-to-text
        ↓
Intent router
        ↓
Assistant skill: notes, app launcher, web search, Q&A, or conversation
        ↓
Response generation
```

## Learning focus

The project intentionally starts with simple, inspectable pieces. Future iterations should prefer deterministic logic and clear logs before adding more autonomous model behavior.
