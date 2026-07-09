# AGENTS.md

This repository contains the learning-first implementation of a personal voice AI assistant.

## Project goal
Build an assistant that can:
- Listen locally for a wake name before recording a command.
- Transcribe spoken commands into text.
- Route commands to tools such as app launching, web search, question answering, and note taking.
- Keep decisions documented so each iteration is easy to study.

## Working conventions
- Prefer small, understandable changes over large rewrites.
- Keep implementation notes in `docs/THINKING_PROCESS.md` updated whenever architecture or model choices change.
- Keep capability definitions in `SKILLS.md` updated whenever a new assistant skill is added or changed.
- Favor local/private processing for always-on audio components where practical.
- Do not commit secrets, API keys, local notes, or generated audio recordings.

## Suggested validation for future iterations
- Run any available test suite before committing.
- If no executable code exists yet, validate Markdown structure and links manually.
- For web-application UI changes, capture a screenshot of the visible change.

## Pull request notes
PR descriptions should summarize:
- What changed.
- Why the change was made.
- What was tested or why tests were not applicable.
