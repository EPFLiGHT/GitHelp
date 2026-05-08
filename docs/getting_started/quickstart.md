# Quickstart

This page explains the shortest path to run DocAsk locally.

## 1. Install the project

From the root of the `docask` repository:

```bash
python -m pip install -e .
```

## 2. Configure the target project

The main file to edit is:

```text
configs/project_config.yaml
```

For the MMORE use case, it should contain paths similar to:

```yaml
project_name: mmore
package_name: mmore

repo_path: ../../mmore
docs_path: ../../mmore/docs/source
code_path: ../../mmore/src/mmore

include_yaml_configs: true
yaml_config_paths:
  - ../../mmore/examples
  - ../../mmore/production-config

include_repo_structure: true
repo_structure_max_depth: 4
```

The important paths are:

- `repo_path`: root of the project being indexed;
- `docs_path`: documentation folder of the target project;
- `code_path`: Python package folder used for docstring extraction;
- `yaml_config_paths`: folders where YAML examples or production configs are stored.

## 3. Build the corpus

```bash
PYTHONPATH=src python scripts/build_corpus.py
```

This creates:

```text
data/processed/corpus.jsonl
```

The corpus can include:

- Markdown and reStructuredText documentation;
- Python docstrings and signatures extracted with `ast`;
- YAML configuration files;
- a synthetic repository structure document.

## 4. Preview the corpus

```bash
PYTHONPATH=src python scripts/preview_corpus.py --limit 2
```

This prints the first extracted documents. It is the fastest way to check that the paths are correct.

## 5. Test the simple retriever

```bash
PYTHONPATH=src python scripts/debug_retrieval.py "How do I configure indexing?"
```

This uses the local prototype retriever. It does not require MMORE indexing.

## 6. Prepare a prompt

```bash
PYTHONPATH=src python scripts/prepare_answer.py "How do I configure indexing?" --backend simple
```

This retrieves sources and formats the prompt that would be sent to an LLM.

## 7. Optional: use MMORE indexing and retrieval

Export the corpus to MMORE format:

```bash
PYTHONPATH=src python scripts/export_mmore_corpus.py
```

Build the MMORE index:

```bash
PYTHONPATH=src python scripts/build_index.py
```

Then prepare an answer with the MMORE backend:

```bash
PYTHONPATH=src python scripts/prepare_answer.py "How do I configure indexing?" --backend mmore
```
