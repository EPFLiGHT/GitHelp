# RAG and LLM layer

The RAG layer starts after retrieval.

Its job is to turn retrieved sources into a grounded answer.

## Relevant files

```text
src/githelp/rag/prompting.py
src/githelp/rag/extractive_answerer.py
src/githelp/rag/answering.py
src/githelp/rag/llm_provider.py
src/githelp/rag/llm_factory.py
src/githelp/rag/qwen_provider.py
```

## Prompting

File:

```text
src/githelp/rag/prompting.py
```

This module formats retrieved sources into a prompt.

The prompt instructs the LLM to:

- answer only from the provided sources;
- cite sources inline with `[Source 1]`, `[Source 2]`, etc.;
- avoid inventing commands, paths, APIs, modules, or configuration keys;
- avoid interpreting configuration values unless the sources explain them;
- say when the sources are insufficient.

Debug command:

```bash
PYTHONPATH=src python scripts/debug_prompting.py \
  "How do I configure indexing?" \
  --backend simple \
  --corpus-path data/projects/mmore/corpus.jsonl \
  --config-path configs/app_config.yaml
```

## LLM providers

GitHelp uses a provider interface:

```text
src/githelp/rag/llm_provider.py
```

The active provider is selected from:

```text
configs/app_config.yaml
```

Example:

```yaml
llm:
  provider: qwen
  model_name: Qwen/Qwen3-1.7B
  max_new_tokens: 512
  temperature: 0.0
  enable_thinking: false
```

The Qwen provider uses Hugging Face Transformers.

## High-level answering helpers

File:

```text
src/githelp/rag/answering.py
```

This module exposes:

```python
prepare_answer_prompt(...)
answer_question(...)
answer_question_with_llm(...)
answer_question_with_provider(...)
```

Current flow:

```text
question
→ project profile query expansion
→ retrieval
→ project profile filtering/reranking
→ optional project profile direct answer
→ prompt construction
→ LLM generation
```

## Direct answers from project profiles

Some structured questions are better answered deterministically than by an LLM.

For example, the MMORE profile can answer Milvus parameter questions directly. This avoids returning unrelated fields such as `model_name`, `top_k`, or `max_workers` when the user asks specifically for Milvus parameters.

## Temporary extractive answerer

File:

```text
src/githelp/rag/extractive_answerer.py
```

This remains available when LLM generation is disabled.

It:

- takes the top retrieved source;
- returns its content;
- has a small special case for signature questions.

Command:

```bash
PYTHONPATH=src python scripts/answer_question.py \
  "How do I configure indexing?" \
  --backend simple
```

## LLM answer generation

LLM generation can be enabled with:

```bash
PYTHONPATH=src python scripts/answer_question.py \
  "How do I configure indexing?" \
  --llm \
  --backend simple \
  --corpus-path data/projects/mmore/corpus.jsonl \
  --config-path configs/app_config.yaml
```

The expected answer includes inline source citations.
