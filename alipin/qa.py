"""Hugging Face backed question-answering skill."""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
import json
import os
import re
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus, unquote, urlparse, parse_qs
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class AnswerResult:
    """Result from the question-answering skill."""

    answer: str
    used_web: bool
    sources: tuple[str, ...] = ()


@dataclass(frozen=True)
class SearchResult:
    """A lightweight web-search result."""

    title: str
    url: str
    snippet: str


class TextGenerator(Protocol):
    """Protocol for model clients that can generate answers."""

    def generate(self, prompt: str) -> str:
        """Generate text from a prompt."""


class WebSearcher(Protocol):
    """Protocol for search clients that can return web snippets."""

    def search(self, query: str, *, limit: int = 3) -> tuple[SearchResult, ...]:
        """Search the web and return a small set of results."""


class HuggingFaceTextGenerator:
    """Minimal Hugging Face Inference API text-generation client."""

    def __init__(self, model: str, token_env: str = "HUGGINGFACE_API_TOKEN", timeout_seconds: int = 30) -> None:
        self.model = model
        self.token_env = token_env
        self.timeout_seconds = timeout_seconds

    def generate(self, prompt: str) -> str:
        token = os.getenv(self.token_env)
        if not token:
            return (
                f"Set {self.token_env} to a Hugging Face access token so I can ask the open-source "
                f"model {self.model}."
            )

        request = Request(
            f"https://api-inference.huggingface.co/models/{self.model}",
            data=json.dumps(
                {
                    "inputs": prompt,
                    "parameters": {"max_new_tokens": 220, "return_full_text": False},
                    "options": {"wait_for_model": True},
                }
            ).encode("utf-8"),
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310 - fixed HTTPS API endpoint.
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            return f"Hugging Face returned HTTP {exc.code} for model {self.model}."
        except (URLError, TimeoutError) as exc:
            return f"I could not reach Hugging Face right now: {exc}."

        if isinstance(payload, list) and payload and isinstance(payload[0], dict):
            generated = payload[0].get("generated_text", "")
            return str(generated).strip() or "The model returned an empty answer."
        if isinstance(payload, dict) and "error" in payload:
            return f"Hugging Face error: {payload['error']}"
        return "I could not understand the Hugging Face response."


class _DuckDuckGoHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.results: list[SearchResult] = []
        self._in_link = False
        self._in_snippet = False
        self._current_url = ""
        self._current_title: list[str] = []
        self._current_snippet: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        css_class = attrs_dict.get("class", "") or ""
        if tag == "a" and "result-link" in css_class:
            self._in_link = True
            self._current_url = _clean_duckduckgo_url(attrs_dict.get("href", "") or "")
            self._current_title = []
        if tag == "a" and "result-snippet" in css_class:
            self._in_snippet = True
            self._current_snippet = []

    def handle_data(self, data: str) -> None:
        if self._in_link:
            self._current_title.append(data)
        if self._in_snippet:
            self._current_snippet.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._in_link:
            self._in_link = False
            title = " ".join(part.strip() for part in self._current_title if part.strip())
            if title and self._current_url:
                self.results.append(SearchResult(title=title, url=self._current_url, snippet=""))
        if tag == "a" and self._in_snippet:
            self._in_snippet = False
            snippet = " ".join(part.strip() for part in self._current_snippet if part.strip())
            if snippet and self.results:
                latest = self.results[-1]
                self.results[-1] = SearchResult(latest.title, latest.url, snippet)


class DuckDuckGoSearcher:
    """Small dependency-free web search client using DuckDuckGo's HTML endpoint."""

    def __init__(self, timeout_seconds: int = 15) -> None:
        self.timeout_seconds = timeout_seconds

    def search(self, query: str, *, limit: int = 3) -> tuple[SearchResult, ...]:
        request = Request(
            f"https://html.duckduckgo.com/html/?q={quote_plus(query)}",
            headers={"User-Agent": "Alipin/0.1 (+https://example.invalid)"},
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310 - fixed HTTPS search endpoint.
            html = response.read().decode("utf-8", errors="replace")
        parser = _DuckDuckGoHTMLParser()
        parser.feed(html)
        return tuple(parser.results[:limit])


def _clean_duckduckgo_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc.endswith("duckduckgo.com") and parsed.path == "/l/":
        uddg = parse_qs(parsed.query).get("uddg")
        if uddg:
            return unquote(uddg[0])
    return url


def _needs_web(question: str) -> bool:
    return bool(re.search(r"\b(latest|current|today|news|search|internet|web|recent|now)\b", question.lower()))


def _build_prompt(question: str, search_results: tuple[SearchResult, ...]) -> str:
    context = "\n".join(
        f"[{index}] {result.title}\nURL: {result.url}\nSnippet: {result.snippet}"
        for index, result in enumerate(search_results, start=1)
    )
    if context:
        return (
            "You are Alipin, a helpful personal assistant. Answer the user's question using the web results below. "
            "If the results are insufficient, say what is missing. Keep the answer concise and include source numbers.\n\n"
            f"Web results:\n{context}\n\nQuestion: {question}\nAnswer:"
        )
    return (
        "You are Alipin, a helpful personal assistant. Answer the user's question clearly and concisely. "
        "If you are unsure or the question needs current facts, say that web search is needed.\n\n"
        f"Question: {question}\nAnswer:"
    )


def answer_question(
    question: str,
    generator: TextGenerator,
    searcher: WebSearcher | None = None,
    *,
    force_web: bool = False,
) -> AnswerResult:
    """Answer a question with an open-source Hugging Face model and optional web context."""
    cleaned = question.strip()
    if not cleaned:
        return AnswerResult("Please ask a question first.", used_web=False)

    used_web = force_web or _needs_web(cleaned)
    search_results: tuple[SearchResult, ...] = ()
    if used_web and searcher is not None:
        try:
            search_results = searcher.search(cleaned, limit=3)
        except (HTTPError, URLError, TimeoutError) as exc:
            return AnswerResult(f"I could not search the web right now: {exc}.", used_web=True)

    answer = generator.generate(_build_prompt(cleaned, search_results))
    sources = tuple(result.url for result in search_results)
    if sources:
        answer = f"{answer}\n\nSources:\n" + "\n".join(f"- {url}" for url in sources)
    return AnswerResult(answer=answer, used_web=used_web, sources=sources)
