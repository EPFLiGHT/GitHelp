# DocAsk

DocAsk is a conversational assistant for querying a software project's documentation and code-related knowledge in natural language.

The initial use case is the [MMORE](https://github.com/swiss-ai/mmore) repository. DocAsk can use MMORE internally for indexing and retrieval, while also providing a simpler project-level interface through Streamlit.

Full documentation is available here:

➡️ [DocAsk documentation](https://epflight.github.io/docask/)

---

## Goal

DocAsk aims to help users ask questions about a software project, such as:

- How do I install or run the project?
- How do I configure indexing or retrieval?
- Where is a specific module implemented?
- What is the signature of a function?
- What does a class or method do?
- What does an example configuration file look like?
- Where are documentation pages, configs, tests, or examples located?

The longer-term goal is to support multiple repositories by combining several source types:

- written documentation;
- Python docstrings and signatures;
- YAML configuration examples;
- repository structure summaries;
- later, selected code snippets, tests, and richer code-aware retrieval.

---

## Current architecture

```text
target project repository
        ↓
DocAsk loaders and extractors
        ↓
DocumentRecord objects
        ↓
corpus.jsonl
        ↓
retrieval backend
        ├── simple local retriever
        └── MMORE-compatible export → MMORE indexing → MMORE retrieval
        ↓
project profile
        ├── optional query expansion
        ├── optional filtering / reranking
        └── optional direct answers for structured questions
        ↓
prompt construction
        ↓
answer generation
        ├── extractive answerer
        └── local LLM provider
        ↓
Streamlit interface