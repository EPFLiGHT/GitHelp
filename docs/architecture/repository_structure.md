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
├── src/
│   └── docask/
└── tests/
```

## Top-level folders

| Folder | Role |
|---|---|
| `configs/` | YAML configuration files for the indexed project, retrieval, indexing, and app. |
| `data/` | Local generated data: corpus files, extracted docs, indexes. |
| `docs/` | Project documentation, optionally built with Sphinx/MyST. |
| `scripts/` | Command-line utilities for building, debugging, indexing, and running DocAsk. |
| `src/docask/` | Main Python package. |
| `tests/` | Future automated tests. |

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
├── app/
└── utils/
```

## Component responsibilities

```text
loaders/      -> load Markdown, YAML, and repository structure documents
extractors/   -> extract documentation from Python code
corpus/       -> merge all sources into corpus.jsonl
indexing/     -> convert and index the corpus with MMORE
retrieval/    -> retrieve relevant documents
rag/          -> build prompts and produce answers
app/          -> Streamlit interface
utils/        -> shared paths and helpers
```

The goal is that a reader can understand the repository without opening every file.
