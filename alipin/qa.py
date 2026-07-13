"""Hugging Face backed question-answering skill."""

from __future__ import annotations

from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
import json
import os
import re
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus, unquote, urlencode, urlparse, parse_qs
from urllib.request import Request, urlopen

_FALLBACK_PROVIDERS = (
    "together",
    "novita",
    "nscale",
    "fireworks-ai",
    "deepinfra",
    "scaleway",
    "ovhcloud",
    "featherless-ai",
)
_DEFAULT_SEARXNG_BASE_URLS = ("https://baresearch.org",)


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


class SearchError(Exception):
    """Search backend failed before returning usable results."""


class HuggingFaceTextGenerator:
    """Minimal Hugging Face Inference Providers chat client."""

    def __init__(self, model: str, token_env: str = "HUGGINGFACE_API_TOKEN", timeout_seconds: int = 30) -> None:
        self.model = model
        self.models = _candidate_models(model)
        self.token_env = token_env
        self.timeout_seconds = timeout_seconds

    def generate(self, prompt: str) -> str:
        token = os.getenv(self.token_env)
        if not token:
            return f"Set {self.token_env} to a Hugging Face access token so I can ask the model {self.model}."

        errors: list[str] = []
        for model in self.models:
            result = self._generate_with_model(prompt, token, model)
            if not _is_retryable_huggingface_error(result):
                return result
            errors.append(result)

        return errors[-1] if errors else "Hugging Face did not return an answer."

    def _generate_with_model(self, prompt: str, token: str, model: str) -> str:
        request = Request(
            "https://router.huggingface.co/v1/chat/completions",
            data=json.dumps(
                {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 220,
                    "stream": False,
                }
            ).encode("utf-8"),
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310 - fixed HTTPS API endpoint.
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            return _format_huggingface_http_error(exc, model)
        except (URLError, TimeoutError) as exc:
            return f"I could not reach Hugging Face right now: {exc}."

        if isinstance(payload, dict) and isinstance(payload.get("choices"), list) and payload["choices"]:
            choice = payload["choices"][0]
            if isinstance(choice, dict):
                message = choice.get("message", {})
                if isinstance(message, dict):
                    content = message.get("content", "")
                    return str(content).strip() or "The model returned an empty answer."
        if isinstance(payload, dict) and "error" in payload:
            return f"Hugging Face error: {payload['error']}"
        return "I could not understand the Hugging Face response."


def _candidate_models(model: str) -> tuple[str, ...]:
    base_model = model.split(":", maxsplit=1)[0]
    fallback_models = tuple(f"{base_model}:{provider}" for provider in _FALLBACK_PROVIDERS)
    return tuple(dict.fromkeys((model, *fallback_models)))


def _is_retryable_huggingface_error(message: str) -> bool:
    retry_markers = (
        "Access denied",
        "Cloudflare",
        "Error 1010",
        "HTTP 429",
        "HTTP 500",
        "HTTP 502",
        "HTTP 503",
        "HTTP 504",
        "could not reach Hugging Face",
        "could not understand the Hugging Face response",
        "model returned an empty answer",
    )
    return any(marker in message for marker in retry_markers)


def _format_huggingface_http_error(exc: HTTPError, model: str) -> str:
    try:
        body = exc.read().decode("utf-8", errors="replace").strip()
    except OSError:
        body = ""

    detail = ""
    if body:
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            detail = _summarize_html_error(body) if _looks_like_html(body) else body
        else:
            error = payload.get("error") if isinstance(payload, dict) else None
            detail = str(error or payload)

    message = f"Hugging Face returned HTTP {exc.code} for model {model}."
    if detail:
        message = f"{message} {detail}"
    if exc.code == 403 and not _is_downstream_provider_block(detail):
        message = (
            f"{message} Check that your token has the Hugging Face "
            "'Make calls to Inference Providers' permission."
        )
    return message


def _is_downstream_provider_block(detail: str) -> bool:
    return any(marker in detail for marker in ("Cloudflare", "Error 1010", "Access denied"))


def _looks_like_html(text: str) -> bool:
    return bool(re.search(r"^\s*<!doctype html|<html\b", text, flags=re.IGNORECASE))


def _summarize_html_error(html: str) -> str:
    parser = _HTMLTextParser()
    parser.feed(html)
    text = " ".join(parser.text_parts)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:500] if text else "HTML error page returned."


class _HTMLTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.text_parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip_depth and data.strip():
            self.text_parts.append(data.strip())


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


