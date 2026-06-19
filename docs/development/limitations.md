# Limitations

This page lists the main current limitations and the design choices used to
handle them.

## Repository Loading

GitHelp currently supports public GitHub repositories through local `git clone`.
Private repositories are not handled yet because they require authentication and
credential-management decisions.

Existing clones under `data/repositories/` are reused as local folders. GitHelp
does not automatically pull updates from the remote repository.

## Corpus and Index Freshness

Building a GitHelp corpus writes:

```text
data/projects/<project_name>/corpus.jsonl
```

This does not automatically rebuild the MMORE index. For MMORE retrieval, the
project corpus must also be exported and indexed:

```text
corpus.jsonl -> mmore_corpus.jsonl -> MMORE index
```

## MMORE Native Retrieval

The `mmore` backend first attempts native MMORE retrieval in a child process.
This keeps the Streamlit process alive if local native dependencies crash.

When the native process succeeds, retrieved sources are tagged with:

```text
native_index
```

When the native process fails, GitHelp falls back to the exported
`mmore_corpus.jsonl` and tags retrieved sources with:

```text
corpus_fallback
```

The fallback still answers from the MMORE-formatted corpus, but it does not use
the native Milvus vector search path.

## Local Environment Sensitivity

MMORE, Milvus Lite, PyTorch, Transformers, and OpenMP native libraries can be
sensitive to the Python and package versions installed locally.

Known examples:

- MMORE sparse indexing currently requires Transformers 4.x, so GitHelp pins
  `transformers>=4.51.0,<5`.
- Some macOS environments can hit an OpenMP runtime conflict while loading
  native ML libraries.
- Python 3.14 may expose dependency compatibility issues earlier than Python
  3.11 or 3.12.

## LLM Provider

The default LLM provider uses a local Qwen model through Hugging Face
Transformers. Answer quality, latency, and memory usage depend on the selected
model and local hardware.

The `dummy` provider remains available for tests and pipeline debugging without
loading a model.

## Retrieval Quality

GitHelp combines several retrieval improvements:

- project profiles;
- query expansion;
- filtering and reranking;
- source-grounded prompts;
- expected-source retrieval evaluation.

It is still not a complete code intelligence system. Future work could include
dependency graphs, richer symbol indexing, tests/examples extraction, and
evaluation-driven reranking.
