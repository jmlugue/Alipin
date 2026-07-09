# Thinking Process and Architecture Log

This document records the technical decisions behind the personal voice AI assistant. It should be updated during every meaningful iteration so the project remains useful as a learning resource.

## Iteration 0: Initial structure

### User goal
Create an AI assistant that can wake when called by name, open apps, search the web, answer up-to-date questions, and take spontaneous notes.

### Architectural decision
Use a pipeline instead of one large model doing everything:

1. **Wake name detection** listens locally for the assistant's name.
2. **Speech-to-text** transcribes only after the wake name is detected.
3. **Intent routing** decides whether the command is for app launching, web search, question answering, note taking, or normal conversation.
4. **Skill execution** runs the selected capability using safe, narrow permissions.
5. **Response generation** explains what happened or answers the question.

This structure is easier to test and safer than letting a language model directly control the computer.

### Why the wake detector should be separate
A wake detector is small and can run continuously. A speech-recognition model is larger and should only run after the wake name is detected. Hugging Face's voice assistant learning material describes this split: use a lightweight on-device audio classification model for wake-word detection, then start the larger speech-recognition model only when needed.

### Initial model research
Current Hugging Face research suggests these starting points:

- **Wake word:** `openWakeWord` because it is an open-source wake-word library with pretrained models and custom wake-word support.
- **Speech-to-text:** `distil-whisper/distil-large-v3.5` because Distil-Whisper is designed as a smaller and faster Whisper-style model while retaining strong accuracy. Hugging Face model listings also show `openai/whisper-large-v3-turbo` as a popular automatic speech-recognition option.
- **Language model / tool use:** start with a small instruct or tool-calling model for local learning, then evaluate stronger hosted Hugging Face models when tool reliability becomes important.

### Why not choose one final model yet
The best model depends on hardware, latency needs, privacy expectations, language support, and whether the Hugging Face plugin will run models locally or through hosted inference. This repository starts by documenting the required components and candidate models before locking into one implementation.

### Skill design decisions
The initial `SKILLS.md` file describes each assistant capability as a module with goals, inputs, outputs, and safety limits. This makes future implementation easier because each skill can be built and tested independently.

### Safety decisions
- Always-on listening should remain local by default.
- App launching should use an allowlist instead of arbitrary command execution.
- Current Q&A should browse/search and cite sources rather than relying on stale model memory.
- Notes should be saved locally and excluded from version control unless explicitly published.

## Next recommended iteration

1. Create a minimal command-line prototype.
2. Add a local notes skill that writes timestamped Markdown files.
3. Add a deterministic intent router.
4. Add a mock app-launcher allowlist.
5. Add speech-to-text and wake-word detection after the text-command flow works.

## Sources consulted on July 9, 2026

- Hugging Face Audio Course: voice assistant architecture and wake-word/speech-recognition split.
- Hugging Face Distil-Whisper project and model pages for speech-to-text candidates.
- Hugging Face automatic speech-recognition model listings for current ASR model options.
- openWakeWord project information for wake-word detection.

## Iteration 1: Text-first runnable prototype

### What changed
A minimal Python command-line assistant was added before any audio components. This keeps the first runnable version easy to inspect and test:

1. `alipin.router` maps command text to an intent with deterministic phrase matching.
2. `alipin.notes` writes local timestamped Markdown notes.
3. `alipin.apps` checks app requests against a static allowlist and dry-runs launches by default.
4. `alipin.cli` connects the router and skills behind an `alipin` command.
5. `setup.sh` creates a virtual environment and local command wrapper without needing network access.

### Why start without voice input
The planned voice assistant still needs wake-word detection and speech-to-text, but the safest learning path is to validate the command pipeline with typed input first. Once routing, note saving, app allowlists, and responses are understandable, audio can feed transcribed text into the same `handle_command` function.

### Safety decisions
- App launching remains dry-run by default, even for allowlisted apps.
- App commands come from static configuration instead of model-generated shell commands.
- Notes are still stored under `notes/`, which is protected from committing personal note files by its `.gitignore`.

### Next recommended iteration

1. Add a simple configuration file for wake name, notes directory, and app allowlist.
2. Add structured logs that record selected intent and reason.
3. Add a real web-search implementation for current Q&A.
4. Add speech-to-text only after the text command path is stable.
