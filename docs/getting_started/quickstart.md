# Quickstart

This page explains the shortest path to run GitHelp locally.

The recommended way to use GitHelp is the Streamlit interface. The command-line scripts remain available for debugging and development.

## 1. Install the project

From the root of the `GitHelp` repository:

```bash
python -m pip install -e .
```

This installs Streamlit, the local Qwen dependencies, and MMORE. The native
MMORE backend is heavier than the simple backend and may download models during
its first indexing or retrieval run.

## 2. Launch the Streamlit app

From the root of the `githelp` repository:

```bash
streamlit run app/streamlit_app.py
```

The interface opens locally, usually at:

```text
http://localhost:8501/
```

## 3. Select a project

In the Streamlit interface, use the **Project setup** section.

For the MMORE use case, either enter the local path to the MMORE repository:

```text
/Users/<user>/path/to/mmore
```

or select the GitHub repository option and enter:

```text
https://github.com/swiss-ai/mmore
```

For GitHub URLs, GitHelp clones the repository into `data/repositories/` and
then runs the same corpus, indexing, retrieval, and RAG pipeline on that local
copy.

## 4. Prepare the project

Click one of the project build buttons:

```text
Build simple index
Build MMORE index
```

GitHelp generates a dedicated project folder:

```text
data/projects/<project_name>/
```

For MMORE, both modes create for example:

```text
data/projects/mmore/project_config.yaml
data/projects/mmore/corpus.jsonl
```

The generated corpus can include:

- Markdown and reStructuredText documentation;
- Python module, class, function, and method docstrings, plus function and
  method signatures extracted with `ast`;
- YAML configuration files;
- a synthetic repository structure document.

## 5. Ask questions

After the corpus is built, use the chat input at the bottom of the
**Conversation** section. The input remains disabled until a valid project
corpus is available.

### Choose an indexing mode

GitHelp supports two indexing modes.

#### Simple index

The simple index builds a GitHelp JSONL corpus and uses the local simple retriever.

Use it when:

- you want a quick setup;
- you are debugging corpus extraction;
- MMORE is not installed or not configured.

#### MMORE index

The MMORE index is the main semantic retrieval mode. Retrieval quality should
still be checked against the displayed sources; the current evaluation is not
large enough to claim that MMORE is better for every question.

It builds the GitHelp corpus, exports it to MMORE format, and builds the MMORE index.

Use it when:

- MMORE is installed;
- you want to use the main retrieval backend;
- the project is ready to be indexed.

After building the MMORE index, select:

```text
Retrieval backend: mmore
```

The simple backend remains the recommended first run for debugging or quick
corpus checks.

Example questions:

```text
How do I configure indexing?
Which Milvus parameters are used in the ColPali config?
Where are the example configs located?
```

## 6. Inspect sources

By default, GitHelp displays retrieved sources under the answer.

The sidebar options let you:

- show or hide retrieved sources;
- show full source content;
- show debug information;
- switch between `simple` and `mmore` retrieval;
- enable or disable LLM generation.

When the `mmore` backend is selected, the diagnostics distinguish native index
retrieval from the lexical corpus fallback:

```text
native_index
corpus_fallback
```

The fallback searches the exported `mmore_corpus.jsonl` lexically. It does not
use native MMORE/Milvus vector retrieval.

## 7. Persistent app state

GitHelp stores the last selected project and UI settings in:

```text
data/app_state.json
```

This allows the interface to restore the previous project, corpus path, backend, and display options after closing and reopening Streamlit.

This file is local state and should normally not be committed.

## 8. Optional: command-line corpus build

The default command still works:

```bash
python scripts/build_corpus.py
```

It reads:

```text
configs/project_config.yaml
```

and writes:

```text
data/processed/corpus.jsonl
```

You can also build a project-specific corpus manually:

```bash
python scripts/build_corpus.py \
  --config data/projects/mmore/project_config.yaml \
  --output-path data/projects/mmore/corpus.jsonl
```

## 9. Optional: MMORE indexing

The `mmore` backend retrieves from an MMORE index. Building a corpus alone is not enough to update that index.

For a full MMORE-backed workflow, the steps are:

```text
build_corpus.py
→ export_mmore_corpus.py
→ build_index.py
→ ask with backend mmore
```

For local development, the `simple` backend is useful when you want to inspect
the GitHelp corpus before exporting and indexing it with MMORE.

```{note}
Project corpora and MMORE export files are stored separately. The default app
configuration nevertheless uses the MMORE-specific profile, and native MMORE
indexing currently uses one shared `mmore_docs` collection. Use
`project_profile: generic` for another project and rebuild the native index when
switching its indexed corpus.
```
