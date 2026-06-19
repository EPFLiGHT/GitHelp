# Retrieval Evaluation

GitHelp includes a small retrieval evaluation workflow for checking whether
retrieval changes improve source selection before looking at generated answers.

## Question Set

Benchmark questions are stored in:

```text
githelp_eval_questions.txt
```

Expected-source examples are stored in:

```text
githelp_eval_expected_sources.example.json
```

The expected-source file lets GitHelp report pass/fail checks for whether a
known relevant source appears in the retrieved top-k results.

## Run Evaluation

Simple backend:

```bash
python scripts/evaluate_retrieval.py \
  --questions-path githelp_eval_questions.txt \
  --expected-sources-path githelp_eval_expected_sources.example.json \
  --corpus-path data/projects/mmore/corpus.jsonl \
  --backend simple \
  --top-k 5
```

MMORE backend:

```bash
python scripts/evaluate_retrieval.py \
  --questions-path githelp_eval_questions.txt \
  --expected-sources-path githelp_eval_expected_sources.example.json \
  --corpus-path data/projects/mmore/corpus.jsonl \
  --backend mmore \
  --top-k 5
```

## What To Inspect

For each question, inspect:

- whether the expected source appears in top-k;
- whether the top result is specific enough for answer generation;
- whether source types are balanced between docs, code, config, and repository
  structure;
- whether project-profile filtering removed useful evidence;
- whether `mmore` results came from `native_index` or `corpus_fallback`.

This evaluation is intentionally lightweight, but it makes retrieval tuning more
repeatable than manually asking a few questions in Streamlit.
