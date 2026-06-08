project = "GitHelp"
author = "GitHelp contributors"

extensions = [
    "myst_parser",
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

html_theme = "furo"
html_title = "GitHelp Documentation"

myst_enable_extensions = [
    "colon_fence",
    "deflist",
]
