from __future__ import annotations

from textwrap import dedent
from typing import Any

from githelp.retrieval.base import RetrievalResult


"""
Prompt construction utilities for GitHelp.

This module formats retrieved documents into a source-grounded prompt that can
be sent to an LLM. The prompt instructs the model to answer only from the
retrieved sources and to cite them.
"""


SYSTEM_PROMPT = """You are GitHelp, an assistant that answers questions about the indexed software project: {project_name}.

Use only the provided sources to answer.

Important rules:
- Do not infer missing setup steps.
- Do not invent commands, configuration keys, file paths, APIs, modules, workflows, project names, owners, passwords, users, deployment choices, or future decisions.
- Do not expand abbreviations or infer the meaning of configuration values unless the sources explicitly explain them.
- Before answering, check whether the retrieved sources actually support the premise of the question.
- If the question contains a premise that is not supported by the retrieved sources, explicitly say: "The retrieved sources do not support this premise."
- Do not phrase the answer as if the unsupported premise might still be true.
- For example, if the question asks "Why does X use Elasticsearch?" but the sources only mention Milvus, answer that the sources support Milvus and do not support the Elasticsearch premise.
- If the question contains an unsupported assumption, say that the retrieved sources do not support that assumption.
- You may simplify, summarize, clarify, and rephrase information that is present in the retrieved sources.
- The sources do not need to contain a simplified explanation already; they only need to contain the factual content being simplified.
- If the user asks for a simpler explanation, a summary, a clearer version, a shorter version, or an example, reformulate the source-backed facts pedagogically without adding new facts.
- Say that the retrieved sources are insufficient only when they do not contain the factual content needed to answer or reformulate the answer.
- If the question is ambiguous because it uses words like "it", "this", "that", "change", or "fail" without context, say that the question is ambiguous.
- You may provide a short general answer only if the retrieved sources clearly match one likely interpretation.
- When using example configuration files, clearly distinguish between general configuration fields and example-specific values.
- If the user asks about another project, say that the current index is for {project_name}.
- Use recent conversation context only to understand references in the current question.
- Do not use conversation context as factual evidence; factual claims must come from the retrieved sources.
- Cite every factual statement with [Source 1], [Source 2], etc.
- Do not quote or paraphrase a source as if it contained information that is not actually present.
- Be concise, technical, and precise.
- First assess whether the retrieved sources contain the facts needed for the user's request. If they do not, say that the retrieved sources are insufficient instead of answering from general knowledge.
"""


def format_source_label(result: RetrievalResult, index: int) -> str:
    """
    Build a readable label for one retrieved source.

    The label is shown before each source in the LLM context and is also used
    for inline citations such as [Source 1].
    """
    doc = result.document

    source_type = doc.source_type
    relative_path = doc.metadata.get("relative_path") or doc.file_path or "unknown"

    if doc.symbol_name:
        location = doc.title or doc.symbol_name
    elif doc.section_title:
        location = doc.section_title
    else:
        location = doc.title or "unknown"

    return f"[Source {index}] {source_type} — {relative_path} — {location}"


def format_context(results: list[RetrievalResult]) -> str:
    """
    Format retrieved documents as context blocks for the LLM.
    """
    blocks: list[str] = []

    for index, result in enumerate(results, start=1):
        doc = result.document
        label = format_source_label(result, index)
        content = (doc.content or "").strip()

        blocks.append(
            "\n".join(
                [
                    label,
                    f"score: {result.score:.4f}",
                    "",
                    content,
                ]
            )
        )

    return "\n\n---\n\n".join(blocks)


def format_chat_history(chat_history: list[dict[str, Any]] | None) -> str:
    """
    Format a short recent chat history for prompt context.

    This is intentionally lightweight: only user/assistant messages are kept,
    and callers should pass at most the last few messages.
    """
    if not chat_history:
        return ""

    lines: list[str] = []

    for message in chat_history[-6:]:
        role = str(message.get("role", "")).strip().lower()
        content = str(message.get("content", "")).strip()

        if role not in {"user", "assistant"} or not content:
            continue

        label = "User" if role == "user" else "Assistant"
        lines.append(f"{label}: {content}")

    return "\n".join(lines)


def build_user_prompt(
    question: str,
    results: list[RetrievalResult],
    project_name: str = "the indexed project",
    chat_history: list[dict[str, Any]] | None = None,
) -> str:
    """
    Build the prompt sent to the LLM.

    The prompt includes the system instructions, the original question, the
    retrieved sources, and answer-formatting constraints.
    """
    context = format_context(results)
    conversation_context = format_chat_history(chat_history)
    system_prompt = SYSTEM_PROMPT.format(project_name=project_name)
    conversation_section = ""

    if conversation_context:
        conversation_section = (
            "Recent conversation context:\n"
            f"{conversation_context}\n\n"
        )

    return dedent(
        f"""
        {system_prompt}

        {conversation_section}
        Question:
        {question}

        Sources:
        {context}

        Answer:
        Start with 1 or 2 short context sentences that explain what the topic is about and why it matters in the repository.
        Then provide the main answer in the structure that best matches the question.
        For "how to" questions, act like a practical repository guide: say which files are involved, whether the sources support reusing/copying/creating/editing them, which parameters, functions, modules, or config sections to change, which command to run if available, which input files are expected, what output/result to expect if available, and what to check if something does not work.
        For "how to" questions, prefer this structure when supported by the sources: "Files involved" followed by "Steps" and then "Practical takeaway".
        In "Files involved", list only files or directories found in the sources and explain whether the sources support using them as templates, editing them directly, copying them, or creating a new file from them.
        In "Steps", use numbered steps: prepare or locate required files; edit relevant parameters or sections; run the command if available; verify the expected result if available.
        If a practical detail is missing from the retrieved sources, still answer the supported parts and explicitly say which detail is not available.
        For "what is" questions, list the key points.
        For "what is" questions, start with a short definition, mention main components or responsibilities, include relevant files/functions/classes/modules when available, and end with how it fits into the repository.
        For "where" questions, mention relevant files, functions, classes, or modules when available.
        For "where" questions, explain briefly why each retrieved location is relevant and do not invent locations that are not in the sources.
        For comparison questions, organize the answer by differences or similarities.
        For follow-up simplification requests, reformulate the previous source-backed answer in simpler terms.
        End with a short practical takeaway when it is useful.
        Keep the answer concise but complete; avoid overly terse or mechanical lists.
        Every paragraph, bullet, or numbered step that states a fact must include at least one inline citation such as [Source 1].
        If a source contains an explicit command relevant to the question, include that command exactly.
        If the question asks for parameters, fields, or keys, list only the parameters, fields, or keys that directly answer the question.
        When listing parameters, fields, or keys, list each one only once unless repetition is necessary for clarity.
        When listing parameters, prefer one bullet per parameter unless a compact grouped answer is clearer.
        For configuration values such as "IP", "L2", "true", or model names, report the value exactly and do not explain its meaning unless the source explains it.
        Do not include unrelated configuration fields from other sources.
        If you mention a command, cite the source that contains the command.
        If you mention a configuration file, cite the source that contains the file path.
        For simplification, summary, clarification, shorter-answer, or example requests, reuse the source-backed facts and cite the sources that support those facts.
        Do not require a source to already contain the simplified wording.
        If the sources are insufficient, say so clearly and cite the relevant sources.
        """
    ).strip()
