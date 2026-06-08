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
python scripts/debug_retrieval.py \
  "How do I configure indexing?" \
  --corpus-path data/projects/mmore/corpus.jsonl
```

## MMORE retriever

File:

```text
src/githelp/retrieval/mmore_retriever.py
src/githelp/retrieval/mmore_native.py
src/githelp/retrieval/mmore_subprocess.py
src/githelp/retrieval/mmore_corpus.py
src/githelp/retrieval/mmore_result_mapping.py
```

The MMORE retriever:

- runs native MMORE retrieval in an isolated subprocess;
- loads a MMORE retriever from config inside that subprocess;
- calls `retriever.retrieve(...)` when native retrieval is available;
- parses GitHelp metadata from retrieved text;
- converts raw MMORE results back into `RetrievalResult` objects.
- falls back to `mmore_corpus.jsonl` if the native process fails locally.

Retrieved sources are tagged with one of these metadata values:

```text
native_index
corpus_fallback
```

Command example:

```bash
python scripts/prepare_answer.py \
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

For a project corpus built from the Streamlit interface, `simple` is useful for
quick deterministic checks:

```text
backend simple
```

For the main MMORE workflow, use:

```text
backend mmore
```

The `mmore` backend attempts native MMORE index retrieval first. If that native
process fails, GitHelp falls back to the exported `mmore_corpus.jsonl` next to
the selected project corpus so Streamlit can continue answering.
