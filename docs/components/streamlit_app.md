# Streamlit app

The Streamlit app is the future user-facing interface for DocAsk.

Current file:

```text
src/docask/app/streamlit_app.py
```

## Goal

The app should let a user:

- type a question about the indexed project;
- choose or configure retrieval settings;
- receive an answer;
- inspect retrieved sources.

## Run command

```bash
scripts/run_app.sh
```

Equivalent command:

```bash
PYTHONPATH=src streamlit run src/docask/app/streamlit_app.py
```

## Current status

The interface is still under development.

The backend pipeline is being prepared first:

```text
corpus -> retrieval -> prompt -> answer
```