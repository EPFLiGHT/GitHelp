# Indexing

GitHelp has its own corpus format, but MMORE expects a different JSONL format.

The indexing layer bridges the two.

## Relevant files

```text
src/githelp/indexing/mmore_format.py
src/githelp/indexing/mmore_indexer.py
scripts/export_mmore_corpus.py
scripts/build_index.py
```

## Step 1: export to MMORE format

Default command:

```bash
python scripts/export_mmore_corpus.py
```

Default input:

```text
data/processed/corpus.jsonl
```

Default output:

```text
data/processed/mmore_corpus.jsonl
```

Project-specific command:

```bash
python scripts/export_mmore_corpus.py \
  --corpus-path data/projects/mmore/corpus.jsonl \
  --output-path data/projects/mmore/mmore_corpus.jsonl
```

MMORE-compatible records look like:

```json
{
  "text": "...",
  "modalities": [],
  "metadata": {}
}
```

GitHelp adds a short source header inside the text field before indexing. This makes it possible to reconstruct source information after MMORE retrieval.

## Step 2: build the MMORE index

Default command:

```bash
python scripts/build_index.py
```

Project-specific command:

```bash
python scripts/build_index.py \
  --documents-path data/projects/mmore/mmore_corpus.jsonl \
  --collection-name mmore_docs
```

This uses:

```text
configs/mmore_index_config.yaml
```

and stores the index under:

```text
data/indexes/mmore/
```

If answering with backend `mmore` fails with `KeyError: 'model_name'`, restart
Streamlit after rebuilding the index. GitHelp can recover from missing Milvus
model metadata by reading model names from `configs/mmore_index_config.yaml`,
but an already-running Streamlit process may still be using older adapter code.

In local environments where native MMORE/Milvus retrieval crashes, GitHelp runs
native retrieval in an isolated child process. If that process fails, the
`mmore` backend falls back to the exported `mmore_corpus.jsonl` so Streamlit can
still answer from the MMORE-formatted corpus.

## Why keep indexing separate?

The corpus can be built and inspected before MMORE is involved.

This makes debugging easier:

1. build `corpus.jsonl`;
2. preview the records;
3. test simple retrieval;
4. only then export and index with MMORE.

## Important distinction

Building a corpus does not automatically rebuild the MMORE index.

For a newly selected project in Streamlit:

```text
Build corpus → backend simple
```

For MMORE retrieval:

```text
Build corpus → export MMORE corpus → build MMORE index → backend mmore
```
