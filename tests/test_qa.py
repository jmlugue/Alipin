from alipin.commands import UNSUPPORTED_MESSAGE
from alipin.qa import AnswerResult, HuggingFaceTextGenerator, SearchError, SearXNGSearcher, answer_question


def test_question_answering_is_disabled():
    result = answer_question("what is the weather?")

    assert result == AnswerResult(UNSUPPORTED_MESSAGE, used_web=False)


def test_disabled_generator_does_not_use_prompt():
    generator = HuggingFaceTextGenerator("old-model", token_env="TOKEN")

    assert generator.generate("search the web") == UNSUPPORTED_MESSAGE


def test_disabled_searcher_fails_closed():
    searcher = SearXNGSearcher(base_url="https://search.example")

    try:
        searcher.search("python tutorials")
    except SearchError as exc:
        assert str(exc) == UNSUPPORTED_MESSAGE
    else:
        raise AssertionError("Disabled searcher should raise SearchError.")
