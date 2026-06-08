# Debugging

This page lists useful checks during development.

## Run all tests

```bash
pytest -q
```

This is the main check before committing changes.

## Compile all Python files

```bash
python -m compileall src scripts app
```

This catches syntax errors and some import issues.

## Test default corpus build

```bash
python scripts/build_corpus.py
```

This should write:

```text
data/processed/corpus.jsonl
```

## Test dynamic corpus build

```bash
python scripts/build_corpus.py \
  --config configs/project_config.yaml \
  --output-path data/projects/mmore/corpus.jsonl
```

This should write:

```text
data/projects/mmore/corpus.jsonl
```

## Test answering on a project-specific corpus

```bash
python scripts/answer_question.py \
  "Which Milvus parameters are used in the ColPali config?" \
  --llm \
  --backend simple \
  --corpus-path data/projects/mmore/corpus.jsonl \
  --config-path configs/app_config.yaml
```

For MMORE, some structured questions may be answered directly by the project profile without loading the LLM.

## Debug Streamlit state

The app stores local state in:

```text
data/app_state.json
```

If the interface restores an old project or wrong corpus path, remove this file:

```bash
rm -f data/app_state.json
```

Then restart Streamlit.

## Clear generated project corpora

```bash
rm -rf data/projects/
```

Then rebuild the project corpus from the Streamlit interface or from the command line.

## Check for old imports after refactoring

```bash
grep -R "githelp.retrieval.answering\|githelp.retrieval.prompting\|githelp.retrieval.extractive_answerer\|githelp.retrieval.mmore_format\|githelp.retrieval.mmore_indexer" -n src scripts app docs
```

This should return nothing after moving files into `rag/` and `indexing/`.

## Remove generated cache files

```bash
find . -type d -name "__pycache__" -prune -exec rm -rf {} +
rm -rf src/githelp.egg-info
```

## Avoid grepping inside the virtual environment

If the virtual environment is inside the repo, grep can return unrelated files from dependencies.

Prefer:

```bash
grep -R "test_prompting\|test_retrieval" -n README.md scripts src docs tests
```

instead of:

```bash
grep -R "test_prompting\|test_retrieval" -n .
```

## Debug source extraction

Build the full corpus:

```bash
python scripts/build_corpus.py
```

Preview specific source types:

```bash
python scripts/preview_corpus.py --source-type python_function --limit 3
python scripts/preview_corpus.py --source-type example_config --limit 3
python scripts/preview_corpus.py --source-type repo_structure --limit 1
```

## Debug retrieval quality

```bash
python scripts/debug_retrieval.py "How do I configure indexing?"
```

If results are poor, check:

- whether the expected source exists in the corpus;
- whether the source type is correct;
- whether titles and metadata are informative;
- whether the selected backend reads the expected corpus or index;
- whether the query is too vague;
- whether a project profile should expand, filter, or rerank that intent.

## Evaluate retrieval on benchmark questions

```bash
python scripts/evaluate_retrieval.py \
  --questions-path githelp_eval_questions.txt \
  --corpus-path data/projects/mmore/corpus.jsonl \
  --backend simple \
  --top-k 5
```

This prints ranked source summaries for each question. It is useful for
comparing retrieval changes before checking generated answers.

To check expected sources as pass/fail criteria, provide a JSON file:

```bash
python scripts/evaluate_retrieval.py \
  --questions-path githelp_eval_questions.txt \
  --expected-sources-path githelp_eval_expected_sources.example.json \
  --corpus-path data/projects/mmore/corpus.jsonl \
  --backend simple \
  --top-k 5
```

## Backend mismatch

A common issue is using:

```text
backend mmore
```

after building a new corpus with Streamlit.

Building a corpus does not update the MMORE index. For a newly built project corpus, use:

```text
backend simple
```

unless the MMORE export and index have also been rebuilt.

## macOS OpenMP conflict while loading MMORE

On some macOS environments, MMORE model loading can fail before retrieval with:

```text
OMP: Error #15: Initializing libomp.dylib, but found libomp.dylib already initialized.
```

This is an environment conflict between native numerical libraries. For a local
debugging run, you can try:

```bash
KMP_DUPLICATE_LIB_OK=TRUE streamlit run app/streamlit_app.py
```

Use this only as a local workaround. The cleaner fix is to reinstall the
environment so PyTorch, transformers, and MMORE share a compatible OpenMP
runtime.
