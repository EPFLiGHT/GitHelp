from __future__ import annotations

import argparse

from githelp.rag.qwen_provider import QwenLLMProvider


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Test Qwen generation through the GitHelp provider."
    )

    parser.add_argument(
        "--model-name",
        default="Qwen/Qwen3-1.7B",
        help="Hugging Face model name.",
    )

    parser.add_argument(
        "--max-new-tokens",
        type=int,
        default=200,
        help="Maximum number of generated tokens.",
    )

    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Generation temperature.",
    )

    parser.add_argument(
        "--enable-thinking",
        action="store_true",
        help="Enable Qwen thinking mode.",
    )

    parser.add_argument(
        "--prompt",
        default="Explain in two sentences what a documentation assistant does.",
        help="Prompt sent to the model.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    llm = QwenLLMProvider(
        model_name=args.model_name,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        enable_thinking=args.enable_thinking,
    )

    answer = llm.generate(args.prompt)

    print(answer)


if __name__ == "__main__":
    main()
