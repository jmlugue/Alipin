from io import BytesIO
from urllib.error import HTTPError

from alipin.qa import (
    AnswerResult,
    SearchResult,
    SearXNGSearcher,
    SerpAPISearcher,
    _candidate_models,
    _format_huggingface_http_error,
    answer_question,
    classify_web_need,
)


class FakeGenerator:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return "model answer"


class FakeSearcher:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def search(self, query: str, *, limit: int = 3) -> tuple[SearchResult, ...]:
        assert limit == 3
        self.queries.append(query)
        return (SearchResult("Example", "https://example.com", f"Snippet for {query}"),)


class EmptySearcher:
    def search(self, query: str, *, limit: int = 3) -> tuple[SearchResult, ...]:
        return ()


class FakeHTTPResponse:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeHTTPResponse":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


def test_answers_question_with_hugging_face_generator():
    generator = FakeGenerator()

    result = answer_question("What is Alipin?", generator)

    assert result == AnswerResult("model answer", used_web=False)
    assert "Question: What is Alipin?" in generator.prompts[0]


def test_adds_web_context_for_current_question():
    generator = FakeGenerator()

    result = answer_question("What is the latest Python release?", generator, FakeSearcher())

    assert result.used_web is True
    assert result.sources == ("https://example.com",)
    assert "Web results:" in generator.prompts[0]
    assert "Sources:\n- https://example.com" in result.answer


def test_force_web_supports_search_commands():
    generator = FakeGenerator()

    result = answer_question("Discord download", generator, FakeSearcher(), force_web=True)

    assert result.used_web is True
    assert "Discord download" in generator.prompts[0]


def test_classifies_web_need_without_exact_current_keywords():
    decision = classify_web_need("Which laptop should I buy for Python development?")

    assert decision.needs_web is True
    assert "current web results" in decision.reason


def test_extracts_explicit_search_query_for_web_context():
    generator = FakeGenerator()
    searcher = FakeSearcher()

    result = answer_question("search for best local speech to text models", generator, searcher)

    assert result.used_web is True
    assert searcher.queries == ["best local speech to text models"]


def test_web_search_reports_empty_backend_results():
    generator = FakeGenerator()

    result = answer_question("search for Python release notes", generator, EmptySearcher())

    assert result.used_web is True
    assert "search backend returned no usable results" in result.answer
    assert generator.prompts == []


def test_formats_hugging_face_403_with_permission_hint():
    error = HTTPError(
        url="https://router.huggingface.co/v1/chat/completions",
        code=403,
        msg="Forbidden",
        hdrs={},
        fp=BytesIO(b'{"error":"Forbidden"}'),
    )

    message = _format_huggingface_http_error(error, "example/model")

    assert "HTTP 403" in message
    assert "Forbidden" in message
    assert "Make calls to Inference Providers" in message


def test_summarizes_html_error_pages():
    error = HTTPError(
        url="https://router.huggingface.co/v1/chat/completions",
        code=403,
        msg="Forbidden",
        hdrs={},
        fp=BytesIO(
            b"<!doctype html><html><head><title>Access denied</title></head>"
            b"<body><h1>Error 1010</h1><script>noise()</script>"
            b"<p>The owner of this website has banned your access.</p></body></html>"
        ),
    )

    message = _format_huggingface_http_error(error, "example/model")

    assert "Error 1010" in message
    assert "banned your access" in message
    assert "<html>" not in message
    assert "noise()" not in message
    assert "Make calls to Inference Providers" not in message


def test_candidate_models_keep_requested_model_and_add_fallbacks():
    candidates = _candidate_models("openai/gpt-oss-120b:groq")

    assert candidates[0] == "openai/gpt-oss-120b:groq"
    assert "openai/gpt-oss-120b:together" in candidates
    assert "openai/gpt-oss-120b:deepinfra" in candidates


def test_searxng_searcher_parses_json_results(monkeypatch):
    def fake_urlopen(request, timeout):
        assert "format=json" in request.full_url
        assert "q=alipin" in request.full_url
        return FakeHTTPResponse(
            b'{"results":[{"title":"Alipin","url":"https://example.com","content":"Assistant project"}]}'
        )

    monkeypatch.setattr("alipin.qa.urlopen", fake_urlopen)
    searcher = SearXNGSearcher(base_url="https://search.example")

    results = searcher.search("alipin")

    assert results == (SearchResult("Alipin", "https://example.com", "Assistant project"),)


def test_searxng_searcher_falls_back_when_instance_fails(monkeypatch):
    fallback = FakeSearcher()

    def fake_urlopen(request, timeout):
        raise TimeoutError("timeout")

    monkeypatch.setattr("alipin.qa.urlopen", fake_urlopen)
    searcher = SearXNGSearcher(base_url="https://search.example", fallback=fallback)

    results = searcher.search("alipin")

    assert results == (SearchResult("Example", "https://example.com", "Snippet for alipin"),)
    assert fallback.queries == ["alipin"]


def test_serpapi_searcher_reports_missing_key(monkeypatch):
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)

    result = answer_question("search for Python release notes", FakeGenerator(), SerpAPISearcher())

    assert result.used_web is True
    assert "Set SERPAPI_API_KEY" in result.answer


def test_serpapi_searcher_parses_organic_results(monkeypatch):
    monkeypatch.setenv("SERPAPI_API_KEY", "test-key")

    def fake_urlopen(request, timeout):
        assert "engine=google" in request.full_url
        assert "q=alipin" in request.full_url
        assert "api_key=test-key" in request.full_url
        return FakeHTTPResponse(
            b'{"organic_results":[{"title":"Alipin","link":"https://example.com","snippet":"Assistant project"}]}'
        )

    monkeypatch.setattr("alipin.qa.urlopen", fake_urlopen)
    searcher = SerpAPISearcher()

    results = searcher.search("alipin")

    assert results == (SearchResult("Alipin", "https://example.com", "Assistant project"),)
