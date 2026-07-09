# Assistant Skills

This file defines the initial capability map for the AI assistant. Each skill should eventually become a small, testable module with a clear trigger, inputs, outputs, permissions, and safety limits.

## 1. Wake Name Listener

**Goal:** Continuously listen for the assistant's name without sending all background audio to a cloud service.

**Initial approach:**
- Use a lightweight on-device wake-word detector.
- After the wake name is detected, temporarily enable speech-to-text for the user's command.
- Keep the wake name configurable so it can change without rewriting the assistant.

**Candidate technology:**
- `openWakeWord` for wake-word detection and custom wake-word training.

**Safety and privacy notes:**
- Always-on listening should stay local by default.
- Store only explicit user commands or notes, never continuous background audio.

## 2. Speech-to-Text

**Goal:** Convert the spoken command after the wake name into text.

**Initial approach:**
- Use a Hugging Face speech-recognition model through the installed Hugging Face integration or a local runtime.
- Start with a fast model, then upgrade if accuracy is not good enough.

**Candidate models:**
- `distil-whisper/distil-large-v3.5` for a strong speed/accuracy balance.
- `openai/whisper-large-v3-turbo` when higher accuracy is more important than local resource usage.
- Smaller Whisper or Distil-Whisper variants for low-power devices.

## 3. App Launcher

**Goal:** Open local applications by voice command.

**Initial approach:**
- Maintain an allowlist of apps and commands.
- Translate commands like "open browser" or "open notes" into operating-system launch actions.
- Implemented first in `alipin.apps` with dry-run mode enabled by default.

**Safety notes:**
- Do not execute arbitrary shell commands from raw model output.
- Require explicit allowlisted app names or user confirmation for sensitive apps.

## 4. Web Search and Current Q&A

**Goal:** Search the web and answer questions with up-to-date information.

**Initial approach:**
- Route time-sensitive questions to a web-search tool.
- Summarize results and cite sources.
- Use the language model to synthesize, not invent, current facts.

**Safety notes:**
- Prefer authoritative sources for medical, legal, financial, or security topics.
- Include source links for answers based on web results.

## 5. Note Taking

**Goal:** Capture spontaneous ideas quickly by voice.

**Initial approach:**
- Commands such as "write this down", "take a note", or "remember this" create a timestamped Markdown note.
- Store notes in a local `notes/` directory that can be synced later if desired.
- Implemented first in `alipin.notes` and reachable through the text-first CLI.

**Safety notes:**
- Confirm before saving sensitive information.
- Keep notes out of version control unless the user explicitly chooses to publish them.

## 6. Intent Router

**Goal:** Decide which skill should handle a transcribed command.

**Initial approach:**
- Use simple deterministic rules first for learning and safety.
- Add a model-based router later for ambiguous commands.
- Keep the router auditable by logging the selected skill and reason.
- Implemented first in `alipin.router` with phrase-based routing for notes, app launching, web search, Q&A, and fallback conversation.

## 7. Conversation and Answer Generation

**Goal:** Provide natural answers after a command is understood.

**Initial approach:**
- Use a local or hosted instruction-tuned model.
- Keep tool calls structured as JSON-like actions so the assistant can validate them before execution.

**Candidate Hugging Face model direction:**
- Use a small instruct/tool-calling model for local experiments.
- Use a stronger hosted model when current web synthesis or complex reasoning is required.
