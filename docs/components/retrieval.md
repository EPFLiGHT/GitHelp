# Retrieval

Retrieval is the step that finds relevant documents for a user question.

GitHelp currently supports two retrieval backends:

```text
simple
mmore
```

## Shared result format

File:

```text
src/githelp/retrieval/base.py
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
src/githelp/retrieval/simple_retriever.py
```

The simple retriever is a local debugging and dynamic-project backend.

It:

- reads a selected `corpus.jsonl`;
- tokenizes the query and documents;
- ranks documents with overlap-based heuristics;
- adds boosts for exact symbols, signatures, modules, titles, and user-facing documentation.

It does not use embeddings or MMORE.

Command:

```bash
PYTHONPATH=src python scripts/debug_retrieval.py \
  "How do I configure indexing?" \
  --corpus-path data/projects/mmore/corpus.jsonl
```

## MMORE retriever

File:

```text
src/githelp/retrieval/mmore_retriever.py
```

The MMORE retriever:

- loads a MMORE retriever from config;
- calls `retriever.retrieve(...)`;
- parses GitHelp metadata from retrieved text;
- converts raw MMORE results back into `RetrievalResult` objects.

Command example:

```bash
PYTHONPATH=src python scripts/prepare_answer.py \
  "How do I configure indexing?" \
  --backend mmore
```

## Retriever factory

File:

```text
src/githelp/retrieval/retriever_factory.py
```

This file gives the rest of GitHelp one entry point:

```python
retrieve_documents(...)
```

It chooses the backend based on:

```text
simple
mmore
```

## Project profiles

Retrieval results can be refined by a project profile.

Project profiles live in:

```text
src/githelp/project_profiles/
```

They can:

- expand queries;
- filter irrelevant sources;
- rerank retrieved results;
- answer some structured questions directly.

This keeps the core GitHelp retrieval pipeline generic while allowing MMORE-specific improvements to remain isolated.

## Backend choice

For a project corpus built from the Streamlit interface, use:

```text
backend simple
```

unless the corresponding MMORE index has also been rebuilt.

The `mmore` backend retrieves from the configured MMORE index, not directly from the selected JSONL corpus.
