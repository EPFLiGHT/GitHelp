![Githelp logo](docs/_static/images/logo.png)

# GitHelp

GitHelp is a conversational assistant for querying a software project's
documentation, configuration files, repository structure, and Python API
documentation in natural language.

The initial use case is the
[MMORE](https://github.com/swiss-ai/mmore) repository. The architecture is
project-oriented, so GitHelp can also build a corpus for another Python
repository selected locally or cloned from a public GitHub URL.

Full documentation:

```text
https://epflight.github.io/GitHelp/
```

## What GitHelp Answers

GitHelp is designed for questions such as:

- How do I install, configure, or run the target project?
- How do I build an MMORE index?
- Where is a specific module, class, function, or config implemented?
- What is the signature of a function?
- What does an example configuration file look like?
- Which retrieved sources support this answer?

Answers are source-grounded: GitHelp retrieves project documents first, builds a
prompt from those sources, and then optionally calls a local LLM provider.

## Architecture

![Githelp schema](docs/_static/images/schema.png)

```text
target repository
        |
        v
loaders and extractors
        |
        v
DocumentRecord objects
        |
        v
corpus.jsonl
        |
        +--> simple retriever
        |
        +--> MMORE export -> MMORE index -> MMORE retriever
                         \-> mmore_corpus.jsonl fallback
        |
        v
project profile
        |
        v
source-grounded prompt
        |
        v
extractive answer or local LLM answer
        |
        v
Streamlit UI and CLI scripts
```

Main package layout:

```text
src/githelp/
  config.py                 typed configuration helpers
  data_models.py            DocumentRecord model
  corpus/                   corpus construction
  loaders/                  Markdown, YAML, repository structure loaders
  extractors/               Python docstring/signature extraction
  indexing/                 MMORE JSONL export and index wrapper
  retrieval/                simple and MMORE retrieval backends
  rag/                      answering, prompting, LLM providers
  project_profiles/         project-specific query/reranking/direct-answer logic
  projects/                 project setup and GitHub loading workflows
  utils/                    shared filesystem paths

app/                        Streamlit interface
scripts/                    command-line workflows and debugging tools
docs/                       Sphinx documentation
tests/                      pytest suite
```

## Installation

From the repository root:

```bash
python -m pip install -e .
```

For development:

```bash
python -m pytest -q
```

GitHelp depends on MMORE for the native `mmore` backend:

```text
mmore[index,rag]==1.2.2
transformers>=4.51.0,<5
```

The Transformers upper bound is intentional: MMORE sparse indexing currently
uses APIs that are not compatible with Transformers 5.

## Run the Streamlit App

```bash
streamlit run app/streamlit_app.py
```

The interface lets a user:

- select a local target repository;
- clone a public GitHub repository into `data/repositories/`;
- build a simple corpus;
- export and build an MMORE-backed index;
- ask questions with or without the local LLM;
- inspect retrieved sources and debug metadata.

The default app configuration is:

```text
configs/app_config.yaml
```

The current local app state is stored in:

```text
data/app_state.json
```

This state file is generated locally and ignored by Git.

## GitHub Repository Workflow

Clone and prepare a public GitHub repository with the simple backend:

```bash
python scripts/prepare_github_project.py \
  https://github.com/swiss-ai/mmore
```

Or clone only:

```bash
python scripts/load_github_repository.py \
  https://github.com/swiss-ai/mmore
```

GitHelp stores cloned repositories under:

```text
data/repositories/
```

## Corpus and Retrieval Commands

Build a project-specific corpus:

```bash
python scripts/build_corpus.py \
  --config data/projects/mmore/project_config.yaml \
  --output-path data/projects/mmore/corpus.jsonl
```

Preview records:

```bash
python scripts/preview_corpus.py \
  --corpus-path data/projects/mmore/corpus.jsonl \
  --limit 3
```

Debug retrieval:

```bash
python scripts/debug_retrieval.py \
  "How do I configure indexing?" \
  --corpus-path data/projects/mmore/corpus.jsonl
```

Prepare an answer prompt:

```bash
python scripts/prepare_answer.py \
  "How do I configure indexing?" \
  --backend simple \
  --corpus-path data/projects/mmore/corpus.jsonl \
  --config-path configs/app_config.yaml
```

Generate an answer:

```bash
python scripts/answer_question.py \
  "How do I configure indexing?" \
  --backend mmore \
  --llm \
  --corpus-path data/projects/mmore/corpus.jsonl \
  --config-path configs/app_config.yaml
```

## MMORE Indexing

Export a GitHelp corpus to MMORE's JSONL format:

```bash
python scripts/export_mmore_corpus.py \
  --corpus-path data/projects/mmore/corpus.jsonl \
  --output-path data/projects/mmore/mmore_corpus.jsonl
```

Build the MMORE index:

```bash
python scripts/build_index.py \
  --documents-path data/projects/mmore/mmore_corpus.jsonl \
  --collection-name mmore_docs
```

The native MMORE retriever is run in an isolated subprocess. If that native
process fails in a local environment, GitHelp keeps Streamlit alive and falls
back to retrieval from the exported `mmore_corpus.jsonl`. Retrieved sources are
tagged with the actual mode:

```text
native_index
corpus_fallback
```

## Retrieval Evaluation

Run retrieval evaluation on benchmark questions:

```bash
python scripts/evaluate_retrieval.py \
  --questions-path githelp_eval_questions.txt \
  --corpus-path data/projects/mmore/corpus.jsonl \
  --backend simple \
  --top-k 5
```

With expected-source checks:

```bash
python scripts/evaluate_retrieval.py \
  --questions-path githelp_eval_questions.txt \
  --expected-sources-path githelp_eval_expected_sources.example.json \
  --corpus-path data/projects/mmore/corpus.jsonl \
  --backend simple \
  --top-k 5
```

## Tests

Run all tests:

```bash
python -m pytest -q
```

Compile Python files:

```bash
python -m compileall -q src app scripts
```

The test suite covers corpus building, loaders, extractors, retrieval,
answering, LLM provider factory behavior, GitHub loading, project setup, and
MMORE adapter edge cases.

## Documentation

Documentation lives in `docs/` and is organized into:

- getting started guides;
- architecture and data flow;
- component-level documentation;
- development and debugging notes.

Build locally with Sphinx from the `docs/` directory if needed:

```bash
python -m pip install -r docs/requirements.txt
sphinx-build -b html docs docs/_build/html
```

## Current Limitations

- GitHub loading currently targets public repositories.
- Existing clones under `data/repositories/` are reused unless manually updated.
- Building a corpus does not automatically rebuild the MMORE index.
- The simple backend is useful and deterministic, but it is not semantic vector retrieval.
- Native MMORE/Milvus retrieval can be sensitive to local Python, PyTorch, and
  OpenMP environments; GitHelp isolates that path and provides an
  `mmore_corpus.jsonl` fallback.
- LLM quality and latency depend on the configured local model.

See `docs/development/limitations.md` for more detail.
