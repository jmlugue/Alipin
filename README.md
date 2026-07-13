# Alipin AI Assistant

Alipin is an early-stage learning project for building a personal AI assistant that can listen for a wake name, understand spoken commands, open allowed apps, search the web for current answers, and save spontaneous notes.

## Current repository state

This iteration adds a text-first command-line prototype so the assistant flow can be tried before audio, wake-word detection, or speech components are added:

- `alipin/router.py` routes text commands with deterministic rules.
- `alipin/notes.py` saves timestamped text notes in `D:/AI Notes` by default.
- `alipin/apps.py` supports a Discord-only allowlisted app launcher with dry-run mode enabled by default.
- `alipin/cli.py` exposes the prototype through the `alipin` command, uses a Hugging Face chat model for Q&A, and can add web-search context for current questions.
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

Q&A uses Hugging Face Inference Providers with the OpenAI-compatible chat completions endpoint and the `openai/gpt-oss-120b:together` model by default. Set `HUGGINGFACE_API_TOKEN` before asking questions, or pass `--hf-token-env` if you store the token in a different environment variable. The token must allow calls to Hugging Face Inference Providers. If the selected provider is unavailable, Alipin tries several other providers for the same model. Questions that look current, location-specific, comparative, recommendation-oriented, or explicitly search-oriented automatically receive web-search snippets as model context. Explicit search commands such as `alipin search for Discord download` force web context. Use `--no-web` to disable web search.

Web search uses SearXNG's open-source JSON API by default. To use your own SearXNG instance, set `SEARXNG_BASE_URL` or pass `--searxng-url`:

```bash
export SEARXNG_BASE_URL=https://your-searxng.example
alipin "search for best local speech to text models"
```

If the SearXNG instance is unavailable or has JSON disabled, Alipin falls back to the older DuckDuckGo HTML search helper. Use `--search-provider duckduckgo` to force the fallback searcher.

For more reliable hosted search, Alipin can use SerpAPI. Set `SERPAPI_API_KEY`, then choose the SerpAPI provider:

```bash
export SERPAPI_API_KEY=your_serpapi_key_here
alipin --search-provider serpapi "search for Python 3.14 release notes"
```

On Windows PowerShell:

```powershell
[Environment]::SetEnvironmentVariable("SERPAPI_API_KEY", "your_serpapi_key_here", "User")
$env:SERPAPI_API_KEY = [Environment]::GetEnvironmentVariable("SERPAPI_API_KEY", "User")
python -m alipin.cli --search-provider serpapi "search for Python 3.14 release notes"
```
