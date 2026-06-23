# Data flow

This page explains how information moves through GitHelp.

## Step 1: project selection

GitHelp starts from a target project repository.

The Streamlit interface lets a user select a local project path. For example, the MMORE repository may be located at:

```text
/path/to/mmore
```

GitHelp then creates a project-specific working folder:

```text
data/projects/<project_name>/
```

For MMORE:

```text
data/projects/mmore/
```

## Step 2: project configuration

GitHelp generates or reads a project configuration file.

For a Streamlit-selected project, this is usually:

```text
data/projects/<project_name>/project_config.yaml
```

For older command-line workflows, the default config remains:

```text
configs/project_config.yaml
```

The project config points to:

```text
docs_path          -> Markdown and RST documentation
code_path          -> Python source code
yaml_config_paths  -> YAML example or production configs
repo_path          -> repository structure
```

## Step 3: normalized records

Each source is converted into a `DocumentRecord`.

A `DocumentRecord` contains:

- a unique `doc_id`;
- textual `content`;
- a `source_type`;
- optional source metadata such as path, title, module, symbol, and signature.

Example source types:

```text
markdown_section
python_module
python_class
python_function
python_method
example_config
production_config
repo_structure
```

## Step 4: corpus file

All records are saved to JSONL.

Default command-line corpus:

```text
data/processed/corpus.jsonl
```

Project-specific corpus:

```text
data/projects/<project_name>/corpus.jsonl
```

Each line is one serialized `DocumentRecord`.

## Step 5: query preparation and retrieval

There are two retrieval paths.

Before retrieval, the selected project profile may expand the question with
project-specific terms. The expanded text is used only for retrieval; the
original question remains the question shown to the answer generator.

### Simple retrieval

The simple retriever reads the selected `corpus.jsonl` directly.

It is useful for:

- debugging corpus quality;
- testing queries quickly;
- using newly built project corpora;
- avoiding MMORE indexing during development.

### MMORE retrieval

For MMORE, the corpus is first converted to:

```text
data/projects/<project_name>/mmore_corpus.jsonl
```

or, in the default workflow:

```text
data/processed/mmore_corpus.jsonl
```

Then MMORE indexes it and retrieves from the generated index. If native
retrieval fails, GitHelp can instead run lexical retrieval over the exported
`mmore_corpus.jsonl` and reports the mode as `corpus_fallback`.

The native MMORE backend does not automatically read a newly built
`corpus.jsonl`. The export and index must be rebuilt when the target corpus
changes.

For code-, symbol-, and filename-oriented questions, the answering pipeline can
also add candidates from the simple retriever before final filtering and
reranking.

## Step 6: project profile

After retrieval, GitHelp applies the result-processing parts of the selected
project profile.

A project profile can:

- filter low-value or irrelevant results;
- rerank results for known intents;
- answer some structured questions directly without calling the LLM.

The MMORE profile, for example, can answer some Milvus parameter questions deterministically to avoid unrelated configuration fields.

The project profile comes from the application config. The generated project
config does not select it automatically, so use `project_profile: generic` when
querying another project unless a custom profile is required.

## Step 7: prompt and answer

If no direct answer is returned by the project profile, retrieved sources are formatted into a prompt.

The LLM is instructed to:

- answer only from the provided sources;
- cite every factual statement;
- avoid inventing commands, paths, APIs, or configuration keys;
- say clearly when the available sources are insufficient.

The final output is an answer with cited sources.
