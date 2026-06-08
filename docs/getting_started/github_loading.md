# GitHub repository loading

GitHelp can prepare a public GitHub repository by cloning it locally and then
using the same project setup pipeline as a local path.

## Streamlit workflow

Run the app:

```bash
streamlit run app/streamlit_app.py
```

In **Project setup**, choose:

```text
Public GitHub repository URL
```

Then enter a public repository URL, for example:

```text
https://github.com/swiss-ai/mmore
```

GitHelp clones the repository into:

```text
data/repositories/swiss-ai-mmore/
```

After that, choose one of the build actions:

```text
Build simple index
Build MMORE index
```

The simple index is the fastest first check because it only builds the GitHelp
JSONL corpus and uses the local simple retriever.

## Command-line workflow

To clone or reuse a repository and build a simple index in one command:

```bash
python scripts/prepare_github_project.py \
  https://github.com/swiss-ai/mmore
```

This prints:

- the local repository path;
- the generated project name;
- the generated project config path;
- the generated corpus path.

The resulting corpus can be used with:

```bash
python scripts/prepare_answer.py \
  "What is MMORE used for?" \
  --backend simple \
  --corpus-path data/projects/mmore/corpus.jsonl
```

## Loading only

If you only want to clone or reuse the repository without building the corpus:

```bash
python scripts/load_github_repository.py \
  https://github.com/swiss-ai/mmore
```

## Supported URLs

GitHelp accepts:

```text
https://github.com/owner/repo
https://github.com/owner/repo.git
git@github.com:owner/repo.git
```

The clone operation uses the normalized HTTPS URL.

## Current limitations

- Private repositories are not supported yet.
- Existing local clones are reused as-is; GitHelp does not automatically pull updates.
- The MMORE backend still requires a matching MMORE export and index.
