# Retrieval Evaluation

GitHelp includes a small retrieval evaluation workflow for checking whether
retrieval changes improve source selection before looking at generated answers.

## Question Set

Benchmark questions are stored in:

```text
tests/evaluation/githelp_eval_questions.txt
```

Expected-source examples are stored in:

```text
tests/evaluation/githelp_eval_expected_sources.example.json
```

The expected-source file lets GitHelp report pass/fail checks for whether a
known relevant source appears in the retrieved top-k results.

## Run Evaluation

Simple backend:

```bash
python scripts/evaluate_retrieval.py \
  --questions-path tests/evaluation/githelp_eval_questions.txt \
  --expected-sources-path tests/evaluation/githelp_eval_expected_sources.example.json \
  --corpus-path data/projects/mmore/corpus.jsonl \
  --backend simple \
  --top-k 5
```

MMORE backend:

```bash
python scripts/evaluate_retrieval.py \
  --questions-path tests/evaluation/githelp_eval_questions.txt \
  --expected-sources-path tests/evaluation/githelp_eval_expected_sources.example.json \
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
- whether the selected raw backend returns the expected evidence.

The evaluation script calls the selected retrieval backend directly. It does
not run the full answering pipeline, so it does not apply project-profile query
expansion, filtering, reranking, filename boosts, or direct answers. The compact
output also does not currently expose whether `mmore` used `native_index` or
`corpus_fallback`; inspect Streamlit diagnostics or the retrieved record metadata
when that distinction matters.

This evaluation is intentionally lightweight, but it makes retrieval tuning more
repeatable than manually asking a few questions in Streamlit.

The repository currently contains ten MMORE questions and expected-source
annotations for a small subset. This is a preliminary regression check, not a
complete benchmark of recall, ranking quality, or answer faithfulness.
