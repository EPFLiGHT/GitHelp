# DocAsk

DocAsk is a conversational interface for querying project documentation in natural language.

Initial use case: MMORE documentation.

Longer-term goal: support other projects by combining written documentation and documentation extracted from code (e.g. docstrings, signatures, selected code snippets).

## Current status

Project setup and initial prototype in progress.

## Planned components

- documentation ingestion
- corpus building
- indexing and retrieval through MMORE
- Streamlit conversational UI

## Dependencies

This project currently targets `mmore==1.2.1`.

Before using this project, make sure the required system dependencies for MMORE are installed, then install MMORE in the project environment.

## Run 
At the root of the repo:  
`PYTHONPATH=src python scripts/build_corpus.py`  
`PYTHONPATH=src python scripts/preview_corpus.py`  
