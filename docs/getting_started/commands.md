# Commands

This page lists the main commands used during development.

Run all commands from the root of the `GitHelp` repository.

## Run the Streamlit app

```bash
streamlit run app/streamlit_app.py
```

The app lets a user:

- select a local target project;
- build a project-specific corpus;
- ask questions;
- inspect retrieved sources;
- switch retrieval backend;
- enable or disable LLM generation.

## Build the default corpus

```bash
PYTHONPATH=src python scripts/build_corpus.py
```

What it does:

- reads `configs/project_config.yaml`;
- loads Markdown and reStructuredText documentation;
- extracts Python docstrings and signatures;
- loads YAML configuration files if enabled;
- generates a repository structure document if enabled;
- writes `data/processed/corpus.jsonl`.

## Build a project-specific corpus

```bash
PYTHONPATH=src python scripts/build_corpus.py \
  --config data/projects/mmore/project_config.yaml \
  --output-path data/projects/mmore/corpus.jsonl
```

This is the command used internally by the Streamlit project setup flow.

## Preview a corpus

Default corpus:

```bash
PYTHONPATH=src python scripts/preview_corpus.py --limit 2
```

Project-specific corpus:

```bash
PYTHONPATH=src python scripts/preview_corpus.py \
  --corpus-path data/projects/mmore/corpus.jsonl \
  --limit 2
```

Useful filters:

```bash
PYTHONPATH=src python scripts/preview_corpus.py --source-type markdown_section --limit 3
PYTHONPATH=src python scripts/preview_corpus.py --source-type python_function --limit 3
PYTHONPATH=src python scripts/preview_corpus.py --source-type python_class --limit 3
PYTHONPATH=src python scripts/preview_corpus.py --source-type python_method --limit 3
PYTHONPATH=src python scripts/preview_corpus.py --source-type example_config --limit 3
PYTHONPATH=src python scripts/preview_corpus.py --source-type production_config --limit 3
PYTHONPATH=src python scripts/preview_corpus.py --source-type repo_structure --limit 1
```

## Debug local retrieval

```bash
PYTHONPATH=src python scripts/debug_retrieval.py "How do I configure indexing?"
```

This directly tests the simple local retriever.

For a project-specific corpus:

```bash
PYTHONPATH=src python scripts/debug_retrieval.py \
  "How do I configure indexing?" \
  --corpus-path data/projects/mmore/corpus.jsonl
```

## Debug prompt construction

```bash
PYTHONPATH=src python scripts/debug_prompting.py \
  "How do I configure indexing?" \
  --backend simple \
  --corpus-path data/projects/mmore/corpus.jsonl \
  --config-path configs/app_config.yaml
```

What it does:

- retrieves sources;
- applies the configured project profile;
- builds the source-grounded prompt;
- prints the prompt without calling an LLM.

## Prepare an answer prompt

Simple backend:

```bash
PYTHONPATH=src python scripts/prepare_answer.py \
  "How do I configure indexing?" \
  --backend simple \
  --corpus-path data/projects/mmore/corpus.jsonl \
  --config-path configs/app_config.yaml
```

MMORE backend:

```bash
PYTHONPATH=src python scripts/prepare_answer.py \
  "How do I configure indexing?" \
  --backend mmore \
  --config-path configs/app_config.yaml
```

The MMORE backend requires an MMORE index to be built first.

## Generate an answer

Simple backend with LLM:

```bash
PYTHONPATH=src python scripts/answer_question.py \
  "How do I configure indexing?" \
  --llm \
  --backend simple \
  --corpus-path data/projects/mmore/corpus.jsonl \
  --config-path configs/app_config.yaml
```

Simple backend without LLM:

```bash
PYTHONPATH=src python scripts/answer_question.py \
  "How do I configure indexing?" \
  --backend simple \
  --corpus-path data/projects/mmore/corpus.jsonl
```

Some project profiles can answer structured questions directly without loading the LLM.

## Extract Python documentation only

```bash
PYTHONPATH=src python scripts/extract_code_docs.py
```

If the script is run dynamically:

```bash
PYTHONPATH=src python scripts/extract_code_docs.py \
  --config data/projects/mmore/project_config.yaml \
  --output-path data/projects/mmore/code_docs.jsonl
```

## Export a corpus for MMORE

Default corpus:

```bash
PYTHONPATH=src python scripts/export_mmore_corpus.py
```

Project-specific corpus:

```bash
PYTHONPATH=src python scripts/export_mmore_corpus.py \
  --corpus-path data/projects/mmore/corpus.jsonl \
  --output-path data/projects/mmore/mmore_corpus.jsonl
```

## Build the MMORE index

Default MMORE corpus:

```bash
PYTHONPATH=src python scripts/build_index.py
```

Project-specific MMORE corpus:

```bash
PYTHONPATH=src python scripts/build_index.py \
  --documents-path data/projects/mmore/mmore_corpus.jsonl \
  --collection-name mmore_docs
```

## Run tests

```bash
PYTHONPATH=src pytest -q
```

The GitHub Actions workflow also runs these tests on push and pull request.
