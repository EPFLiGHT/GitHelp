# Limitations

This page lists the main current limitations and the design choices used to
handle them.

## Repository Loading

GitHelp currently supports public GitHub repositories through local `git clone`.
Private repositories are not handled yet because they require authentication and
credential-management decisions.

Existing clones under `data/repositories/` are reused as local folders. GitHelp
does not automatically pull updates from the remote repository.

Repository ingestion is optimized for Python projects. Documentation, YAML, and
the repository tree can still be collected from other repositories, but API
extraction currently understands Python syntax only.

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

The corpus and exported MMORE JSONL are project-specific. Native MMORE indexing
currently uses one shared Milvus Lite database and the `mmore_docs` collection;
rebuilding resets that database and replaces the previously indexed project.

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
the native Milvus vector search path. It ranks records with the simple lexical
retriever.

For some code-, symbol-, and filename-oriented questions, the high-level
answering pipeline also merges simple lexical candidates with MMORE candidates.
Selecting the MMORE backend therefore does not guarantee that every final
source originated from the native index.

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

The repository does not currently include an external or hosted LLM provider.

## Project Profiles

The active profile is selected globally from `configs/app_config.yaml`. The
default is the MMORE-specific profile, and building a project-specific corpus
does not update it automatically. Use `project_profile: generic` for another
project unless it requires its own profile.

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

The current evaluation set contains ten MMORE questions, with expected-source
annotations for only a small subset. It is useful as a regression check but is
not a systematic benchmark of retrieval or answer quality.
