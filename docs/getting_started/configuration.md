# Configuration

DocAsk uses YAML configuration files stored in `configs/`.

## `project_config.yaml`

This is the main file to edit when changing the project indexed by DocAsk.

For example:
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
```

### Main fields

| Field | Meaning |
|---|---|
| `project_name` | Human-readable project name stored in metadata. |
| `package_name` | Python package prefix used to build full module names. |
| `repo_path` | Root folder of the target repository. |
| `docs_path` | Folder containing Markdown or reStructuredText docs. |
| `code_path` | Python source folder used for docstring extraction. |
| `include_yaml_configs` | Whether to include YAML files in the corpus. |
| `yaml_config_paths` | Folders scanned for `.yaml` and `.yml` files. |
| `include_repo_structure` | Whether to add a synthetic repository tree document. |
| `repo_structure_max_depth` | Maximum depth of the generated repository tree. |

## `indexing_config.yaml`

This file controls general corpus and retrieval settings.

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

Some fields, such as `chunk_size` and `chunk_overlap`, are kept for future chunking improvements. The current prototype mostly relies on Markdown sections and extracted code documentation records.

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
    uri: ./data/indexes/mmore/proc_demo.db
    name: my_db

collection_name: mmore_docs
documents_path: data/processed/mmore_corpus.jsonl
```

## `mmore_retriever_config.yaml`

This file configures MMORE retrieval.

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

## `app_config.yaml`

This file stores UI-level settings.

```yaml
app_title: DocAsk
app_subtitle: Ask questions about a project's documentation
show_sources: true
default_top_k: 5
```
