# GitHelp Documentation

GitHelp is a conversational assistant for querying a software project's documentation and code-related knowledge in natural language.

The initial use case is the MMORE repository, but the architecture is designed to support other Python projects through project-specific configuration and optional project profiles.

GitHelp can be used in two ways:

- through the Streamlit interface, where a user selects a local project, builds a corpus, and asks questions;
- through command-line scripts, which are useful for debugging corpus construction, retrieval, prompting, and indexing.


```{toctree}
:maxdepth: 1
:caption: Getting started

getting_started/quickstart
getting_started/configuration
getting_started/commands
```

```{toctree}
:maxdepth: 1
:caption: Architecture

architecture/overview
architecture/repository_structure
architecture/data_flow
```

```{toctree}
:maxdepth: 1
:caption: Components

components/corpus_building
components/loaders_extractors
components/indexing
components/retrieval
components/rag_and_llm
components/streamlit_app
```

```{toctree}
:maxdepth: 1
:caption: Development

development/debugging
development/roadmap
```
