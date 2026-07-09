# Alipin AI Assistant

Alipin is an early-stage learning project for building a personal AI assistant that can listen for a wake name, understand spoken commands, open allowed apps, search the web for current answers, and save spontaneous notes.

## Current repository state

This iteration adds a text-first command-line prototype so the assistant flow can be tried before audio, wake-word detection, or speech components are added:

- `alipin/router.py` routes text commands with deterministic rules.
- `alipin/notes.py` saves timestamped text notes in `D:/AI Notes` by default.
- `alipin/apps.py` supports a Discord-only allowlisted app launcher with dry-run mode enabled by default.
- `alipin/cli.py` exposes the prototype through the `alipin` command, uses a Hugging Face text-generation model for Q&A, and can add web-search context for current questions.
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
alipin open discord
export HUGGINGFACE_API_TOKEN=your_token_here
alipin "what is Alipin?"
alipin "what is the latest Python release?"
```

By default, app launching is a dry run. To actually launch allowlisted apps, pass `--launch-apps`:

```bash
alipin --launch-apps open discord
```

## Planned architecture

```text
Wake name listener
        ↓
Speech-to-text
        ↓
Intent router
        ↓
Assistant skill: notes, app launcher, Hugging Face Q&A, web search, or conversation
        ↓
Response generation
```

## Learning focus

The project intentionally starts with simple, inspectable pieces. Future iterations should prefer deterministic logic and clear logs before adding more autonomous model behavior.


## Question answering and search

Q&A uses the Hugging Face Inference API with the open-source `HuggingFaceH4/zephyr-7b-beta` model by default. Set `HUGGINGFACE_API_TOKEN` before asking questions, or pass `--hf-token-env` if you store the token in a different environment variable. Questions containing words like "latest", "current", "today", "news", or "internet" automatically receive DuckDuckGo web-search snippets as model context. Explicit search commands such as `alipin search for Discord download` force web context. Use `--no-web` to disable web search.
