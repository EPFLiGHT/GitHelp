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

## Conversation layout

The main page is organized as a chat assistant:

- conversation messages render chronologically with `st.chat_message`;
- the newest user and assistant messages appear at the bottom;
- `st.chat_input` stays at the bottom of the page for the next question;
- **Clear chat** sits beside the conversation heading;
- the input remains disabled until a project corpus is available.

Project and retrieval settings remain in compact controls so the conversation
stays visually dominant. The same Streamlit layout is used locally and in the
Docker deployment.

## Visual identity

The compact header uses the project logo from:

```text
docs/_static/images/logo.png
```

The path is resolved relative to the application source, not the shell's
working directory, so it is the same locally and under Docker's `/app`
working directory. The pastel-green primary color is defined in
`.streamlit/config.toml`; a small complementary CSS layer in
`app/streamlit_theme.py` styles buttons, chat accents, focus states, and
neutral user/assistant avatars for light and dark displays.

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

The `simple` backend reads the generated `corpus.jsonl` directly and is useful
for deterministic debugging.

The `mmore` backend is the main MMORE workflow. It attempts native MMORE index
retrieval first and can fall back to the exported `mmore_corpus.jsonl` if the
native process fails locally. The fallback uses lexical ranking rather than
native MMORE/Milvus vector search.

The answer caption and source panels show the actual MMORE retrieval mode:

```text
native_index
corpus_fallback
```

Project corpora and exports are stored in project-specific folders, but the
default profile and native collection are global. The default config uses the
MMORE profile, and **Build MMORE index** writes the shared `mmore_docs`
collection. When switching projects, use the appropriate app config and rebuild
the native index before relying on `native_index` results.

## LLM caching

The app uses Streamlit resource caching to avoid reloading the local LLM provider for every question.

The first LLM query may take longer because the model is loaded. Later queries reuse the cached provider unless the config cache is cleared.

## Sources and diagnostics

Retrieved sources are enabled by default but appear in a collapsed **Latest
answer sources and diagnostics** section below the conversation.

The sidebar can:

- hide retrieved sources;
- show full source content;
- show debug information.

The debug panel shows the original question, the standalone query used for
retrieval, and whether the question was detected as a follow-up. It also marks
ambiguous follow-ups that were stopped for clarification before retrieval.

This makes the interface useful both for users and for development debugging.
