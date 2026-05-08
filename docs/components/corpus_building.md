# Corpus building

Corpus building is the first main step of DocAsk.

It is orchestrated by:

```text
scripts/build_corpus.py
```

and implemented mainly in:

```text
src/docask/corpus/builder.py
```

## What `build_corpus.py` does

`build_corpus.py` reads the project configuration and builds a unified corpus.

Depending on `configs/project_config.yaml`, it can include:

- Markdown and reStructuredText documentation;
- Python files for docstrings and signatures through `ast`;
- YAML configuration files;
- repository structure.

## Command

```bash
PYTHONPATH=src python scripts/build_corpus.py
```

## Output

```text
data/processed/corpus.jsonl
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

## Why JSONL?

JSONL is simple and useful here because:

- each document is independent;
- it can be inspected line by line;
- it can be streamed by later indexing pipelines;
- it is easy to convert to other formats.
