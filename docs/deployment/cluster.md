# Using GitHelp on the EPFL lab server

GitHelp is deployed on the EPFL GPU server and is accessible from the EPFL
network or VPN at:

<http://gpu217.rcp.epfl.ch:1312/githelp/>

The final `/` is important for Streamlit to load correctly behind the
`/githelp` route.

This page is for GitHelp users. Server administration is documented in
{doc}`maintainer`, and operational problems are covered in
{doc}`troubleshooting`.

## What GitHelp does

GitHelp lets users ask natural-language questions about a selected software
repository. It builds an inspectable corpus from:

- Markdown and reStructuredText documentation;
- Python module, class, function, and method docstrings;
- function and method signatures;
- YAML configuration files;
- repository structure metadata.

Typical questions include:

```text
How do I install this project?
How do I configure indexing?
Where is this function documented?
What does this configuration file do?
Which sources support the answer?
```

GitHelp retrieves project sources before answering. Important answers should
still be checked against the displayed evidence.

## 1. Open the interface

Open:

<http://gpu217.rcp.epfl.ch:1312/githelp/>

If the page is not reachable, connect to the EPFL VPN and try again.

## 2. Select a repository

Open **Project settings and index management**, then choose one source:

- **Public GitHub repository URL** clones or reuses a public repository under
  `/app/data/repositories/`;
- **Local project path** uses a repository already visible inside the
  container.

GitHelp runs inside Docker. Local paths entered in the interface must therefore
be container paths, for example:

```text
/app/data/repositories/swiss-ai-mmore
```

Do not enter the corresponding host path, such as:

```text
/home/githelp/GitHelp/data/repositories/swiss-ai-mmore
```

## 3. Prepare the project

Start with **Build simple index**. Despite the button name, this mode builds the
GitHelp `corpus.jsonl` and searches it directly with the lexical retriever. It is
the fastest way to verify extraction and source quality.

Generated project files are stored under:

```text
/app/data/projects/<project_name>/
```

Use **Build MMORE index** when native MMORE retrieval is needed. This single
action performs all three stages:

```text
build corpus → export mmore_corpus.jsonl → build native MMORE index
```

The first MMORE build may download and load embedding models. The persistent
Hugging Face cache makes later runs faster.

## 4. Choose the retrieval backend

The sidebar provides two backends:

- `simple` performs deterministic lexical retrieval over the selected
  `corpus.jsonl`;
- `mmore` first attempts native MMORE/Milvus retrieval.

If the native MMORE child process fails, GitHelp can fall back to lexical
retrieval over the exported `mmore_corpus.jsonl`. Check the diagnostics before
interpreting a result:

```text
native_index
corpus_fallback
```

## 5. Ask questions and inspect sources

Use the chat input at the bottom of the **Conversation** section. The input is
enabled once a valid corpus exists.

Recommended first questions:

```text
How do I install this project?
What are the main modules of this repository?
How do I configure indexing?
```

The sidebar can show or hide retrieved sources, display their full content, and
show retrieval diagnostics. Inspect these sources whenever accuracy matters.

## Current user-facing limitations

- Only public GitHub repositories can be cloned automatically.
- Existing clones are reused without an automatic `git pull`.
- Python is the only language with API/docstring extraction.
- Project corpora and MMORE exports are isolated, but the default profile and
  native `mmore_docs` index are shared.
- The first local LLM or MMORE model load can be slow.
- The interface is intended for internal EPFL/lab use.

For server commands, GPU verification, index rebuilding, and deployment paths,
continue with {doc}`maintainer`.
