# RAG and LLM layer

The RAG layer starts after retrieval.

Its job is to turn retrieved sources into a grounded answer.

## Relevant files

```text
src/docask/rag/prompting.py
src/docask/rag/extractive_answerer.py
src/docask/rag/answering.py
```

## Prompting

File:

```text
src/docask/rag/prompting.py
```

This module formats retrieved sources into a prompt.

The prompt instructs the future LLM to:

- answer only from the provided sources;
- cite sources inline with `[Source 1]`, `[Source 2]`, etc.;
- say when the sources are insufficient.

Debug command:

```bash
PYTHONPATH=src python scripts/debug_prompting.py "How do I configure indexing?"
```

## Temporary extractive answerer

File:

```text
src/docask/rag/extractive_answerer.py
```

This is not a real LLM answerer.

It currently:

- takes the top retrieved source;
- returns its content;
- has a small special case for signature questions.

Command:

```bash
PYTHONPATH=src python scripts/answer_question.py "How do I configure indexing?" --backend simple
```

## High-level answering helpers

File:

```text
src/docask/rag/answering.py
```

This module exposes:

```python
prepare_answer_prompt(...)
answer_question(...)
```

Current flow:

```text
question -> retrieval -> prompt or extractive answer
```

## Next step: LLM generation

The next planned step is to replace the temporary extractive answerer with a source-grounded LLM call.

Possible local model path:

```text
Ollama + qwen3:8b
```

The expected final flow is:

```text
question -> retrieval -> prompt -> LLM answer -> cited sources
```