class SearXNGSearcher:
    """Search client for SearXNG's open-source JSON API."""

    def __init__(
        self,
        base_url: str | None = None,
        fallback: WebSearcher | None = None,
        timeout_seconds: int = 15,
    ) -> None:
        env_url = os.getenv("SEARXNG_BASE_URL")
        configured_url = base_url or env_url
        self.base_urls = (_normalize_base_url(configured_url),) if configured_url else _DEFAULT_SEARXNG_BASE_URLS
        self.fallback = fallback
        self.timeout_seconds = timeout_seconds

    def search(self, query: str, *, limit: int = 3) -> tuple[SearchResult, ...]:
        errors: list[Exception] = []
        for base_url in self.base_urls:
            try:
                results = self._search_instance(base_url, query, limit=limit)
            except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
                errors.append(exc)
                continue
            if results:
                return results

        if self.fallback is not None:
            return self.fallback.search(query, limit=limit)
        if errors:
            raise errors[-1]
        return ()

    def _search_instance(self, base_url: str, query: str, *, limit: int) -> tuple[SearchResult, ...]:
        params = urlencode({"q": query, "format": "json", "language": "en", "safesearch": "1"})
        request = Request(
            f"{base_url}/search?{params}",
            headers={"Accept": "application/json", "User-Agent": "Alipin/0.1"},
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310 - user-configured HTTPS search endpoint.
            payload = json.loads(response.read().decode("utf-8"))

        raw_results = payload.get("results") if isinstance(payload, dict) else None
        if not isinstance(raw_results, list):
            return ()

        results: list[SearchResult] = []
        for item in raw_results:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            url = str(item.get("url") or "").strip()
            snippet = str(item.get("content") or item.get("snippet") or "").strip()
            if title and url:
                results.append(SearchResult(unescape(title), url, unescape(snippet)))
            if len(results) >= limit:
                break
        return tuple(results)


def _normalize_base_url(base_url: str) -> str:
    return base_url.strip().rstrip("/")


class SerpAPISearcher:
    """Search client for SerpAPI's Google Search API."""

    def __init__(
        self,
        token_env: str = "SERPAPI_API_KEY",
        fallback: WebSearcher | None = None,
        timeout_seconds: int = 15,
    ) -> None:
        self.token_env = token_env
        self.fallback = fallback
        self.timeout_seconds = timeout_seconds

    def search(self, query: str, *, limit: int = 3) -> tuple[SearchResult, ...]:
        token = os.getenv(self.token_env)
        if not token:
            raise SearchError(f"Set {self.token_env} to a SerpAPI key or choose another search provider.")

        try:
            return self._search_serpapi(query, limit=limit, token=token)
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
            if self.fallback is not None:
                return self.fallback.search(query, limit=limit)
            raise

    def _search_serpapi(self, query: str, *, limit: int, token: str) -> tuple[SearchResult, ...]:
        params = urlencode(
            {
                "engine": "google",
                "q": query,
                "api_key": token,
                "num": str(limit),
                "hl": "en",
            }
        )
        request = Request(
            f"https://serpapi.com/search?{params}",
            headers={"Accept": "application/json", "User-Agent": "Alipin/0.1"},
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310 - fixed HTTPS SerpAPI endpoint.
            payload = json.loads(response.read().decode("utf-8"))

        if isinstance(payload, dict) and payload.get("error"):
            raise SearchError(f"SerpAPI error: {payload['error']}")

        raw_results = payload.get("organic_results") if isinstance(payload, dict) else None
        if not isinstance(raw_results, list):
            return ()

        results: list[SearchResult] = []
        for item in raw_results:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            url = str(item.get("link") or "").strip()
            snippet = str(item.get("snippet") or "").strip()
            if title and url:
                results.append(SearchResult(unescape(title), url, unescape(snippet)))
            if len(results) >= limit:
                break
        return tuple(results)


def _clean_duckduckgo_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc.endswith("duckduckgo.com") and parsed.path == "/l/":
        uddg = parse_qs(parsed.query).get("uddg")
        if uddg:
            return unquote(uddg[0])
    return url


def _needs_web(question: str) -> bool:
    return classify_web_need(question).needs_web


@dataclass(frozen=True)
class WebNeedDecision:
    """Decision about whether a question should receive web context."""

    needs_web: bool
    search_query: str
    reason: str


def classify_web_need(question: str) -> WebNeedDecision:
    """Decide whether a question needs fresh or external web context."""
    cleaned = question.strip()
    lowered = cleaned.lower()
    normalized = re.sub(r"\s+", " ", lowered)
    search_query = _extract_search_query(cleaned)

    if re.search(r"\b(search|look up|find|browse|google)\b", normalized):
        return WebNeedDecision(True, search_query, "The user explicitly asked to search or find information.")

    if re.search(r"\b(latest|current|today|tonight|tomorrow|yesterday|news|recent|now|this week|this month|this year)\b", normalized):
        return WebNeedDecision(True, search_query, "The question asks for time-sensitive information.")

    if re.search(r"\b(weather|forecast|temperature|traffic|near me|nearby|hours|open right now|price|prices|cost|release date|version|download|available|availability|stock|score|schedule)\b", normalized):
        return WebNeedDecision(True, search_query, "The question depends on live or location-specific facts.")

    if re.search(r"\b(best|top|compare|comparison|review|reviews|recommend|recommendation|should i buy|should i get|worth buying|vs\.?|versus)\b", normalized):
        return WebNeedDecision(True, search_query, "The question benefits from current web results and source comparison.")

    return WebNeedDecision(False, search_query, "The question can usually be answered from the model without web context.")


def _extract_search_query(question: str) -> str:
    cleaned = question.strip()
    lowered = cleaned.lower()
    prefixes = (
        "search the web for",
        "search online for",
        "search for",
        "look up",
        "find me",
        "find",
        "browse for",
        "google",
    )
    for prefix in prefixes:
        if lowered.startswith(prefix):
            return cleaned[len(prefix) :].strip(" :,-") or cleaned
    return cleaned


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
            search_results = searcher.search(classify_web_need(cleaned).search_query, limit=3)
        except (HTTPError, URLError, TimeoutError, SearchError) as exc:
            return AnswerResult(f"I could not search the web right now: {exc}.", used_web=True)
        if not search_results:
            return AnswerResult(
                "I tried to search the web, but the search backend returned no usable results. "
                "Set SEARXNG_BASE_URL to a working SearXNG instance for reliable search.",
                used_web=True,
            )

    answer = generator.generate(_build_prompt(cleaned, search_results))
    sources = tuple(result.url for result in search_results)
    if sources:
        answer = f"{answer}\n\nSources:\n" + "\n".join(f"- {url}" for url in sources)
    return AnswerResult(answer=answer, used_web=used_web, sources=sources)
