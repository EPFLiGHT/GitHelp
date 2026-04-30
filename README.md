# DocAsk

DocAsk is a conversational interface for querying project documentation in natural language.

The initial use case is the MMORE documentation. The longer-term goal is to support other software projects by combining written documentation with documentation extracted from code, such as docstrings, function signatures, class descriptions, and selected code snippets.

## Project goal

DocAsk aims to provide a documentation assistant that can:

- ingest project documentation;
- extract structured documentation from Python code;
- build a unified corpus;
- retrieve relevant sources for a user question;
- generate an answer grounded in the retrieved sources;
- display the answer together with traceable citations.

The final target architecture is:

```text
project docs + code
        ↓
structured corpus
        ↓
MMORE indexing / retrieval
        ↓
LLM answer generation
        ↓
Streamlit conversational UI
```

## Current status

The current version is an early prototype.

Implemented so far:

- Markdown documentation loading;
- Python code documentation extraction with `ast`;
- unified `DocumentRecord` format;
- JSONL corpus building;
- corpus preview utilities;
- temporary local retriever;
- prompt formatting for future LLM use;
- simple extractive answerer for terminal testing.

Not implemented yet:

- MMORE indexing / retrieval integration;
- LLM generation;
- Streamlit chat interface;
- multi-project configuration;
- advanced chunking;
- dependency graph or code navigation features.

The current local retriever is temporary. It is used to validate the corpus format, metadata, source display, and question-to-source flow before replacing the retrieval layer with MMORE.

## Repository structure

```text
docask/
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
├── configs/
│   ├── project_config.yaml
│   ├── indexing_config.yaml
│   └── app_config.yaml
├── data/
│   ├── raw/
│   ├── processed/
│   └── extracted_code_docs/
├── scripts/
│   ├── build_corpus.py
│   ├── extract_code_docs.py
│   ├── preview_corpus.py
│   ├── test_retrieval.py
│   ├── test_prompting.py
│   ├── prepare_answer.py
│   └── answer_question.py
├── src/
│   └── docask/
│       ├── __init__.py
│       ├── config.py
│       ├── data_models.py
│       ├── loaders/
│       │   └── markdown_loader.py
│       ├── extractors/
│       │   └── python_doc_extractor.py
│       ├── corpus/
│       │   └── builder.py
│       ├── retrieval/
│       │   ├── simple_retriever.py
│       │   ├── prompting.py
│       │   ├── answering.py
│       │   └── extractive_answerer.py
│       └── utils/
│           └── paths.py
└── tests/
```

## Main modules

### `src/docask/data_models.py`

Defines the internal document format used by DocAsk.

The main model is `DocumentRecord`, which represents one indexable unit. It contains:

- `doc_id`;
- `content`;
- `source_type`;
- `title`;
- `file_path`;
- `section_title`;
- `module_name`;
- `symbol_name`;
- `signature`;
- `language`;
- `tags`;
- `metadata`.

This format is shared by Markdown documentation and Python code documentation.

### `src/docask/loaders/markdown_loader.py`

Loads Markdown documentation files and splits them into structured sections.

For each section, it creates a `DocumentRecord` with metadata such as:

- relative file path;
- page title;
- section title;
- heading level;
- documentation domain.

Example source type:

```text
markdown_section
```

### `src/docask/extractors/python_doc_extractor.py`

Extracts documentation from Python source files using the built-in `ast` module.

It extracts:

- module docstrings;
- class docstrings;
- function signatures and docstrings;
- method signatures and docstrings.

It creates `DocumentRecord` objects with source types such as:

```text
python_module
python_class
python_function
python_method
```

For functions and methods, the indexed content includes the symbol name, type, signature, and docstring. This makes code-related questions easier to retrieve.

Example indexed content:

```text
Symbol: mmore.run_dashboard_backend.get_latest_reports
Type: function
Signature: get_latest_reports(page_size: int = Query(100, ge=1), page_idx: int = Query(0, ge=0)) -> BatchedReports

Docstring:
Get the latest reports in a paginated way.
```

### `src/docask/corpus/builder.py`

Builds the final corpus by merging several sources:

- Markdown documentation;
- Python code documentation.

It can save the corpus as JSONL in:

```text
data/processed/corpus.jsonl
```

Each line contains one serialized `DocumentRecord`.

### `src/docask/retrieval/simple_retriever.py`

Temporary local retriever used for prototyping.

It loads the JSONL corpus and retrieves relevant documents for a question using token overlap and simple scoring rules.

The retriever includes basic heuristics to:

- favor Markdown documentation for user-facing questions such as “how do I install…”;
- favor code documentation for symbol-related questions such as “what is the signature of…”;
- boost exact matches on function, class, or method names.

This retriever is not the final retrieval system. It will later be replaced by MMORE indexing and retrieval.

### `src/docask/retrieval/prompting.py`

Formats retrieved sources into a prompt that can be sent to an LLM.

It builds a source-grounded prompt with explicit source labels:

```text
[Source 1] markdown_section — getting_started/indexing.md — 2. Run the indexing command
```

The prompt instructs the model to answer only from the provided sources and cite them inline.

### `src/docask/retrieval/extractive_answerer.py`

Temporary answer generator.

It does not call an LLM. It simply builds a minimal answer from the top retrieved source.

