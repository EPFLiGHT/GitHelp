# Streamlit app

The Streamlit app is the main user-facing interface for GitHelp.

Current file:

```text
app/streamlit_app.py
```

## Goal

The app lets a user:

- select a local software project;
- build a GitHelp corpus for that project;
- ask questions about the selected project;
- choose the retrieval backend;
- enable or disable LLM generation;
- inspect retrieved sources;
- keep the last selected project and settings after reopening the app.

## Run command

```bash
streamlit run app/streamlit_app.py
```

The app usually opens at:

```text
http://localhost:8501/
```

## Project setup

The app contains a **Project setup** section.

Supported modes:

```text
Local project path
Public GitHub repository URL
```

For GitHub URLs, GitHelp clones the repository into:

```text
data/repositories/<owner>-<repo>/
```

It then reuses the same project-specific corpus and indexing pipeline as local paths.

When a local project path is provided, GitHelp builds the corpus directly from that folder.

For example:

```text
/path/to/mmore
```

generates:

```text
data/projects/mmore/project_config.yaml
data/projects/mmore/corpus.jsonl
```

## Persistent state

The app stores local UI state in:

```text
data/app_state.json
```

This can include:

- last project name;
- last project path;
- last corpus path;
- last project config path;
- selected retrieval backend;
- number of sources;
- whether LLM is enabled;
- source display options;
- debug display options.

This file is local and should normally not be committed.

## Retrieval backend

The app supports:

```text
simple
mmore
```

For a corpus built from the interface, the safest first option is:

```text
simple
```

The `simple` backend reads the generated `corpus.jsonl` directly.

The `mmore` backend should be used when the MMORE index has been built for the relevant corpus.

## LLM caching

The app uses Streamlit resource caching to avoid reloading the local LLM provider for every question.

The first LLM query may take longer because the model is loaded. Later queries reuse the cached provider unless the config cache is cleared.

## Sources

Retrieved sources are displayed by default.

The sidebar can:

- hide retrieved sources;
- show full source content;
- show debug information.

This makes the interface useful both for users and for development debugging.
