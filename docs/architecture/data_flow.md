# Data flow

This page explains how information moves through DocAsk.

## Step 1: source files

DocAsk starts from a target project repository.

For the MMORE use case, the relevant sources are:

```text
../../mmore/docs/source       -> Markdown and RST documentation
../../mmore/src/mmore         -> Python source code
../../mmore/examples          -> YAML example configs
../../mmore/production-config -> YAML production configs
../../mmore                   -> repository structure
```

## Step 2: normalized records

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

## Step 3: corpus file

All records are saved to:

```text
data/processed/corpus.jsonl
```

Each line is one serialized `DocumentRecord`.

## Step 4: retrieval

There are two retrieval paths.

### Simple retrieval

The simple retriever reads `corpus.jsonl` directly.

It is useful for:

- debugging corpus quality;
- testing queries quickly;
- avoiding MMORE indexing during development.

### MMORE retrieval

For MMORE, the corpus is first converted to:

```text
data/processed/mmore_corpus.jsonl
```

Then MMORE indexes it and retrieves from the generated index.

## Step 5: prompt and answer

Retrieved sources are formatted into a prompt.

The current answerer is extractive and temporary. It returns content from the top source. Later, this will be replaced by source-grounded LLM generation.
