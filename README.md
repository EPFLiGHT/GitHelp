# DocAsk

DocAsk is a conversational assistant for querying a software project's documentation and code-related knowledge in natural language.

The initial use case is the [MMORE](https://github.com/swiss-ai/mmore) repository. DocAsk can use MMORE internally for indexing and retrieval, while exposing a simpler project-level interface to the user.

---

## Goal

DocAsk aims to help users ask questions about a project such as:

- How do I install or run the project?
- How do I configure indexing or retrieval?
- Where is a specific module implemented?
- What is the signature of a function?
- What does a class or method do?
- What does an example configuration file look like?

The long-term goal is to support other repositories by combining several source types:

- written documentation;
- Python docstrings and signatures;
- YAML configuration examples;
- repository structure summaries;
- later, selected code snippets and tests.

---

## Current architecture

```text
project repository
        ↓
DocAsk loaders and extractors
        ↓
unified corpus.jsonl
        ↓
retrieval backend
        ├── simple local retriever
        └── MMORE-compatible export → MMORE indexing → MMORE retrieval
        ↓
prompt construction
        ↓
answer generation
        ├── temporary extractive answerer
        └── future LLM answer generation
        ↓
Streamlit UI
```

At the moment, DocAsk supports:

- corpus building;
- local retrieval for debugging;
- MMORE-compatible export;
- MMORE indexing;
- MMORE retrieval;
- prompt preparation;
- temporary extractive answers.

LLM generation and the final Streamlit conversational interface are the next steps.

---

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

---

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


---
## Current status

Implemented:

- Markdown and reStructuredText documentation loading;
- Python documentation extraction using `ast`;
- extraction of module, class, function and method docstrings;
- extraction of Python signatures;
- YAML configuration loading;
- repository structure summary generation;
- unified `DocumentRecord` format;
- JSONL corpus generation;
- export to MMORE-compatible JSONL format;
- internal MMORE indexing through the PyPI package;
- internal MMORE retrieval backend;
- temporary local retriever for debugging;
- prompt construction with source citations;
- temporary extractive answerer for terminal testing.

Not implemented yet:

- LLM-based answer generation;
- final Streamlit conversational interface;
- deployment;
- selected code snippets;
- test file extraction;
- advanced source-aware reranking.

