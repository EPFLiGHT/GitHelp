# Roadmap

GitHelp is currently an early but functional prototype.

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
- tests for corpus building, retrieval, prompting, project state, project builder, and project profiles;
- GitHub Actions workflow for running tests.

## Current limitations

- Public GitHub repository loading currently supports public repositories through local `git clone`.
- Existing GitHub clones are reused as-is and are not automatically updated.
- Streamlit currently supports local project paths as the main project setup mode.
- Building a corpus does not automatically rebuild the MMORE index.
- The `simple` backend is useful for newly built corpora, but it is not a semantic retriever.
- The MMORE backend depends on an existing MMORE index and configuration.
- LLM quality depends on the selected local model.
- Project profiles are currently lightweight heuristics, not a general evaluation-based reranking system.

## Next steps

1. Add an optional Streamlit action to export a project corpus to MMORE format.
2. Add an optional Streamlit action to build or rebuild the MMORE index.
3. Make backend selection clearer when the selected corpus and MMORE index may not match.
4. Add richer support for code-aware questions.
5. Add better source browsing in the Streamlit interface.
6. Add deployment instructions for local lab machines or servers.

## Future ideas

- dependency graph between modules and symbols;
- test and example extraction;
- richer code-aware retrieval;
- multiple saved projects in the UI;
- project selector for previously built corpora;
- evaluation set for retrieval quality;
- better UI for browsing sources;
- support for private GitHub repositories with authentication;
- Sphinx documentation deployment through GitHub Pages.
