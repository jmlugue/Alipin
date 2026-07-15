# Alipin V1

Alipin is a local-first Windows desktop command assistant prototype. V1 proves one narrow behavior: "Hey Alipin" or the window `Listen` button captures a command, then Alipin runs an allowlisted desktop action.

Alipin V1 is not a general AI assistant. It does not answer questions, chat, search the web, summarize pages, browse online, or open arbitrary websites from natural language.

## Supported Commands

- `open Chrome`
- `open Edge`
- `open File Explorer`
- `open Notepad`
- `open VS Code`
- `open Spotify`
- `open Settings`
- `play music`
- `pause music`
- `next song`
- `previous song`
- `play [song name]`

For `play [song name]`, Alipin opens Spotify search for that song. It does not use the Spotify Web API or autoplay.

Unknown commands return:

```text
That command is not supported yet.
```

## Run

From the repository root:

```powershell
py -3.11 -m alipin
```

The installed console script also opens the desktop window:

```powershell
alipin
```

If Vosk or a speech model is not available, the `Listen` button falls back to a typed command dialog.

## Speech Model

Install dependencies from `pyproject.toml`, then download the small English Vosk model into:

```text
models/vosk-model-small-en-us-0.15
```

Alipin auto-detects that local model folder. To use a different model, set:

```powershell
$env:ALIPIN_VOSK_MODEL = "C:\path\to\vosk-model-small-en-us"
```

## Configuration

App aliases and launch commands live in:

```text
config/apps.json
```

Only apps in that file can be opened.

## Tests

```powershell
py -3.11 -m pytest
```

The tests cover app aliases, music controls, Spotify song search, dry-run action execution, and rejection of AI/web-search style prompts.
