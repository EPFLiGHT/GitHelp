![Githelp logo](docs/_static/images/logo.png)

# GitHelp

GitHelp is a conversational assistant for querying a software project's
documentation, configuration files, repository structure, and Python API
documentation in natural language.

The initial use case is the
[MMORE](https://github.com/swiss-ai/mmore) repository. The architecture is
project-oriented, so GitHelp can also build a corpus for another Python
repository selected locally or cloned from a public GitHub URL.

Full documentation: [GitHelp documentation](https://epflight.github.io/GitHelp/)

Direct access to the interface (from EPFL or VPN-connected): [Interface](http://gpu217.rcp.epfl.ch:1312/githelp/)

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

GitHelp turns a target repository into a structured `DocumentRecord` corpus.
The simple backend searches this corpus directly, while the MMORE workflow
exports and indexes it before retrieval. Retrieved records are then used either
by the extractive answerer or as grounded context for the local LLM.

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

## Quick Start

## Quick Start

GitHelp requires Python 3.10 or higher.

Clone the repository and create a fresh environment:

```bash
git clone https://github.com/EPFLiGHT/GitHelp.git
cd GitHelp

conda create -n githelp python=3.10 -y
conda activate githelp
```

Install GitHelp from the repository root:

```bash
python -m pip install -e .
```

Run the Streamlit interface:

```bash
streamlit run app/streamlit_app.py
```

Then open `http://localhost:8501` and:

1. Select a local Python repository or enter a public GitHub repository URL.
2. Build the **simple index** first. It creates the GitHelp corpus and is the
   fastest way to validate extraction and retrieval.
3. Ask a question and inspect the retrieved sources.
4. Optionally build the **MMORE index** for native MMORE/Milvus retrieval.

The two modes serve different purposes:

- **Simple:** lightweight, deterministic lexical retrieval; recommended for a
  first run and for debugging.
- **MMORE:** dense and sparse retrieval through MMORE and Milvus; requires the
  additional indexing step and is more sensitive to model dependencies and
  local hardware.

## Installation

GitHelp requires Python 3.10 or higher.

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
mmore[index,rag]==1.2.4
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
back to lexical retrieval over the exported `mmore_corpus.jsonl`. This fallback
keeps the application usable, but it does not use native MMORE/Milvus vector
search. Retrieved sources are tagged with the actual mode:

```text
native_index
corpus_fallback
```

## Retrieval Evaluation

Run retrieval evaluation on benchmark questions:

```bash
python scripts/evaluate_retrieval.py \
  --questions-path tests/evaluation/githelp_eval_questions.txt \
  --corpus-path data/projects/mmore/corpus.jsonl \
  --backend simple \
  --top-k 5
```

With expected-source checks:

```bash
python scripts/evaluate_retrieval.py \
  --questions-path tests/evaluation/githelp_eval_questions.txt \
  --expected-sources-path tests/evaluation/githelp_eval_expected_sources.example.json \
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

## Docker and EPFL Cluster Deployment

GitHelp can also be run with Docker.

For local testing:

```bash
docker compose -f docker-compose.local.yml up --build
```

Then open:
```text
http://localhost:8501
```
For the EPFL GPU server deployment, GitHelp is packaged as a CUDA-enabled Docker image and served through Traefik under:
```text
http://gpu217.rcp.epfl.ch:1312/githelp/
```
The deployment uses a persistent `data/` volume for cloned repositories, generated corpora and MMORE indexes, and a persistent Hugging Face cache for local model files.

Detailed deployment and troubleshooting instructions are available in:
```text
docs/deployment/cluster.md
```
