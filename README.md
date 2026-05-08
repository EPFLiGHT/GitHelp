# DocAsk

DocAsk is a conversational assistant for querying a software project's documentation and code-related knowledge in natural language.

The initial use case is the [MMORE](https://github.com/swiss-ai/mmore) repository. DocAsk can use MMORE internally for indexing and retrieval, while exposing a simpler project-level interface to the user.

---

## Goal

DocAsk aims to help users ask questions about a project such as:

- How do I install or run the project?
- How do I configure indexing or retrieval?
- Where is a specific module implemented?
- What is the signature of a function?
- What does a class or method do?
- What does an example configuration file look like?

The long-term goal is to support other repositories by combining several source types:

- written documentation;
- Python docstrings and signatures;
- YAML configuration examples;
- repository structure summaries;
- later, selected code snippets and tests.

---

## Current architecture

```text
project repository
        ↓
DocAsk loaders and extractors
        ↓
unified corpus.jsonl
        ↓
retrieval backend
        ├── simple local retriever
        └── MMORE-compatible export → MMORE indexing → MMORE retrieval
        ↓
prompt construction
        ↓
answer generation
        ├── temporary extractive answerer
        └── future LLM answer generation
        ↓
Streamlit UI
```

At the moment, DocAsk supports:

- corpus building;
- local retrieval for debugging;
- MMORE-compatible export;
- MMORE indexing;
- MMORE retrieval;
- prompt preparation;
- temporary extractive answers.

LLM generation and the final Streamlit conversational interface are the next steps.

---

## Current status

Implemented:

- Markdown and reStructuredText documentation loading;
- Python documentation extraction using `ast`;
- extraction of module, class, function and method docstrings;
- extraction of Python signatures;
- YAML configuration loading;
- repository structure summary generation;
- unified `DocumentRecord` format;
- JSONL corpus generation;
- export to MMORE-compatible JSONL format;
- internal MMORE indexing through the PyPI package;
- internal MMORE retrieval backend;
- temporary local retriever for debugging;
- prompt construction with source citations;
- temporary extractive answerer for terminal testing.

Not implemented yet:

- LLM-based answer generation;
- final Streamlit conversational interface;
- deployment;
- selected code snippets;
- test file extraction;
- advanced source-aware reranking.

---

## Sources used to build the corpus

DocAsk currently builds its corpus from the following source types.

### 1. Markdown / reStructuredText documentation

Configured with:

```yaml
docs_path: ../../mmore/docs/source
```

The Markdown loader reads `.md` and `.rst` files, splits them into sections, and creates one `DocumentRecord` per section.

Source type:

```text
markdown_section
```

Used for questions such as:

```text
How do I install MMORE?
How do I run the indexing pipeline?
What is the RAG module?
How does processing work?
```

---

### 2. Python code documentation

Configured with:

```yaml
code_path: ../../mmore/src/mmore
package_name: mmore
```

The Python extractor uses the built-in `ast` module to extract:

- module docstrings;
- class docstrings;
- function signatures and docstrings;
- method signatures and docstrings.

Source types:

```text
python_module
python_class
python_function
python_method
```

Used for questions such as:

```text
What is the signature of get_latest_reports?
What does Retriever.retrieve do?
Which arguments does this function take?
```

The extractor does not index full raw code at this stage.

---

### 3. YAML configuration files

Configured with:

```yaml
include_yaml_configs: true
yaml_config_paths:
  - ../../mmore/examples
  - ../../mmore/production-config
```

DocAsk loads `.yaml` and `.yml` files from the configured paths.

If a repository does not have YAML files or does not have an `examples/` folder, DocAsk skips this source type without failing.

Source types:

```text
example_config
production_config
yaml_config
```

Used for questions such as:

```text
What should the indexing config look like?
Show me an example RAG config.
How do I configure the retriever?
What fields are required in an indexing config?
```

---

### 4. Repository structure summary

Configured with:

```yaml
include_repo_structure: true
repo_path: ../../mmore
repo_structure_max_depth: 4
```

DocAsk generates a synthetic tree view of the repository.

Source type:

```text
repo_structure
```

Used for questions such as:

```text
Where is the retriever implemented?
Where are the example configs?
Where is the documentation stored?
What is the structure of the repository?
```

---

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
│   ├── app_config.yaml
│   ├── mmore_index_config.yaml
│   └── mmore_retriever_config.yaml
├── data/
│   ├── raw/
│   ├── processed/
│   ├── extracted_code_docs/
│   └── indexes/
├── scripts/
│   ├── build_corpus.py
│   ├── export_mmore_corpus.py
│   ├── build_index.py
│   ├── extract_code_docs.py
│   ├── preview_corpus.py
│   ├── debug_retrieval.py
│   ├── debug_prompting.py
│   ├── prepare_answer.py
│   ├── answer_question.py
│   └── run_app.sh
├── src/
│   └── docask/
│       ├── __init__.py
│       ├── config.py
│       ├── data_models.py
│       ├── loaders/
│       │   ├── markdown_loader.py
│       │   ├── yaml_config_loader.py
│       │   └── repo_structure_loader.py
│       ├── extractors/
│       │   └── python_doc_extractor.py
│       ├── corpus/
│       │   └── builder.py
│       ├── indexing/
│       │   ├── mmore_format.py
│       │   └── mmore_indexer.py
│       ├── retrieval/
│       │   ├── base.py
│       │   ├── simple_retriever.py
│       │   ├── mmore_retriever.py
│       │   └── retriever_factory.py
│       ├── rag/
│       │   ├── prompting.py
│       │   ├── extractive_answerer.py
│       │   └── answering.py
│       ├── app/
│       │   └── streamlit_app.py
│       └── utils/
│           └── paths.py
└── tests/
```

---

## Main modules

### `src/docask/data_models.py`

Defines the internal document format used by DocAsk.

The main model is `DocumentRecord`, which represents one indexable unit.

It includes:

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

All source types are converted into this common format.

---

### `src/docask/loaders/markdown_loader.py`

Loads Markdown and reStructuredText documentation.

It creates section-level records with metadata such as:

- relative path;
- page title;
- section title;
- heading level;
- documentation domain.

---

### `src/docask/extractors/python_doc_extractor.py`

Extracts Python documentation using `ast`.

It extracts:

- modules;
- classes;
- functions;
- methods;
- signatures;
- docstrings.

It does not index full raw code at this stage.

---

### `src/docask/loaders/yaml_config_loader.py`

Loads YAML configuration files from configured paths and converts them into `DocumentRecord` objects.

It is tolerant:

- missing paths are skipped;
- repositories without YAML files are supported;
- source types are inferred from the path when possible.

For example:

```text
examples/index/config.yaml          → example_config
production-config/rag/config.yaml   → production_config
other/config.yaml                    → yaml_config
```

---

### `src/docask/loaders/repo_structure_loader.py`

Generates a synthetic repository tree document.

It excludes noisy directories such as:

- `.git`;
- `__pycache__`;
- `.venv`;
- `dist`;
- `build`;
- `.pytest_cache`;
- `node_modules`.

It keeps useful files such as:

- `.py`;
- `.md`;
- `.rst`;
- `.yaml`;
- `.yml`;
- `.toml`;
- `.json`;
- `.txt`.

---

### `src/docask/corpus/builder.py`

Builds the final DocAsk corpus by combining:

- Markdown documentation;
- Python code documentation;
- YAML configuration files;
- repository structure summary.

The output is:

```text
data/processed/corpus.jsonl
```

Each line is a serialized `DocumentRecord`.

---

### `src/docask/indexing/mmore_format.py`

Converts the internal DocAsk corpus into a MMORE-compatible JSONL format.

MMORE expects records shaped like:

```json
{
  "text": "...",
  "modalities": [],
  "metadata": {}
}
```

The output is:

```text
data/processed/mmore_corpus.jsonl
```

DocAsk adds a short source header to each text field before indexing so that source information can be reconstructed after MMORE retrieval.

---

### `src/docask/indexing/mmore_indexer.py`

Internal wrapper around MMORE indexing.

It calls MMORE through Python internally:

```bash
python -m mmore index ...
```

The user does not call this command directly.

---

### `src/docask/retrieval/base.py`

Defines shared retrieval objects.

The main object is:

```python
RetrievalResult
```

It stores:

- the retrieved `DocumentRecord`;
- the retrieval score.

This type is backend-independent and can be used by both the simple retriever and MMORE retriever.

---

### `src/docask/retrieval/simple_retriever.py`

Temporary local retriever used for debugging and comparison.

It does not use MMORE. It ranks documents with token-overlap heuristics and small boosts for code symbols, signatures, titles, and documentation pages.

It is useful to quickly test the corpus without rebuilding the MMORE index.

---

### `src/docask/retrieval/mmore_retriever.py`

Internal wrapper around MMORE retrieval.

It uses:

```python
Retriever.from_config(...)
retriever.retrieve(...)
```

and converts raw MMORE results back into DocAsk `RetrievalResult` objects with source metadata.

---

### `src/docask/retrieval/retriever_factory.py`

Selects the retrieval backend.

Available backends:

```text
simple
mmore
```

This allows DocAsk to switch retrieval backends without changing the rest of the answering pipeline.

---

### `src/docask/rag/prompting.py`

Formats retrieved sources into a source-grounded prompt for a future LLM.

The prompt asks the model to:

- answer only from the provided sources;
- cite sources inline;
- say when the sources are insufficient.

---

### `src/docask/rag/extractive_answerer.py`

Temporary answer generator.

It does not call an LLM. It produces a simple answer from the top retrieved source.

This is only used until the LLM generation layer is added.

---

### `src/docask/rag/answering.py`

High-level answering functions.

Current functions:

```python
prepare_answer_prompt(...)
answer_question(...)
```

This module centralizes the flow:

```text
question → retrieval → prompt or answer
```

---

## Configuration files

### `configs/project_config.yaml`

Defines which project to index.

Example for MMORE:

```yaml
project_name: mmore
package_name: mmore

repo_path: ../../mmore
docs_path: ../../mmore/docs/source
code_path: ../../mmore/src/mmore

include_yaml_configs: true
yaml_config_paths:
  - ../../mmore/examples
  - ../../mmore/production-config

include_repo_structure: true
repo_structure_max_depth: 4

include_extensions:
  - .md
  - .rst
  - .py
  - .yaml
  - .yml

exclude_patterns:
  - "__pycache__"
  - ".ipynb_checkpoints"
  - ".DS_Store"
  - ".git"
  - "build"
  - "dist"
  - ".venv"
  - "venv"
```

---

### `configs/indexing_config.yaml`

Contains DocAsk indexing and retrieval settings.

Example:

```yaml
include_markdown: true
include_code_docstrings: true
include_signatures: true
include_code_snippets: false

chunk_size: 1200
chunk_overlap: 150

top_k: 5

retrieval_backend: simple
# retrieval_backend: mmore

collection_name: mmore_docs
mmore_index_config_path: configs/mmore_index_config.yaml
```

Some fields, such as `chunk_size` and `chunk_overlap`, are reserved for later chunking improvements and are not fully used yet.

---

### `configs/mmore_index_config.yaml`

MMORE indexing configuration.

Example:

```yaml
indexer:
  dense_model:
    model_name: sentence-transformers/all-MiniLM-L6-v2
    is_multimodal: false

  sparse_model:
    model_name: splade
    is_multimodal: false

  db:
    uri: ./data/indexes/mmore/proc_demo.db
    name: my_db

collection_name: mmore_docs
documents_path: data/processed/mmore_corpus.jsonl
```

DocAsk calls this internally when building the MMORE index.

---

### `configs/mmore_retriever_config.yaml`

MMORE retrieval configuration.

Example:

```yaml
db:
  uri: ./data/indexes/mmore/proc_demo.db
  name: my_db

hybrid_search_weight: 0.5
k: 5
collection_name: mmore_docs
use_web: false
reranker_model_name: null
```

---

### `configs/app_config.yaml`

Application settings.

Example:

```yaml
app_title: DocAsk
app_subtitle: Ask questions about a project's documentation
show_sources: true
default_top_k: 5
```

---

## Dependencies

DocAsk uses a `src/` layout and is installed in editable mode during development.

Install the project:

```bash
python -m pip install -e .
```

If MMORE is listed as an optional dependency in `pyproject.toml`, install it with:

```bash
python -m pip install -e ".[mmore]"
```

For development dependencies:

```bash
python -m pip install -e ".[dev]"
```

For both development and MMORE support:

```bash
python -m pip install -e ".[dev,mmore]"
```

---

## Usage

Run all commands from the root of the DocAsk repository.

---

### 1. Build the DocAsk corpus

Command:

```bash
PYTHONPATH=src python scripts/build_corpus.py
```

What it does:

- reads `configs/project_config.yaml`;
- loads Markdown and reStructuredText documentation;
- extracts Python docstrings and signatures;
- loads YAML configuration files if enabled;
- generates a repository structure document if enabled;
- saves the unified corpus as JSONL.

Output file:

```text
data/processed/corpus.jsonl
```

What you should see:

```text
Building DocAsk corpus
--------------------------------------------------------------------------------
project_name: mmore
package_name: mmore
repo_path: ../../mmore
docs_path: ../../mmore/docs/source
code_path: ../../mmore/src/mmore
include_yaml_configs: True
yaml_config_paths: ['../../mmore/examples', '../../mmore/production-config']
include_repo_structure: True
repo_structure_max_depth: 4
--------------------------------------------------------------------------------
Loaded 246 markdown documents
Loaded 246 code documents
Loaded 52 YAML config documents
Loaded 1 repo structure documents

Built corpus with 545 documents
Saved to: .../data/processed/corpus.jsonl
Breakdown by source_type:
  - markdown_section: 246
  - python_function: 58
  - python_module: 10
  - python_class: 49
  - python_method: 129
  - example_config: 46
  - production_config: 6
  - repo_structure: 1
```

The exact numbers may change if the indexed repository changes.

---

### 2. Preview the corpus

Command:

```bash
PYTHONPATH=src python scripts/preview_corpus.py --limit 2
```

What it does:

- opens `data/processed/corpus.jsonl`;
- prints a readable preview of the first records;
- helps verify that corpus building worked.

What you should see:

```text
================================================================================
doc_id: markdown::index.md::0-mmore-documentation
title: MMORE Documentation
section_title: MMORE Documentation
source_type: markdown_section
relative_path: index.md
module_name: None
symbol_name: None
signature: None

MMORE is an open-source multimodal ingestion and retrieval framework...
```

Useful filters:

```bash
PYTHONPATH=src python scripts/preview_corpus.py --source-type markdown_section --limit 3
PYTHONPATH=src python scripts/preview_corpus.py --source-type python_function --limit 3
PYTHONPATH=src python scripts/preview_corpus.py --source-type python_class --limit 3
PYTHONPATH=src python scripts/preview_corpus.py --source-type python_method --limit 3
PYTHONPATH=src python scripts/preview_corpus.py --source-type example_config --limit 3
PYTHONPATH=src python scripts/preview_corpus.py --source-type production_config --limit 3
PYTHONPATH=src python scripts/preview_corpus.py --source-type repo_structure --limit 1
```

---

### 3. Debug local retrieval

Command:

```bash
PYTHONPATH=src python scripts/debug_retrieval.py "How do I configure indexing?"
```

What it does:

- loads `data/processed/corpus.jsonl`;
- runs the local simple retriever;
- prints the top retrieved documents with scores and metadata.

What you should see:

```text
Query: How do I configure indexing?
Results: 5

================================================================================
#1 score=...
doc_id: ...
title: ...
source_type: ...
relative_path: ...
section_title: ...
module_name: ...
symbol_name: ...
signature: ...

...
```

This script is useful for checking whether the corpus contains the right sources and whether the simple retriever finds reasonable documents.

The simple retriever is only a debugging backend. It does not use embeddings or MMORE.

---

### 4. Debug prompt construction

Command:

```bash
PYTHONPATH=src python scripts/debug_prompting.py "How do I configure indexing?"
```

What it does:

- runs the local simple retriever;
- formats the retrieved documents into a source-grounded prompt;
- prints the prompt that would be sent to an LLM.

What you should see:

```text
Question:
How do I configure indexing?

Sources:
[Source 1] markdown_section — getting_started/indexing.md — ...

score: ...

...

Answer the question using only the sources above.
Cite sources inline using [Source 1], [Source 2], etc.
```

This is useful before connecting LLM generation.

---

### 5. Prepare an answer prompt

Command with the simple backend:

```bash
PYTHONPATH=src python scripts/prepare_answer.py "How do I run the indexing pipeline?" --backend simple
```

What it does:

- retrieves relevant documents;
- builds the final prompt for LLM answer generation;
- prints the prompt and the retrieved sources.

What you should see:

```text
Question:
How do I run the indexing pipeline?

Sources:
[Source 1] ...
...

================================================================================
Retrieved sources:
1. markdown_section | getting_started/indexing.md | ...
2. example_config | examples/index/config.yaml | ...
```

Command with the MMORE backend:

```bash
PYTHONPATH=src python scripts/prepare_answer.py "How do I run the indexing pipeline?" --backend mmore
```

This requires the MMORE-compatible corpus to be exported and indexed first.

---

### 6. Generate a temporary extractive answer

Command:

```bash
PYTHONPATH=src python scripts/answer_question.py "How do I run the indexing pipeline?" --backend simple
```

What it does:

- retrieves relevant documents;
- returns a simple answer from the top retrieved source;
- prints the sources.

What you should see:

```text
Answer:
Based on the most relevant source, here is the answer:

...

Source: [Source 1]

================================================================================
Sources:
1. markdown_section | getting_started/indexing.md | ...
```

This does not call an LLM yet. It is a temporary answerer used to test the pipeline.

---

### 7. Extract Python documentation only

Command:

```bash
PYTHONPATH=src python scripts/extract_code_docs.py
```

What it does:

- reads the configured `code_path`;
- extracts Python module, class, function, and method documentation;
- saves the extracted code documentation separately.

Output file:

```text
data/extracted_code_docs/code_docs.jsonl
```

What you should see:

```text
Extracted 246 code documents
Saved to: .../data/extracted_code_docs/code_docs.jsonl
```

This script is mainly useful for debugging the Python extractor independently from the full corpus build.

---

### 8. Export the corpus for MMORE

Command:

```bash
PYTHONPATH=src python scripts/export_mmore_corpus.py
```

What it does:

- reads `data/processed/corpus.jsonl`;
- converts each `DocumentRecord` into a MMORE-compatible JSONL sample;
- writes the converted corpus.

Output file:

```text
data/processed/mmore_corpus.jsonl
```

What you should see:

```text
Exporting corpus to MMORE format
--------------------------------------------------------------------------------
corpus_path: .../data/processed/corpus.jsonl
corpus_exists: True
output_path: .../data/processed/mmore_corpus.jsonl
--------------------------------------------------------------------------------
output_exists: True
Exported MMORE-compatible corpus to: .../data/processed/mmore_corpus.jsonl
```

---

### 9. Build the MMORE index

Command:

```bash
PYTHONPATH=src python scripts/build_index.py
```

What it does:

- reads `configs/indexing_config.yaml`;
- uses `configs/mmore_index_config.yaml`;
- indexes `data/processed/mmore_corpus.jsonl` with MMORE;
- stores the index under `data/indexes/mmore/`.

What you should see:

```text
Building MMORE index
--------------------------------------------------------------------------------
config_path: configs/mmore_index_config.yaml
documents_path: .../data/processed/mmore_corpus.jsonl
collection_name: mmore_docs
--------------------------------------------------------------------------------
...
MMORE index built successfully
```

This step can take longer than the simple backend because it builds the actual MMORE retrieval index.

---

### 10. Run the Streamlit app

If `scripts/run_app.sh` is available:

```bash
scripts/run_app.sh
```

Equivalent command:

```bash
PYTHONPATH=src streamlit run src/docask/app/streamlit_app.py
```

What it does:

- starts the Streamlit interface;
- loads the configured backend;
- allows the user to ask questions through a web UI.

What you should see:

```text
Local URL: http://localhost:8501
```

The Streamlit interface is still under development.

---

## Full local workflow

Use this workflow when starting from scratch with the simple backend:

```bash
PYTHONPATH=src python scripts/build_corpus.py
PYTHONPATH=src python scripts/preview_corpus.py --limit 2
PYTHONPATH=src python scripts/debug_retrieval.py "How do I configure indexing?"
PYTHONPATH=src python scripts/prepare_answer.py "How do I configure indexing?" --backend simple
PYTHONPATH=src python scripts/answer_question.py "How do I configure indexing?" --backend simple
```

Use this workflow when rebuilding the MMORE backend:

```bash
rm -rf data/indexes/mmore
mkdir -p data/indexes/mmore

PYTHONPATH=src python scripts/build_corpus.py
PYTHONPATH=src python scripts/export_mmore_corpus.py
PYTHONPATH=src python scripts/build_index.py
PYTHONPATH=src python scripts/prepare_answer.py "How do I configure indexing?" --backend mmore
```

---

## Development checks

After moving files or changing imports, run:

```bash
python -m compileall src scripts
```

What it does:

- checks that all Python files can be compiled;
- catches syntax errors and broken imports early.

You should see no `SyntaxError`.

To check that old imports were removed after the package reorganization:

```bash
grep -R "docask.retrieval.answering\|docask.retrieval.prompting\|docask.retrieval.extractive_answerer\|docask.retrieval.mmore_format\|docask.retrieval.mmore_indexer" -n src scripts
```

This command should return nothing.

To remove generated Python cache files:

```bash
find . -type d -name "__pycache__" -prune -exec rm -rf {} +
rm -rf src/docask.egg-info
```

---

## Development notes

Important design choices:

- DocAsk keeps its own internal `DocumentRecord` format.
- MMORE is used internally for indexing and retrieval.
- The simple retriever remains available for debugging.
- Markdown and code documentation are stored in the same corpus.
- YAML examples are indexed because they are important for configuration questions.
- Repository structure is indexed to support navigation questions.
- MMORE retrieval results are converted back into DocAsk source objects for citations.
- RAG-related logic is separated from retrieval logic:
  - `retrieval/` finds documents;
  - `rag/` builds prompts and answers;
  - `indexing/` handles MMORE export and indexing.

---

## Next steps

Planned next steps:

1. Add LLM generation with a local model such as `qwen3:8b` through Ollama.
2. Replace the extractive answerer with source-grounded LLM generation.
3. Build a minimal Streamlit chat interface.
4. Display retrieved sources under each answer.
5. Improve source-aware reranking, especially for configuration questions.
6. Add selected code snippets when docstrings are insufficient.
7. Add test extraction for examples of expected behavior.
8. Deploy the application.
