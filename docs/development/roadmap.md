# Roadmap

DocAsk is currently an early prototype.

## Implemented

- Markdown and reStructuredText loading;
- Python docstring extraction with `ast`;
- signature extraction;
- YAML config loading;
- repository structure summary;
- unified `DocumentRecord` format;
- JSONL corpus generation;
- MMORE-compatible export;
- MMORE indexing wrapper;
- MMORE retrieval adapter;
- local simple retriever for debugging;
- source-grounded prompt construction;
- temporary extractive answerer.

## Next steps

1. Add LLM generation.
2. Replace the temporary extractive answerer.
3. Build a minimal Streamlit chat interface.
4. Display sources under each answer.
5. Improve reranking for configuration and code questions.
6. Add selected code snippets when docstrings are insufficient.
7. Add tests for corpus building and retrieval behavior.
8. Add Sphinx documentation deployment through GitHub Pages.

## Future ideas

- dependency graph between modules and symbols;
- test and example extraction;
- richer code-aware retrieval;
- multiple project support;
- evaluation set for retrieval quality;
- better UI for browsing sources.
