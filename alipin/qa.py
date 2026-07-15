"""Disabled question-answering module for Alipin V1.

Alipin V1 is command-only. This module remains only so older imports fail closed
instead of reaching an AI model or web search backend.
"""

from __future__ import annotations

from dataclasses import dataclass

from alipin.commands import UNSUPPORTED_MESSAGE


@dataclass(frozen=True)
class AnswerResult:
    """Result from the disabled question-answering skill."""

    answer: str
    used_web: bool
    sources: tuple[str, ...] = ()


class SearchError(Exception):
    """Raised if older code tries to use a search backend."""


class DisabledTextGenerator:
    def __init__(self, *args: object, **kwargs: object) -> None:
        del args, kwargs

    def generate(self, prompt: str) -> str:
        del prompt
        return UNSUPPORTED_MESSAGE


class DisabledSearcher:
    def __init__(self, *args: object, **kwargs: object) -> None:
        del args, kwargs

    def search(self, query: str, *, limit: int = 3) -> tuple[object, ...]:
        del query, limit
        raise SearchError(UNSUPPORTED_MESSAGE)


HuggingFaceTextGenerator = DisabledTextGenerator
DuckDuckGoSearcher = DisabledSearcher
SearXNGSearcher = DisabledSearcher
SerpAPISearcher = DisabledSearcher


def answer_question(*args: object, **kwargs: object) -> AnswerResult:
    """Return unsupported instead of dispatching to an AI model or search backend."""
    del args, kwargs
    return AnswerResult(UNSUPPORTED_MESSAGE, used_web=False)
