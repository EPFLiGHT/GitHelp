# Commands

This page lists the main commands used during development.

Run all commands from the root of the `docask` repository.

## Build the corpus

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

What you should see:

```text
Building DocAsk corpus
--------------------------------------------------------------------------------
project_name: mmore
package_name: mmore
repo_path: ../../mmore
docs_path: ../../mmore/docs/source
code_path: ../../mmore/src/mmore
include_yaml_configs: True
yaml_config_paths: ['../../mmore/examples', '../../mmore/production-config']
include_repo_structure: True
repo_structure_max_depth: 4
--------------------------------------------------------------------------------
Loaded 246 markdown documents
Loaded 246 code documents
Loaded 52 YAML config documents
Loaded 1 repo structure documents

Built corpus with 545 documents
Saved to: .../data/processed/corpus.jsonl
Breakdown by source_type:
  - markdown_section: 246
  - python_function: 58
  - python_module: 10
  - python_class: 49
  - python_method: 129
  - example_config: 46
  - production_config: 6
  - repo_structure: 1
```

The exact numbers may change when the indexed repository changes.

## Preview the corpus

```bash
PYTHONPATH=src python scripts/preview_corpus.py --limit 2
```

What it does:

- reads `data/processed/corpus.jsonl`;
- prints a readable preview of extracted records.

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

What it does:

- loads the local JSONL corpus;
- runs the simple token-based retriever;
- prints ranked sources with scores.

This does not require MMORE.

## Debug prompt construction

```bash
PYTHONPATH=src python scripts/debug_prompting.py "How do I configure indexing?"
```

What it does:

- retrieves sources with the simple backend;
- builds the source-grounded prompt;
- prints the prompt that would be sent to an LLM.

## Prepare an answer prompt

Simple backend:

```bash
PYTHONPATH=src python scripts/prepare_answer.py "How do I configure indexing?" --backend simple
```

MMORE backend:

```bash
PYTHONPATH=src python scripts/prepare_answer.py "How do I configure indexing?" --backend mmore
```

The MMORE backend requires the MMORE corpus to be exported and indexed first.

## Generate a temporary extractive answer

```bash
PYTHONPATH=src python scripts/answer_question.py "How do I configure indexing?" --backend simple
```

What it does:

- retrieves sources;
- returns a simple answer from the top retrieved document;
- prints the source list.

This does not call an LLM yet.

## Extract Python documentation only

```bash
PYTHONPATH=src python scripts/extract_code_docs.py
```

What it does:

- reads the configured `code_path`;
- extracts Python module, class, function, and method documentation;
- writes `data/extracted_code_docs/code_docs.jsonl`.

This is useful for debugging the Python extractor independently.

## Export the corpus for MMORE

```bash
PYTHONPATH=src python scripts/export_mmore_corpus.py
```

What it does:

- reads `data/processed/corpus.jsonl`;
- converts each `DocumentRecord` into MMORE-compatible format;
- writes `data/processed/mmore_corpus.jsonl`.

## Build the MMORE index

```bash
PYTHONPATH=src python scripts/build_index.py
```

What it does:

- reads `configs/indexing_config.yaml`;
- uses `configs/mmore_index_config.yaml`;
- indexes `data/processed/mmore_corpus.jsonl` with MMORE;
- stores the index under `data/indexes/mmore/`.

## Run the Streamlit app

```bash
scripts/run_app.sh
```

Equivalent command:

```bash
PYTHONPATH=src streamlit run src/docask/app/streamlit_app.py
```

The Streamlit interface is still under development.
