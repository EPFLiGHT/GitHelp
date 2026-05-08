# DocAsk

DocAsk is a conversational assistant for querying a software project's documentation and code-related knowledge in natural language.

The initial use case is the MMORE repository.

## Documentation

The full project documentation is in:

```text
docs/
```

Start with:

```text
docs/index.md
```

Main pages:

- `docs/getting_started/quickstart.md`
- `docs/getting_started/configuration.md`
- `docs/getting_started/commands.md`
- `docs/architecture/overview.md`
- `docs/architecture/repository_structure.md`
- `docs/components/corpus_building.md`
- `docs/components/retrieval.md`
- `docs/components/rag_and_llm.md`

## Quickstart

Build the corpus:

```bash
PYTHONPATH=src python scripts/build_corpus.py
```

Preview it:

```bash
PYTHONPATH=src python scripts/preview_corpus.py --limit 2
```

Debug retrieval:

```bash
PYTHONPATH=src python scripts/debug_retrieval.py "How do I configure indexing?"
```

Prepare a prompt:

```bash
PYTHONPATH=src python scripts/prepare_answer.py "How do I configure indexing?" --backend simple
```

## Build the docs locally

```bash
python -m pip install -r docs/requirements.txt
sphinx-build -b html docs docs/_build/html
```
