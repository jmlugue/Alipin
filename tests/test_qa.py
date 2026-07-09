from alipin.qa import AnswerResult, SearchResult, answer_question


class FakeGenerator:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return "model answer"


class FakeSearcher:
    def search(self, query: str, *, limit: int = 3) -> tuple[SearchResult, ...]:
        assert limit == 3
        return (SearchResult("Example", "https://example.com", f"Snippet for {query}"),)


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
