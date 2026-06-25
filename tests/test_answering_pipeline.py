from pathlib import Path

import pytest

from githelp.data_models import DocumentRecord
from githelp.rag.answering import (
    AMBIGUOUS_FOLLOWUP_RESPONSE,
    _boost_filename_matches,
    _extract_filename_tokens,
    _get_project_name,
    _prepare_llm_answer_input,
    _resolve_corpus_path,
    answer_question,
    answer_question_with_provider,
    is_context_dependent_question,
    is_reformulation_followup,
    resolve_retrieval_query,
    rewrite_query_with_history,
)
from githelp.retrieval.base import RetrievalResult


def make_result(doc_id: str, relative_path: str, score: float) -> RetrievalResult:
    document = DocumentRecord(
        doc_id=doc_id,
        content="example content",
        source_type="markdown_section",
        title=Path(relative_path).name,
        file_path=relative_path,
        section_title=None,
        module_name=None,
        symbol_name=None,
        signature=None,
        language="en",
        tags=[],
        metadata={"relative_path": relative_path, "project_name": "mmore"},
    )
    return RetrievalResult(document=document, score=score)


def make_custom_result(
    doc_id: str,
    content: str,
    source_type: str,
    score: float,
    title: str = "Example",
    relative_path: str = "docs/example.md",
    symbol_name: str | None = None,
) -> RetrievalResult:
    document = DocumentRecord(
        doc_id=doc_id,
        content=content,
        source_type=source_type,
        title=title,
        file_path=relative_path,
        section_title=None,
        module_name="mmore.index.indexer" if symbol_name else None,
        symbol_name=symbol_name,
        signature=None,
        language="en",
        tags=[],
        metadata={"relative_path": relative_path, "project_name": "mmore"},
    )
    return RetrievalResult(document=document, score=score)


class DummyProvider:
    def __init__(self, response: str = "generated answer"):
        self.response = response
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.response


class FailingProvider:
    def generate(self, prompt: str) -> str:
        raise RuntimeError("rewrite failed")


class SequencedProvider:
    def __init__(self, responses: list[str]):
        self.responses = iter(responses)
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return next(self.responses)


def test_extract_filename_tokens_finds_common_extensions():
    question = "What is defined in config_index.yml and app_config.yaml?"
    assert _extract_filename_tokens(question) == [
        "config_index.yml",
        "app_config.yaml",
    ]


def test_boost_filename_matches_reorders_matching_result():
    low = make_result("doc::config", "examples/config_index.yml", 0.5)
    high = make_result("doc::other", "docs/index.md", 1.0)

    results = _boost_filename_matches(
        [high, low],
        "Explain config_index.yml",
        boost=1.0,
    )

    assert results[0].document.doc_id == "doc::config"
    assert results[0].score == pytest.approx(1.5)


def test_get_project_name_prefers_app_config():
    assert _get_project_name({"project_name": "githelp"}) == "githelp"


def test_get_project_name_falls_back_to_result_metadata():
    result = make_result("doc::one", "docs/index.md", 1.0)

    assert _get_project_name({}, [result]) == "mmore"


def test_get_project_name_uses_referenced_project_config(tmp_path: Path):
    project_config = tmp_path / "project_config.yaml"
    project_config.write_text("project_name: referenced-project\n", encoding="utf-8")

    config = {"project": {"config_path": str(project_config)}}

    assert _get_project_name(config) == "referenced-project"


def test_resolve_corpus_path_uses_explicit_path():
    path = _resolve_corpus_path("custom/corpus.jsonl", {})

    assert path == Path("custom/corpus.jsonl")


def test_resolve_corpus_path_uses_project_name_from_config():
    path = _resolve_corpus_path(None, {"project_name": "mmore"})

    assert path == Path("data") / "projects" / "mmore" / "corpus.jsonl"


def test_resolve_corpus_path_uses_referenced_project_config(tmp_path: Path):
    project_config = tmp_path / "project_config.yaml"
    project_config.write_text("project_name: referenced-project\n", encoding="utf-8")

    path = _resolve_corpus_path(
        None,
        {"project_config_path": str(project_config)},
    )

    assert path == Path("data") / "projects" / "referenced-project" / "corpus.jsonl"


def test_resolve_corpus_path_fails_when_project_name_missing():
    with pytest.raises(ValueError, match="Could not infer"):
        _resolve_corpus_path(None, {})


