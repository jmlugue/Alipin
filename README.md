# Alipin AI Assistant

Alipin is an early-stage learning project for building a personal AI assistant that can listen for a wake name, understand spoken commands, open allowed apps, search the web for current answers, and save spontaneous notes.

## Current repository state

This first iteration creates the planning and documentation structure before implementation:

- `AGENTS.md` defines repository guidance for future AI coding agents.
- `SKILLS.md` defines the assistant capabilities and safety boundaries.
- `docs/THINKING_PROCESS.md` explains the architecture decisions and model research.
- `notes/` is reserved for local note-taking output and should not contain committed personal notes.

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
