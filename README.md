# DocAsk

DocAsk is a conversational assistant for querying a software project's documentation and code-related knowledge in natural language.

The initial use case is the [MMORE](https://github.com/swiss-ai/mmore) repository. DocAsk uses MMORE internally for indexing and retrieval, while exposing a simpler project-level interface to the user.

The user does not need to call MMORE directly.

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
MMORE-compatible export
        ↓
MMORE indexing
        ↓
MMORE retrieval
        ↓
prompt construction
        ↓
LLM answer generation
        ↓
Streamlit UI
```

At the moment, the project supports corpus building, MMORE indexing, MMORE retrieval, prompt preparation, and a temporary extractive answerer.

LLM generation and the Streamlit interface are the next steps.

---

## Current status

Implemented:

- Markdown documentation loading;
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
- Streamlit conversational interface;
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
Which arguments does the index command take?
```

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

If a repository does not have YAML files or does not have an `examples/` folder, DocAsk simply skips this source type without failing.

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
│       │   ├── markdown_loader.py
│       │   ├── yaml_loader.py
│       │   └── repo_structure_loader.py
│       ├── extractors/
│       │   └── python_doc_extractor.py
│       ├── corpus/
│       │   └── builder.py
│       ├── retrieval/
│       │   ├── simple_retriever.py
│       │   ├── mmore_format.py
│       │   ├── mmore_indexer.py
│       │   ├── mmore_retriever.py
│       │   ├── retriever_factory.py
│       │   ├── prompting.py
│       │   ├── answering.py
│       │   └── extractive_answerer.py
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

It creates structured section-level records with metadata such as:

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

### `src/docask/loaders/yaml_loader.py`

Loads YAML configuration files from configured paths.

It is generic and tolerant:

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

### `src/docask/retrieval/mmore_format.py`

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

### `src/docask/retrieval/mmore_indexer.py`

Internal wrapper around MMORE indexing.

It calls MMORE through Python internally:

```bash
python -m mmore index ...
```

The user does not call this command directly.

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

### `src/docask/retrieval/simple_retriever.py`

Temporary local retriever used for debugging and comparison.

It does not use MMORE. It is useful to quickly test the corpus without rebuilding the MMORE index.

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

### `src/docask/retrieval/prompting.py`

Formats retrieved sources into a source-grounded prompt for a future LLM.

The prompt asks the model to:

- answer only from the provided sources;
- cite sources inline;
- say when the sources are insufficient.

---

### `src/docask/retrieval/extractive_answerer.py`

Temporary answer generator.

It does not call an LLM. It produces a simple answer from the top retrieved source.

This is only used until the LLM generation layer is added.

---

### `src/docask/retrieval/answering.py`

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
retrieval_backend: mmore
collection_name: mmore_docs
mmore_index_config_path: configs/mmore_index_config.yaml
mmore_retriever_config_path: configs/mmore_retriever_config.yaml

chunk_size: 1200
chunk_overlap: 150
top_k: 5
```

Some fields are planned for later chunking improvements and are not fully used yet.

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

DocAsk uses MMORE from PyPI.

The current recommended dependency is:

```toml
"mmore[index,rag]==1.2.2"
```

The project also pins Transformers below version 5 because the MMORE SPLADE sparse retrieval path currently requires a Transformers 4.x-compatible tokenizer API.

```toml
"transformers>=4.44,<5"
```

Install DocAsk in editable mode:

```bash
python -m pip install -e .
```

---

## Usage

Run all commands from the root of the repository.

### 1. Build the DocAsk corpus

```bash
PYTHONPATH=src python scripts/build_corpus.py
```

This creates:

```text
data/processed/corpus.jsonl
```

The corpus contains Markdown documentation, Python docstrings and signatures, YAML configs, and repository structure.

---

### 2. Preview the corpus

Preview the first entries:

```bash
PYTHONPATH=src python scripts/preview_corpus.py
```

Preview Markdown sections:

```bash
PYTHONPATH=src python scripts/preview_corpus.py --source-type markdown_section --limit 3
```

Preview Python functions:

```bash
PYTHONPATH=src python scripts/preview_corpus.py --source-type python_function --limit 3
```

Preview YAML example configs:

```bash
PYTHONPATH=src python scripts/preview_corpus.py --source-type example_config --limit 3
```

Preview production configs:

```bash
PYTHONPATH=src python scripts/preview_corpus.py --source-type production_config --limit 3
```

Preview repository structure:

```bash
PYTHONPATH=src python scripts/preview_corpus.py --source-type repo_structure --limit 1
```

---

### 3. Export the corpus for MMORE

```bash
PYTHONPATH=src python scripts/export_mmore_corpus.py
```

This creates:

```text
data/processed/mmore_corpus.jsonl
```

---

### 4. Build the MMORE index

```bash
PYTHONPATH=src python scripts/build_index.py
```

This internally calls MMORE and builds the vector index in:

```text
data/indexes/mmore/
```

The user does not call MMORE directly.

---

### 5. Test prompt preparation with the MMORE backend

Documentation question:

```bash
PYTHONPATH=src python scripts/prepare_answer.py "How do I run the indexing pipeline?" --backend mmore
```

Code question:

```bash
PYTHONPATH=src python scripts/prepare_answer.py "What is the signature of get_latest_reports?" --backend mmore
```

Configuration question:

```bash
PYTHONPATH=src python scripts/prepare_answer.py "What should the indexing config look like?" --backend mmore
```

Repository navigation question:

```bash
PYTHONPATH=src python scripts/prepare_answer.py "Where is the retriever implemented in the repo?" --backend mmore
```

---

### 6. Use the temporary simple backend

The simple backend does not use MMORE. It is useful for debugging corpus quality.

```bash
PYTHONPATH=src python scripts/prepare_answer.py "How do I run the indexing pipeline?" --backend simple
```

---

### 7. Generate a temporary extractive answer

```bash
PYTHONPATH=src python scripts/answer_question.py "How do I run the indexing pipeline?" --backend mmore
```

This does not call an LLM yet. It only answers from the top retrieved source.

---

## Full rebuild workflow

When the corpus changes, rebuild everything:

```bash
rm -rf data/indexes/mmore
rm -f proc_demo.db
mkdir -p data/indexes/mmore

PYTHONPATH=src python scripts/build_corpus.py
PYTHONPATH=src python scripts/export_mmore_corpus.py
PYTHONPATH=src python scripts/build_index.py
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

---