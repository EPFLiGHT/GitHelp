# Roadmap

GitHelp is a functional repository RAG application with local, Docker, and EPFL
GPU-server workflows. This page distinguishes implemented behavior from the
remaining multi-project and evaluation work.

## Implemented

- Markdown and reStructuredText loading;
- Python docstring extraction with `ast`;
- signature extraction;
- YAML config loading;
- repository structure summary;
- unified `DocumentRecord` format;
- JSONL corpus generation;
- project-specific corpus generation under `data/projects/`;
- persisted Streamlit app state under `data/app_state.json`;
- MMORE-compatible export;
- MMORE indexing wrapper;
- MMORE retrieval adapter;
- local simple retriever for debugging and dynamic project corpora;
- source-grounded prompt construction;
- local Qwen LLM provider through Hugging Face Transformers;
- LLM-based answer generation;
- cached LLM provider in Streamlit;
- optional extractive answering path;
- project profiles for project-specific query expansion, filtering, reranking, and direct answers;
- MMORE project profile with deterministic Milvus parameter answers;
- public GitHub repository cloning into local GitHelp-managed folders;
- command-line GitHub preparation for the simple backend;
- retrieval evaluation script for benchmark question sets;
- expected-source checks for retrieval evaluation;
- Streamlit interface for project setup, corpus building, question answering, and source inspection;
- Streamlit actions for building the corpus, exporting it to MMORE format, and
  building or rebuilding the native MMORE index;
- conversational Streamlit layout with lightweight follow-up resolution;
- tests for corpus building, retrieval, prompting, project state, project builder, and project profiles;
- GitHub Actions workflow for running tests;
- Sphinx documentation deployment through GitHub Pages;
- CUDA-enabled Docker packaging and EPFL server deployment through Docker
  Compose and Traefik.

## Current limitations

- GitHub repository loading supports public repositories through local `git clone`.
- Existing GitHub clones are reused as-is and are not automatically updated.
- Building a corpus does not automatically rebuild the MMORE index.
- The `simple` backend is useful for newly built corpora, but it is not a semantic retriever.
- Native MMORE retrieval depends on an existing MMORE index and compatible
  local dependencies; failures use a lexical corpus fallback.
- Project corpora are isolated, but the active profile and native `mmore_docs`
  collection are still global.
- LLM quality depends on the selected local model.
- Project profiles are currently lightweight heuristics, not a general evaluation-based reranking system.
- Code extraction is Python-specific and indexes documented APIs rather than
  complete implementation bodies or dependency graphs.
- The evaluation set is preliminary and only partially annotated.

## Future ideas

- dependency graph between modules and symbols;
- test and example extraction;
- richer code-aware retrieval;
- support for private GitHub repositories with authentication;
- optional external LLM providers;
- automated index freshness checks;
- evaluation-driven reranking.