def test_prepare_llm_answer_input_returns_final_answer_for_empty_results():
    answer, results, should_generate = _prepare_llm_answer_input(
        question="How do I install it?",
        results=[],
        config={},
    )

    assert answer == "I could not find relevant sources in the corpus."
    assert results == []
    assert should_generate is False


def test_prepare_llm_answer_input_blocks_subjective_private_dataset_recommendation():
    result = make_result("doc::one", "docs/index.md", 1.0)

    answer, results, should_generate = _prepare_llm_answer_input(
        question="Which embedding model is best for my dataset?",
        results=[result],
        config={},
    )

    assert "private dataset" in answer
    assert results == [result]
    assert should_generate is False


def test_prepare_llm_answer_input_builds_prompt_when_generation_is_needed():
    result = make_result("doc::one", "docs/index.md", 1.0)

    prompt, results, should_generate = _prepare_llm_answer_input(
        question="How do I configure it?",
        results=[result],
        config={"project_name": "githelp"},
    )

    assert "How do I configure it?" in prompt
    assert "githelp" in prompt
    assert results == [result]
    assert should_generate is True


def test_context_dependent_question_detection():
    assert is_context_dependent_question("Explain more simply") is True
    assert is_context_dependent_question("explain it more simply") is True
    assert is_context_dependent_question("make it clearer") is True
    assert is_context_dependent_question("Where is it used?") is True
    assert is_context_dependent_question("Can you explain step 2?") is True
    assert is_context_dependent_question("tell me briefly the steps to apply") is True
    assert is_context_dependent_question("What about Docker?") is True
    assert is_context_dependent_question("Why did that fail?") is True
    assert is_context_dependent_question("How to use indexing in mmore?") is False
    assert is_context_dependent_question("Which file defines the app config?") is False
    assert is_context_dependent_question("Summarize how MMORE indexing works") is False
    assert (
        is_context_dependent_question("Which setting ensures that Docker uses GPU?")
        is False
    )


def test_reformulation_followup_detection():
    assert is_reformulation_followup("Explain more simply") is True
    assert is_reformulation_followup("make it clearer") is True
    assert is_reformulation_followup("make it shorter") is True
    assert is_reformulation_followup("give me an example") is True
    assert is_reformulation_followup("Where is it used?") is False


def test_rewrite_query_with_history_uses_llm_for_vague_followup():
    provider = DummyProvider("Explain how to use indexing in mmore in simple terms.")
    history = [
        {"role": "user", "content": "How to use indexing in mmore?"},
        {
            "role": "assistant",
            "content": "Use a config file and python3 -m mmore index.",
        },
    ]

    rewritten = rewrite_query_with_history(
        "explain it more simply",
        chat_history=history,
        llm_provider=provider,
    )

    assert rewritten == "Explain how to use indexing in mmore in simple terms."
    assert "Do not answer the question" in provider.prompts[0]
    assert "Output only one rewritten retrieval query" in provider.prompts[0]


def test_rewrite_query_with_history_falls_back_safely():
    history = [{"role": "user", "content": "What does MmoreRetriever do?"}]

    assert (
        rewrite_query_with_history(
            "Where is it used?",
            chat_history=history,
            llm_provider=None,
        )
        == "Where is it used?"
    )

    assert (
        rewrite_query_with_history(
            "Where is it used?",
            chat_history=history,
            llm_provider=FailingProvider(),
        )
        == "Where is it used?"
    )


def test_resolve_retrieval_query_does_not_consult_history_for_standalone_question():
    provider = DummyProvider("wrong rewritten query")

    decision = resolve_retrieval_query(
        "How does Docker deployment work?",
        chat_history=[
            {"role": "user", "content": "How does MMORE indexing work?"},
            {"role": "assistant", "content": "It builds a vector index."},
        ],
        llm_provider=provider,
    )

    assert decision.retrieval_query == "How does Docker deployment work?"
    assert decision.is_followup is False
    assert decision.is_ambiguous is False
    assert provider.prompts == []


