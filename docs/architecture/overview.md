# Architecture overview

DocAsk is organized around a simple idea: all sources are converted into the same internal document format before retrieval.

## High-level flow

```text
Target project repository
        |
        |  Markdown / RST docs
        |  Python source files
        |  YAML config files
        |  repository tree
        v
DocAsk loaders and extractors
        v
DocumentRecord objects
        v
corpus.jsonl
        v
retrieval backend
        |-------------------------------|
        |                               |
        v                               v
simple retriever                MMORE retriever
(local debugging)               (target backend)
        |                               |
        |-------------------------------|
        v
retrieved sources
        v
RAG prompt construction
        v
answer generation
```

## Main design choices

DocAsk separates the pipeline into clear blocks:

| Block | Role |
|---|---|
| `loaders/` | Load source files that are already documentation-like. |
| `extractors/` | Extract documentation from source code. |
| `corpus/` | Combine all sources into one corpus. |
| `indexing/` | Export and index the corpus with MMORE. |
| `retrieval/` | Retrieve relevant documents. |
| `rag/` | Build prompts and generate answers. |
| `app/` | User interface. |

## Why keep a DocAsk format?

DocAsk uses its own `DocumentRecord` format instead of exposing MMORE everywhere.

This keeps the project modular:

- the corpus can be inspected before indexing;
- the simple retriever can run without MMORE;
- MMORE can be replaced or updated without rewriting loaders;
- retrieved sources keep consistent metadata for citations.
