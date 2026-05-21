# Loaders and extractors

DocAsk uses loaders and extractors to convert project sources into `DocumentRecord` objects.

## Markdown loader

File:

```text
src/docask/loaders/markdown_loader.py
```

Role:

- reads `.md` and `.rst` files;
- splits Markdown files by headings;
- creates one record per documentation section;
- stores metadata such as relative path, page title, section title, and heading level.

Main source type:

```text
markdown_section
```

## Python documentation extractor

File:

```text
src/docask/extractors/python_doc_extractor.py
```

Role:

- parses Python files with the built-in `ast` module;
- extracts module docstrings;
- extracts class docstrings;
- extracts function and method docstrings;
- reconstructs readable signatures.

Source types:

```text
python_module
python_class
python_function
python_method
```

Current limitation:

- it does not index full raw code;
- it does not build a dependency graph;
- it ignores symbols without docstrings.

## YAML config loader

File:

```text
src/docask/loaders/yaml_config_loader.py
```

Role:

- scans configured folders for `.yaml` and `.yml` files;
- converts config files into searchable documents;
- adds hints for indexing, RAG, and retriever-related configs.

Source types:

```text
example_config
production_config
yaml_config
```

## Repository structure loader

File:

```text
src/docask/loaders/repo_structure_loader.py
```

Role:

- creates a synthetic tree view of the repository;
- excludes noisy folders such as `.git`, `__pycache__`, `.venv`, `dist`, and `build`;
- includes useful files such as `.py`, `.md`, `.rst`, `.yaml`, `.yml`, `.toml`, `.json`, and `.txt`;
- helps answer navigation questions.

The maximum tree depth is controlled by:

```yaml
repo_structure_max_depth: 6
```

in the project configuration.

Source type:

```text
repo_structure
```