def test_standalone_unrelated_question_is_used_as_is_for_retrieval(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    result = make_custom_result(
        doc_id="markdown::docker",
        content="Docker deployment uses the documented compose configuration.",
        source_type="markdown_section",
        score=1.0,
        title="Docker deployment",
        relative_path="docs/deployment/docker.md",
    )
    queries: list[str] = []
    provider = DummyProvider("Docker answer")
    monkeypatch.setattr(
        "githelp.rag.answering.load_yaml",
        lambda _path: {"project_profile": "generic", "project_name": "githelp"},
    )

    def fake_retrieve_documents(**kwargs):
        queries.append(kwargs["query"])
        return [result]

    monkeypatch.setattr(
        "githelp.rag.answering.retrieve_documents",
        fake_retrieve_documents,
    )

    answer, results = answer_question_with_provider(
        question="How does Docker deployment work?",
        llm_provider=provider,
        corpus_path=tmp_path / "corpus.jsonl",
        backend="simple",
        config_path="unused.yaml",
        chat_history=[
            {"role": "user", "content": "How does MMORE indexing work?"},
            {"role": "assistant", "content": "It builds a vector index."},
        ],
    )

    assert answer == "Docker answer"
    assert results == [result]
    assert queries == ["How does Docker deployment work?"]
    assert len(provider.prompts) == 1


def test_resolve_retrieval_query_can_report_ambiguous_followup():
    provider = DummyProvider("AMBIGUOUS")

    decision = resolve_retrieval_query(
        "Where is it used?",
        chat_history=[
            {"role": "user", "content": "Compare the indexer and retriever."},
        ],
        llm_provider=provider,
    )

    assert decision.retrieval_query == "Where is it used?"
    assert decision.is_followup is True
    assert decision.is_ambiguous is True
    assert "Prefer the most recent relevant user question" in provider.prompts[0]
    assert "output exactly AMBIGUOUS" in provider.prompts[0]


def test_answer_question_without_llm_uses_shared_prepared_retrieval(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    uv_result = make_custom_result(
        doc_id="markdown::uv",
        content="Use `uv` to install `mmore`",
        source_type="markdown_section",
        score=100.0,
        title="uv",
        relative_path="advanced_usage/uv.md",
    )
    code_result = make_custom_result(
        doc_id="python::indexer",
        content=(
            "The Indexer class builds and manages indexes for document "
            "retrieval workflows."
        ),
        source_type="python_class",
        score=1.0,
        title="mmore.index.indexer.Indexer",
        relative_path="src/mmore/index/indexer.py",
        symbol_name="Indexer",
    )

    calls: list[str] = []

    def fake_load_yaml(config_path: str) -> dict:
        return {"project_profile": "mmore", "project_name": "mmore"}

    def fake_retrieve_documents(**kwargs):
        calls.append(kwargs["backend"])
        if kwargs["backend"] == "simple":
            return [code_result]
        return [uv_result]

    monkeypatch.setattr("githelp.rag.answering.load_yaml", fake_load_yaml)
    monkeypatch.setattr(
        "githelp.rag.answering.retrieve_documents",
        fake_retrieve_documents,
    )

    answer, results = answer_question(
        question="What does the Indexer class do?",
        corpus_path=tmp_path / "corpus.jsonl",
        top_k=5,
        backend="mmore",
        config_path="unused.yaml",
    )

    assert calls == ["mmore", "simple"]
    assert results == [code_result]
    assert "Indexer class builds and manages indexes" in answer
    assert "Use `uv` to install `mmore`" not in answer


def test_answer_question_merges_original_query_after_profile_expansion(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    expanded_query_result = make_custom_result(
        doc_id="python::cli-index",
        content="Run the indexer from the CLI with a config file.",
        source_type="python_function",
        score=5.0,
        title="mmore.cli.index",
        relative_path="cli.py",
        symbol_name="index",
    )
    original_query_result = make_custom_result(
        doc_id="python::indexer",
        content=(
            "The Indexer class builds and manages indexes for document "
            "retrieval workflows."
        ),
        source_type="python_class",
        score=1.0,
        title="mmore.index.indexer.Indexer",
        relative_path="src/mmore/index/indexer.py",
        symbol_name="Indexer",
    )

    queries: list[str] = []

    def fake_load_yaml(config_path: str) -> dict:
        return {"project_profile": "mmore", "project_name": "mmore"}

    def fake_retrieve_documents(**kwargs):
        queries.append(kwargs["query"])
        if kwargs["query"] == "What does the Indexer class do?":
            return [original_query_result]
        return [expanded_query_result]

    monkeypatch.setattr("githelp.rag.answering.load_yaml", fake_load_yaml)
    monkeypatch.setattr(
        "githelp.rag.answering.retrieve_documents",
        fake_retrieve_documents,
    )

    answer, results = answer_question(
        question="What does the Indexer class do?",
        corpus_path=tmp_path / "corpus.jsonl",
        top_k=5,
        backend="simple",
        config_path="unused.yaml",
    )

    assert queries[0] != "What does the Indexer class do?"
    assert queries[1] == "What does the Indexer class do?"
    assert results[0] == original_query_result
    assert "Indexer class builds and manages indexes" in answer


def test_answer_question_with_provider_uses_retrieval_query_only_for_retrieval(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    result = make_custom_result(
        doc_id="markdown::indexing",
        content="Indexing uses a config file and a JSONL documents file.",
        source_type="markdown_section",
        score=1.0,
        title="Indexing",
        relative_path="getting_started/indexing.md",
    )
    queries: list[str] = []
    provider = DummyProvider("answer")

    def fake_load_yaml(config_path: str) -> dict:
        return {"project_profile": "generic", "project_name": "mmore"}

    def fake_retrieve_documents(**kwargs):
        queries.append(kwargs["query"])
        return [result]

    monkeypatch.setattr("githelp.rag.answering.load_yaml", fake_load_yaml)
    monkeypatch.setattr(
        "githelp.rag.answering.retrieve_documents",
        fake_retrieve_documents,
    )

    answer, results = answer_question_with_provider(
        question="explain it more simply",
        llm_provider=provider,
        corpus_path=tmp_path / "corpus.jsonl",
        backend="simple",
        config_path="unused.yaml",
        retrieval_query="Explain how to use indexing in mmore in simple terms.",
        chat_history=[
            {"role": "user", "content": "How to use indexing in mmore?"},
            {"role": "assistant", "content": "Use the indexing command."},
        ],
    )

    assert answer == "answer"
    assert results == [result]
    assert queries == ["Explain how to use indexing in mmore in simple terms."]
    assert "Question:" in provider.prompts[0]
    assert "explain it more simply" in provider.prompts[0]
    assert "Recent conversation context:" in provider.prompts[0]


def test_answer_question_with_provider_rewrites_followup_before_retrieval(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    result = make_custom_result(
        doc_id="markdown::indexing",
        content="Indexing uses a configuration file that defines the index settings.",
        source_type="markdown_section",
        score=1.0,
    )
    queries: list[str] = []
    provider = SequencedProvider(
        ["How is MMORE indexing configured?", "focused answer"]
    )

    monkeypatch.setattr(
        "githelp.rag.answering.load_yaml",
        lambda _path: {"project_profile": "generic", "project_name": "mmore"},
    )

    def fake_retrieve_documents(**kwargs):
        queries.append(kwargs["query"])
        return [result]

    monkeypatch.setattr(
        "githelp.rag.answering.retrieve_documents",
        fake_retrieve_documents,
    )

    answer, results = answer_question_with_provider(
        question="How do I configure it?",
        llm_provider=provider,
        corpus_path=tmp_path / "corpus.jsonl",
        backend="simple",
        config_path="unused.yaml",
        chat_history=[
            {"role": "user", "content": "How does MMORE indexing work?"},
            {"role": "assistant", "content": "It uses a configuration file."},
        ],
    )

    assert answer == "focused answer"
    assert results == [result]
    assert queries == ["How is MMORE indexing configured?"]
    assert "Standalone retrieval query:" in provider.prompts[0]
    assert "Question:\nHow do I configure it?" in provider.prompts[1]


def test_answer_question_with_provider_asks_for_clarification_when_ambiguous(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    provider = DummyProvider("AMBIGUOUS")

    def fail_if_retrieval_runs(**_kwargs):
        raise AssertionError("ambiguous follow-up should not run retrieval")

    monkeypatch.setattr(
        "githelp.rag.answering.retrieve_documents",
        fail_if_retrieval_runs,
    )

    answer, results = answer_question_with_provider(
        question="Where is it used?",
        llm_provider=provider,
        corpus_path=tmp_path / "corpus.jsonl",
        config_path="unused.yaml",
        chat_history=[
            {"role": "user", "content": "Compare the indexer and retriever."},
        ],
    )

    assert answer == AMBIGUOUS_FOLLOWUP_RESPONSE
    assert results == []
    assert len(provider.prompts) == 1
