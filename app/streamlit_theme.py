from __future__ import annotations

from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOGO_RELATIVE_PATH = Path("docs") / "_static" / "images" / "logo.png"


GITHELP_CSS = """
<style>
:root {
    --githelp-green: #7bc89c;
    --githelp-green-strong: #57a979;
    --githelp-green-soft: rgba(123, 200, 156, 0.12);
    --githelp-ink: #14251b;
    --githelp-border: rgba(87, 169, 121, 0.48);
}

/* Keep the identity quiet: color is used for actions, focus, and structure. */
[data-testid="stAppViewContainer"] a {
    color: var(--githelp-green-strong);
}

div.stButton > button {
    background: var(--githelp-green) !important;
    border: 1px solid var(--githelp-green-strong) !important;
    color: var(--githelp-ink) !important;
    box-shadow: none !important;
}

div.stButton > button:hover {
    background: #8fd3aa !important;
    border-color: var(--githelp-green-strong) !important;
    color: #0e1d14 !important;
}

div.stButton > button:focus-visible,
[data-testid="stChatInput"]:focus-within {
    border-color: var(--githelp-green-strong) !important;
    box-shadow: 0 0 0 0.16rem rgba(123, 200, 156, 0.28) !important;
    outline: none !important;
}

div.stButton > button:disabled {
    background: rgba(123, 200, 156, 0.35) !important;
    border-color: rgba(87, 169, 121, 0.3) !important;
    color: rgba(20, 37, 27, 0.58) !important;
}

[data-testid="stChatInput"] {
    border-color: var(--githelp-border);
}

[data-testid="stChatInputSubmitButton"] {
    color: var(--githelp-green-strong) !important;
}

[data-testid="stChatMessage"] {
    background: var(--githelp-green-soft);
    border-left: 3px solid var(--githelp-border);
    border-radius: 0.55rem;
    padding-left: 0.65rem;
}

[data-testid="stChatMessageAvatarUser"] {
    background: var(--githelp-green) !important;
    color: var(--githelp-ink) !important;
}

[data-testid="stChatMessageAvatarAssistant"] {
    background: #25332a !important;
    color: #f5f8f6 !important;
}

[data-testid="stChatMessageAvatarUser"] svg,
[data-testid="stChatMessageAvatarAssistant"] svg {
    fill: currentColor !important;
}

[data-testid="stSidebar"] {
    border-right: 1px solid rgba(87, 169, 121, 0.2);
}

[data-testid="stExpander"] {
    border-color: rgba(87, 169, 121, 0.3);
}

@media (prefers-color-scheme: dark) {
    :root {
        --githelp-green-soft: rgba(123, 200, 156, 0.09);
        --githelp-border: rgba(143, 211, 170, 0.5);
    }

    [data-testid="stAppViewContainer"] a {
        color: #9bdbb4;
    }
}
</style>
"""


def resolve_logo_path(project_root: str | Path | None = None) -> Path:
    """Resolve the logo independently of the process working directory."""
    roots = [Path(project_root).resolve()] if project_root else [PROJECT_ROOT]
    cwd = Path.cwd().resolve()

    if cwd not in roots:
        roots.append(cwd)

    for root in roots:
        candidate = root / LOGO_RELATIVE_PATH
        if candidate.is_file():
            return candidate

    checked = ", ".join(str(root / LOGO_RELATIVE_PATH) for root in roots)
    raise FileNotFoundError(f"GitHelp logo not found. Checked: {checked}")


def apply_githelp_theme() -> None:
    """Inject the small set of GitHelp-specific component styles."""
    st.markdown(GITHELP_CSS, unsafe_allow_html=True)


def render_githelp_header() -> None:
    """Render the compact logo, title, and application description."""
    logo_column, title_column = st.columns(
        [1, 7],
        gap="small",
        vertical_alignment="center",
    )

    with logo_column:
        # Let the browser scale the original PNG to the header column. Passing
        # a small integer width makes Streamlit downsample it server-side,
        # which looks soft on high-density displays.
        st.image(str(resolve_logo_path()), width="stretch")

    with title_column:
        st.title("GitHelp")
        st.caption(
            "Ask questions about a software project's documentation and code."
        )
