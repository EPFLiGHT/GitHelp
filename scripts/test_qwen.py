from __future__ import annotations

from docask.rag.qwen_provider import QwenLLMProvider


def main() -> None:
    llm = QwenLLMProvider(
        model_name="Qwen/Qwen3-8B",
        max_new_tokens=200,
        temperature=0.0,
        enable_thinking=False,
    )

    answer = llm.generate(
        "Explain in two sentences what a documentation assistant does."
    )

    print(answer)


if __name__ == "__main__":
    main()