This is useful to validate the full flow before adding LLM generation.

### `src/docask/retrieval/answering.py`

High-level retrieval and answering functions.

It currently exposes:

- `prepare_answer_prompt(...)`;
- `answer_question(...)`.

This module centralizes the flow:

```text
question → retrieve sources → build prompt or answer
```

Later, this is where the LLM-based answer generation can be integrated.

### `src/docask/config.py`

Loads YAML configuration files from the `configs/` directory.

### `src/docask/utils/paths.py`

Defines project paths such as:

- project root;
- config directory;
- data directory;
- processed data directory;
- extracted code documentation directory.

## Configuration files

### `configs/project_config.yaml`

Defines the project to index.

Example:

```yaml
project_name: mmore
docs_path: ../../mmore/docs/source
code_path: ../../mmore/src/mmore
include_extensions:
  - .md
  - .rst
  - .py
exclude_patterns:
  - "__pycache__"
  - ".ipynb_checkpoints"
  - ".DS_Store"
```

### `configs/indexing_config.yaml`

Contains indexing-related settings.

Current example:

```yaml
include_markdown: true
include_code_docstrings: false
include_signatures: false
include_code_snippets: false

chunk_size: 1200
chunk_overlap: 150
top_k: 5
```

Some options are planned for later stages and are not fully used yet.

### `configs/app_config.yaml`

Contains application-related settings.

Current example:

```yaml
app_title: DocAsk
app_subtitle: Ask questions about a project's documentation
show_sources: true
default_top_k: 5
```

## Dependencies

This project currently targets:

```text
mmore==1.2.1
```

Before using DocAsk, make sure the required system dependencies for MMORE are installed.

For local development, MMORE can either be installed from PyPI or installed as an editable package from a local clone.

Example with a local MMORE clone:

```bash
pip install -e ../mmore
```

## Usage

Run all commands from the root of the repository.

### Build the corpus

```bash
PYTHONPATH=src python scripts/build_corpus.py
```

This reads the paths defined in `configs/project_config.yaml`, loads Markdown documentation, extracts Python code documentation, and writes:

```text
data/processed/corpus.jsonl
```

### Preview the corpus

Preview the first corpus entries:

```bash
PYTHONPATH=src python scripts/preview_corpus.py
```

Preview specific source types:

```bash
PYTHONPATH=src python scripts/preview_corpus.py --source-type markdown_section --limit 3
```

```bash
PYTHONPATH=src python scripts/preview_corpus.py --source-type python_function --limit 3
```

```bash
PYTHONPATH=src python scripts/preview_corpus.py --source-type python_method --limit 3
```

### Test retrieval

```bash
PYTHONPATH=src python scripts/test_retrieval.py "How do I run the indexing pipeline?"
```

```bash
PYTHONPATH=src python scripts/test_retrieval.py "What is the signature of get_latest_reports?"
```

### Test prompt construction

```bash
PYTHONPATH=src python scripts/test_prompting.py "How do I run the indexing pipeline?"
```

This prints the prompt that would be sent to a future LLM.

### Prepare answer prompt

```bash
PYTHONPATH=src python scripts/prepare_answer.py "How do I run the indexing pipeline?"
```

This retrieves sources and prints the full source-grounded prompt.

### Generate a temporary extractive answer

```bash
PYTHONPATH=src python scripts/answer_question.py "How do I run the indexing pipeline?"
```

Example output:

```text
Answer:
Based on the most relevant source, here is the answer:

Once the configuration file is ready, launch the indexing pipeline with:
python3 -m mmore index --config_file /path/to/config.yaml

Source: [Source 1]
```

## Current example queries

User-facing documentation question:

```bash
PYTHONPATH=src python scripts/answer_question.py "How do I run the indexing pipeline?"
```

Code documentation question:

```bash
PYTHONPATH=src python scripts/answer_question.py "What is the signature of get_latest_reports?"
```

## Development notes

The current retrieval system is intentionally simple. It exists to validate the corpus and source formatting before integrating MMORE.

Important design choices:

- Markdown sections and Python code documentation are stored in the same internal format.
- Code documents include signatures directly in the indexed content.
- Metadata is kept rich enough to support source display and later filtering.
- User-facing questions should generally prefer written documentation.
- Symbol-level questions should generally prefer extracted code documentation.

## Next steps

Planned next steps:

1. Integrate an LLM in terminal mode.
2. Replace the temporary retriever with MMORE indexing and retrieval.
3. Build a minimal Streamlit chat interface.
4. Display retrieved sources under each answer.
5. Add configuration options for source types and top-k retrieval.
6. Improve chunking and source balancing.
7. Extend support to other projects.

## Roadmap

### Level 1 — MVP

- Markdown documentation ingestion.
- Corpus building.
- Retrieval.
- Answer generation.
- Source display.
- Minimal conversational UI.

### Level 2 — Strong prototype

- Markdown documentation plus Python docstrings and signatures.
- Better metadata handling.
- LLM answer generation with citations.
- Streamlit interface.
- MMORE retrieval integration.

### Level 3 — Advanced version

- Selected code snippets.
- Multi-project support.
- Dependency graph or symbol graph.
- More advanced source ranking.
- Navigation between documentation and code.
