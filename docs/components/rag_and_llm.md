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
- begin with a brief, direct context sentence;
- use practical numbered steps for how-to questions;
- group parameters by role instead of repeating one description pattern;
- clearly separate supported facts, safe inferences, and missing evidence;
- say when the sources are incomplete or insufficient.

Debug command:

```bash
python scripts/debug_prompting.py \
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
  model_name: Qwen/Qwen3-4B
  max_new_tokens: 512
  temperature: 0.0
  enable_thinking: false
```

The Qwen provider uses Hugging Face Transformers. A `dummy` provider is also
implemented for tests and pipeline debugging. No external or hosted LLM
provider is currently included.

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
current question + recent chat
→ keep standalone questions unchanged, or rewrite a clear follow-up
→ ask for clarification when a follow-up has no single clear referent
→ project profile query expansion
→ retrieval
→ project profile filtering/reranking
→ optional project profile direct answer
→ prompt construction with the original question and lightweight recent context
→ LLM generation
```

The rewritten query is used only for retrieval. Recent chat is not appended to
the retrieval query, and standalone questions are not forced into the previous
topic. The final answer prompt receives at most six recent messages to resolve
references, but instructs the model not to repeat earlier answers unless the
user explicitly asks for a summary or rephrasing.

## Direct answers from project profiles

Some structured questions are better answered deterministically than by an LLM.

For example, the MMORE profile can answer Milvus parameter questions directly.
It scans the retrieved records for a fixed allowlist of known Milvus keys. This
avoids returning unrelated fields such as `model_name`, `top_k`, or
`max_workers`, but it is not a general YAML schema parser.

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
python scripts/answer_question.py \
  "How do I configure indexing?" \
  --backend simple
```

## LLM answer generation

LLM generation can be enabled with:

```bash
python scripts/answer_question.py \
  "How do I configure indexing?" \
  --llm \
  --backend simple \
  --corpus-path data/projects/mmore/corpus.jsonl \
  --config-path configs/app_config.yaml
```

The expected answer includes inline source citations.
