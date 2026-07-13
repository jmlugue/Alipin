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


## Iteration 2: Make typed commands useful before speech

### What changed
The text-first prototype now performs the three requested non-speech actions:

1. Question commands are handled by `alipin.qa`, a small local answer skill for identity, capability, date/time, and safe arithmetic questions.
2. App launching is narrowed to Discord as the first allowlisted application. Launching still dry-runs by default unless `--launch-apps` is passed.
3. Note commands now create timestamped `.txt` files under `D:/AI Notes` by default, and the folder is created automatically if missing.

### Why keep Q&A small first
A deterministic local answer skill makes the command path runnable without introducing API keys, model hosting, or web-search reliability issues. Broader knowledge and current-fact answers should be added later through a sourced web-search or model-backed Q&A layer.

### Safety decisions
- The app launcher still uses a static allowlist, currently only Discord.
- The Q&A math helper evaluates only a small safe arithmetic AST, not arbitrary Python code.
- Note files are plain text and remain outside version control by default when saved to the configured Data drive folder.


## Iteration 3: Hugging Face model-backed Q&A with web context

### What changed
Question answering moved away from the hard-coded local answer table. The assistant now builds prompts for an open-source Hugging Face text-generation model and can optionally gather DuckDuckGo search snippets for current or explicit search questions.

### Why use the Hugging Face Inference API first
Using the hosted inference API keeps this iteration small and avoids forcing every learner to install local model runtimes immediately. The configured model can be swapped with `--hf-model`, while the access token is read from `HUGGINGFACE_API_TOKEN` by default so no secrets are committed.

### Web-search decision
The CLI now treats explicit search commands as Q&A with forced web context. Normal questions automatically search only when they look time-sensitive, such as questions containing "latest", "current", "today", "news", "recent", or "internet".

### Safety decisions
- Hugging Face tokens are read only from environment variables.
- Search results are summarized into short prompt context instead of executing anything from the web.
- Answers include source URLs when web snippets were used.


## Iteration 4: Update hosted Q&A endpoint

### What changed
The Hugging Face Q&A client now calls the current Inference Providers router at `https://router.huggingface.co/v1/chat/completions` instead of the older `api-inference.huggingface.co/models/...` text-generation endpoint.

### Why change the endpoint
The previous endpoint failed DNS resolution on the development machine, while `router.huggingface.co` resolved and accepted HTTPS connections. Hugging Face's current Inference Providers documentation also shows the router endpoint for chat-completion workloads.

### Model decision
The default hosted model changed to `openai/gpt-oss-120b:together`, matching Hugging Face's provider-specific model suffix pattern and avoiding automatic fastest-provider routing.

### Safety decisions
- The token remains environment-variable only through `HUGGINGFACE_API_TOKEN`.
- The client still uses only a fixed HTTPS Hugging Face endpoint.
- Web snippets remain prompt context only and are not executed.

### Follow-up: token permission clarity
The client now includes Hugging Face's response body for HTTP errors when available. For HTTP 403 responses, it also points the user to the required `Make calls to Inference Providers` token permission, because plain read tokens can authenticate to the Hub while still being rejected by the Inference Providers router.

### Follow-up: provider routing
Using `openai/gpt-oss-120b:fastest` routed one request to Cerebras, which returned a Cloudflare 1010 HTML access-denied page. Pinning Groq produced the same class of downstream Cloudflare block. The default now pins the model to Together with `openai/gpt-oss-120b:together`, Alipin falls back through several other providers for the same model, and HTML error pages are summarized before being shown in the terminal.


## Iteration 5: Broader web-context routing

### What changed
The Q&A skill now classifies whether a question needs web context instead of only checking a short keyword list. It routes current, location-specific, recommendation-oriented, comparative, availability, pricing, weather, release, download, schedule, score, and explicit search-style questions through DuckDuckGo snippets before asking the hosted model.

### Why keep this classifier local
A local classifier is still easy to inspect and test, and it avoids spending a model call just to decide whether to search. This is a practical middle step before adding a model-based planner or a full browser/search API.

### Current limitation
The search backend is still DuckDuckGo's HTML endpoint and passes only a few snippets to the model. It can improve search triggering, but it is not yet a full browser, crawler, or source-quality ranking system.


## Iteration 6: Open-source search API backend

### What changed
The web-search backend now uses SearXNG's JSON search API first. The CLI accepts `--searxng-url`, and the same setting can be supplied through the `SEARXNG_BASE_URL` environment variable. If SearXNG is unavailable or the instance has JSON disabled, Alipin falls back to the previous DuckDuckGo HTML search helper.

### Why SearXNG
SearXNG is open source, supports a simple `/search?q=...&format=json` HTTP API, and can be self-hosted. This keeps the assistant aligned with the project goal of understandable, inspectable components without introducing a paid proprietary search key.

### Current limitation
Public SearXNG instances often rate-limit requests or disable JSON output. For reliable use, the best next step is to self-host a small private SearXNG instance and set `SEARXNG_BASE_URL` to that URL.


## Iteration 7: Optional SerpAPI backend

### What changed
Alipin now supports SerpAPI as an optional hosted search backend. Users can select it with `--search-provider serpapi` and provide the key through `SERPAPI_API_KEY`.

### Why add a hosted option
Public SearXNG instances are inconsistent because many disable JSON output, rate-limit automated requests, or return bot-check pages. SerpAPI is not open source, but it provides a stable Google Search API shape with `organic_results`, `title`, `link`, and `snippet` fields, which makes the assistant's web context much more reliable.

### Safety decisions
- SerpAPI keys are read only from environment variables.
- SearXNG remains the default to preserve the open-source path.
- DuckDuckGo remains a no-key fallback for local experimentation.
