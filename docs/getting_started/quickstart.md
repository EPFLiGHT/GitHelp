# Quickstart

This page explains the shortest path to run GitHelp locally.

The recommended way to use GitHelp is the Streamlit interface. The command-line scripts remain available for debugging and development.

## 1. Install the project

From the root of the `githelp` repository:

```bash
python -m pip install -e .
```

If you use the local Qwen provider, make sure the LLM dependencies are installed:

```bash
python -m pip install transformers torch accelerate
```

If Streamlit is not already installed:

```bash
python -m pip install streamlit
```

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

For the MMORE use case, enter the local path to the MMORE repository, for example:

```text
/Users/<user>/path/to/mmore
```

GitHelp can currently build a corpus from a local project path.

Public GitHub repository support is planned, but the main supported workflow for now is local project selection.

## 4. Build the corpus

Click:

```text
Build corpus
```

GitHelp generates a dedicated project folder:

```text
data/projects/<project_name>/
```

For MMORE, this creates for example:

```text
data/projects/mmore/project_config.yaml
data/projects/mmore/corpus.jsonl
```

The generated corpus can include:

- Markdown and reStructuredText documentation;
- Python docstrings and signatures extracted with `ast`;
- YAML configuration files;
- a synthetic repository structure document.

## 5. Ask questions

After the corpus is built, use the **Ask questions** section.

### Choose an indexing mode

GitHelp supports two indexing modes.

#### Simple index

The simple index builds a GitHelp JSONL corpus and uses the local simple retriever.

Use it when:

- you want a quick setup;
- you are debugging corpus extraction;
- MMORE is not installed or not configured.

#### MMORE index

The MMORE index is the recommended mode for better retrieval quality.

It builds the GitHelp corpus, exports it to MMORE format, and builds the MMORE index.

Use it when:

- MMORE is installed;
- you want to use the main retrieval backend;
- the project is ready to be indexed.

After building the MMORE index, select:

```text
Retrieval backend: mmore

The simple backend remains available for debugging or quick corpus checks.

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
PYTHONPATH=src python scripts/build_corpus.py
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
PYTHONPATH=src python scripts/build_corpus.py \
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

For local development and newly built corpora, use the `simple` backend first.
