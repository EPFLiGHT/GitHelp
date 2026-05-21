# Repository structure

DocAsk uses a `src/` layout.

```text
docask/
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
├── configs/
├── data/
├── docs/
├── scripts/
├── app/
├── src/
│   └── docask/
└── tests/
```

## Top-level folders

| Folder | Role |
|---|---|
| `app/` | Streamlit application entry point. |
| `configs/` | YAML configuration files for app settings, indexed project defaults, retrieval, and indexing. |
| `data/` | Local generated data: corpora, app state, extracted docs, and indexes. |
| `docs/` | Project documentation, optionally built with Sphinx/MyST. |
| `scripts/` | Command-line utilities for building, debugging, indexing, and running DocAsk. |
| `src/docask/` | Main Python package. |
| `tests/` | Automated tests. |

## Generated data layout

DocAsk can still use the default corpus path:

```text
data/processed/corpus.jsonl
```

The Streamlit project setup flow creates project-specific data:

```text
data/projects/
└── <project_name>/
    ├── project_config.yaml
    ├── corpus.jsonl
    └── mmore_corpus.jsonl       # optional, if exported for MMORE
```

The Streamlit app stores local UI state in:

```text
data/app_state.json
```

This file is machine-specific and should normally not be committed.

## Python package structure

```text
src/docask/
├── config.py
├── data_models.py
├── loaders/
├── extractors/
├── corpus/
├── indexing/
├── retrieval/
├── rag/
├── project_profiles/
├── projects/
└── utils/
```

## Component responsibilities

```text
loaders/           -> load Markdown, YAML, and repository structure documents
extractors/        -> extract documentation from Python code
corpus/            -> merge all sources into corpus.jsonl
indexing/          -> convert and index the corpus with MMORE
retrieval/         -> retrieve relevant documents
rag/               -> build prompts and produce answers
project_profiles/ -> project-specific query expansion, filtering, reranking, and direct answers
projects/          -> project setup, generated configs, corpus paths, app state
utils/             -> shared paths and helpers
```

The goal is that a reader can understand the repository without opening every file.
