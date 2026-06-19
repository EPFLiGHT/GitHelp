# Configuration

GitHelp uses YAML configuration files stored in `configs/`, plus project-specific configuration files generated under `data/projects/`.

There are two levels of configuration:

```text
configs/
→ global GitHelp settings

data/projects/<project_name>/
→ generated configuration and corpus for a selected target project
```

## `app_config.yaml`

This file stores application-level settings.

Example:

```yaml
app_title: GitHelp
app_subtitle: Ask questions about a project's documentation
show_sources: true
default_top_k: 5

project_profile: mmore

llm:
  provider: qwen
  model_name: Qwen/Qwen3-4B
  max_new_tokens: 512
  temperature: 0.0
  enable_thinking: false
```

MMORE sparse indexing currently requires Transformers 4.x. GitHelp pins:

```text
transformers>=4.51.0,<5
```

If MMORE index building fails with a tokenizer error such as
`BertTokenizer has no attribute batch_encode_plus`, reinstall the compatible
version:

```bash
python -m pip install "transformers>=4.51.0,<5"
```

### Main fields

| Field | Meaning |
|---|---|
| `app_title` | Title used by the app. |
| `app_subtitle` | Subtitle used by the app. |
| `show_sources` | Whether sources should be shown by default. |
| `default_top_k` | Default number of retrieved sources. |
| `project_profile` | Project-specific behavior profile, for example `generic` or `mmore`. |
| `llm.provider` | LLM provider used by GitHelp. |
| `llm.model_name` | Model name used by the provider. |
| `llm.max_new_tokens` | Maximum number of generated tokens. |
| `llm.temperature` | Generation temperature. |
| `llm.enable_thinking` | Whether to enable Qwen thinking mode. |

## `project_config.yaml`

This file describes the target project being indexed.

The default configuration is:

```text
configs/project_config.yaml
```

When using the Streamlit interface, GitHelp also generates a project-specific config:

```text
data/projects/<project_name>/project_config.yaml
```

Example for MMORE:

```yaml
project_name: mmore
package_name: mmore

repo_path: /absolute/path/to/mmore
docs_path: /absolute/path/to/mmore/docs/source
code_path: /absolute/path/to/mmore/src/mmore

include_yaml_configs: true
yaml_config_paths:
  - /absolute/path/to/mmore/examples
  - /absolute/path/to/mmore/production-config

include_repo_structure: true
repo_structure_max_depth: 6
```

### Main fields

| Field | Meaning |
|---|---|
| `project_name` | Project name stored in metadata and used for project folders. |
| `package_name` | Python package prefix used to build full module names. |
| `repo_path` | Root folder of the target repository. |
| `docs_path` | Folder containing Markdown or reStructuredText docs. |
| `code_path` | Python source folder used for docstring extraction. |
| `include_yaml_configs` | Whether to include YAML files in the corpus. |
| `yaml_config_paths` | Folders scanned for `.yaml` and `.yml` files. |
| `include_repo_structure` | Whether to add a synthetic repository tree document. |
| `repo_structure_max_depth` | Maximum depth of the generated repository tree. |

## `indexing_config.yaml`

This file controls MMORE indexing defaults.

```yaml
include_markdown: true
include_code_docstrings: true
include_signatures: true
include_code_snippets: false

chunk_size: 1200
chunk_overlap: 150

top_k: 5
retrieval_backend: simple
collection_name: mmore_docs
mmore_index_config_path: configs/mmore_index_config.yaml
```

Some fields, such as `chunk_size` and `chunk_overlap`, are kept for future chunking improvements. The current implementation mostly relies on Markdown sections and extracted code documentation records.

## `mmore_index_config.yaml`

This file is passed to MMORE when building the index.

```yaml
indexer:
  dense_model:
    model_name: sentence-transformers/all-MiniLM-L6-v2
    is_multimodal: false
  sparse_model:
    model_name: splade
    is_multimodal: false
  db:
    uri: ./data/indexes/mmore/githelp.db
    name: my_db

collection_name: mmore_docs
documents_path: data/processed/mmore_corpus.jsonl
```

## `mmore_retriever_config.yaml`

This file configures MMORE retrieval.

```yaml
db:
  uri: ./data/indexes/mmore/githelp.db
  name: my_db

hybrid_search_weight: 0.5
k: 5
collection_name: mmore_docs
use_web: false
reranker_model_name: null
```

## `data/app_state.json`

The Streamlit app persists the latest local UI state in:

```text
data/app_state.json
```

It can contain:

```json
{
  "project_name": "mmore",
  "project_path": "/path/to/mmore",
  "corpus_path": "/path/to/githelp/data/projects/mmore/corpus.jsonl",
  "project_config_path": "/path/to/githelp/data/projects/mmore/project_config.yaml",
  "backend": "simple",
  "top_k": 5,
  "use_llm": true,
  "show_sources": true,
  "show_full_sources": false,
  "show_debug": false
}
```

This file is machine-specific and should normally be ignored by Git.
