# Debugging

This page lists useful checks during development.

## Compile all Python files

```bash
python -m compileall src scripts
```

This catches syntax errors and some import issues.

## Check for old imports after refactoring

```bash
grep -R "docask.retrieval.answering\|docask.retrieval.prompting\|docask.retrieval.extractive_answerer\|docask.retrieval.mmore_format\|docask.retrieval.mmore_indexer" -n src scripts
```

This should return nothing after moving files into `rag/` and `indexing/`.

## Remove generated cache files

```bash
find . -type d -name "__pycache__" -prune -exec rm -rf {} +
rm -rf src/docask.egg-info
```

## Avoid grepping inside the virtual environment

If the virtual environment is inside the repo, grep can return unrelated files from dependencies.

Prefer:

```bash
grep -R "test_prompting\|test_retrieval" -n README.md scripts src docs
```

instead of:

```bash
grep -R "test_prompting\|test_retrieval" -n .
```

## Debug source extraction

Build the full corpus:

```bash
PYTHONPATH=src python scripts/build_corpus.py
```

Preview specific source types:

```bash
PYTHONPATH=src python scripts/preview_corpus.py --source-type python_function --limit 3
PYTHONPATH=src python scripts/preview_corpus.py --source-type example_config --limit 3
PYTHONPATH=src python scripts/preview_corpus.py --source-type repo_structure --limit 1
```

## Debug retrieval quality

```bash
PYTHONPATH=src python scripts/debug_retrieval.py "How do I configure indexing?"
```

If results are poor, check:

- whether the expected source exists in the corpus;
- whether the source type is correct;
- whether titles and metadata are informative;
- whether the query is too vague;
- whether reranking rules are needed for that intent.
