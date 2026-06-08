"""
Planned GitHub repository loading helpers.

The intended workflow is:
1. accept a public GitHub repository URL from the Streamlit UI or CLI;
2. clone or download the repository into a local GitHelp-managed folder;
3. pass that local path through the existing project config, indexing, retrieval,
   and RAG pipeline.

The current supported project setup path is local repositories.
"""
