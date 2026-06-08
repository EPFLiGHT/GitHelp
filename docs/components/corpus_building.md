# Corpus building

Corpus building is the first main step of GitHelp.

It is orchestrated by:

```text
scripts/build_corpus.py
```

and implemented mainly in:

```text
src/githelp/corpus/builder.py
```

## What `build_corpus.py` does

`build_corpus.py` reads a project configuration and builds a unified corpus.

Depending on the project config, it can include:

- Markdown and reStructuredText documentation;
- Python files for docstrings and signatures through `ast`;
- YAML configuration files;
- repository structure.

## Default command

```bash
PYTHONPATH=src python scripts/build_corpus.py
```

This reads:

```text
configs/project_config.yaml
```

and writes:

```text
data/processed/corpus.jsonl
```

## Dynamic project command

The script can also build a corpus for a project-specific config:

```bash
PYTHONPATH=src python scripts/build_corpus.py \
  --config data/projects/mmore/project_config.yaml \
  --output-path data/projects/mmore/corpus.jsonl
```

This is the mechanism used by the Streamlit app when a user selects a local project and clicks **Build corpus**.

## Output

Default output:

```text
data/processed/corpus.jsonl
```

Project-specific output:

```text
data/projects/<project_name>/corpus.jsonl
```

## Source breakdown

A successful run prints a breakdown by `source_type`, for example:

```text
Built corpus with 545 documents
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

## Project-specific generated config

The Streamlit project setup flow generates:

```text
data/projects/<project_name>/project_config.yaml
```

This file contains absolute paths to the selected local project.

## Why JSONL?

JSONL is simple and useful here because:

- each document is independent;
- it can be inspected line by line;
- it can be streamed by later indexing pipelines;
- it is easy to convert to other formats.
