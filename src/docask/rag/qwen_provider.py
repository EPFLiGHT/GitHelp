from __future__ import annotations

from transformers import AutoModelForCausalLM, AutoTokenizer

from docask.rag.llm_provider import LLMProvider


class QwenLLMProvider(LLMProvider):
    """LLM provider using Qwen through Hugging Face Transformers."""

    def __init__(
        self,
        model_name: str = "Qwen/Qwen3-0.6B",
        max_new_tokens: int = 128,
        temperature: float = 0.0,
        enable_thinking: bool = False,
    ) -> None:
        self.model_name = model_name
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.enable_thinking = enable_thinking

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            dtype="auto",
            device_map="auto",
        )

    def generate(self, prompt: str) -> str:
        messages = [
            {
                "role": "user",
                "content": prompt,
            }
        ]

        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=self.enable_thinking,
        )

        inputs = self.tokenizer(
            text,
            return_tensors="pt",
        ).to(self.model.device)

        generation_kwargs = {
            "max_new_tokens": self.max_new_tokens,
            "do_sample": self.temperature > 0,
        }

        if self.temperature > 0:
            generation_kwargs["temperature"] = self.temperature

        outputs = self.model.generate(
            **inputs,
            **generation_kwargs,
        )

        generated_ids = outputs[0][inputs["input_ids"].shape[-1]:]

        answer = self.tokenizer.decode(
            generated_ids,
            skip_special_tokens=True,
        )

        return answer.strip()