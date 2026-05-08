# Retrieval

Retrieval is the step that finds relevant documents for a user question.

DocAsk currently supports two retrieval backends:

```text
simple
mmore
```

## Shared result format

File:

```text
src/docask/retrieval/base.py
```

The shared result type is:

```python
RetrievalResult
```

It contains:

- the retrieved `DocumentRecord`;
- a retrieval score.

## Simple retriever

File:

```text
src/docask/retrieval/simple_retriever.py
```

The simple retriever is a local debugging backend.

It:

- reads `data/processed/corpus.jsonl`;
- tokenizes the query and documents;
- ranks documents with overlap-based heuristics;
- adds boosts for exact symbols, signatures, modules, titles, and user-facing documentation.

It does not use embeddings or MMORE.

Command:

```bash
PYTHONPATH=src python scripts/debug_retrieval.py "How do I configure indexing?"
```

## MMORE retriever

File:

```text
src/docask/retrieval/mmore_retriever.py
```

The MMORE retriever:

- loads a MMORE retriever from config;
- calls `retriever.retrieve(...)`;
- parses DocAsk metadata from retrieved text;
- converts raw MMORE results back into `RetrievalResult` objects.

Command example:

```bash
PYTHONPATH=src python scripts/prepare_answer.py "How do I configure indexing?" --backend mmore
```

## Retriever factory

File:

```text
src/docask/retrieval/retriever_factory.py
```

This file gives the rest of DocAsk one entry point:

```python
retrieve_documents(...)
```

It chooses the backend based on:

```text
simple
mmore
```
