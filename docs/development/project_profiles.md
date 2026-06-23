# Adding a project profile

Project profiles keep project-specific retrieval and answering behavior out of
the generic RAG pipeline.

Use a profile when a target project needs custom behavior such as:

- query expansion for project-specific terminology;
- filtering noisy source types;
- reranking results for known intents;
- deterministic direct answers for structured questions.

## Relevant files

```text
src/githelp/project_profiles/base.py
src/githelp/project_profiles/generic.py
src/githelp/project_profiles/mmore.py
src/githelp/project_profiles/factory.py
```

## 1. Create a profile class

Add a new module under:

```text
src/githelp/project_profiles/
```

The class should implement the same methods as `ProjectProfile`:

```python
from __future__ import annotations

from githelp.project_profiles.base import ProjectProfile
from githelp.retrieval.base import RetrievalResult


class ExampleProjectProfile(ProjectProfile):
    def expand_query(self, question: str) -> str:
        return question

    def filter_results(
        self,
        results: list[RetrievalResult],
        question: str,
    ) -> list[RetrievalResult]:
        return results

    def rerank_results(
        self,
        results: list[RetrievalResult],
        question: str,
    ) -> list[RetrievalResult]:
        return results

    def answer_directly(
        self,
        question: str,
        results: list[RetrievalResult],
    ) -> str | None:
        return None
```

## 2. Register the profile

Update:

```text
src/githelp/project_profiles/factory.py
```

Add a branch for the profile name:

```python
if profile_name == "example":
    return ExampleProjectProfile()
```

## 3. Select the profile in config

Set the app config field:

```yaml
project_profile: example
```

The profile is selected from an app-level config such as:

```text
configs/app_config.yaml
```

Generated `data/projects/<project_name>/project_config.yaml` files describe
source paths but do not select a profile. The default app config remains set to
`mmore`, so switch it to `generic` or a custom profile when changing projects.

## 4. Add tests

Add focused tests under:

```text
tests/
```

Useful tests include:

- query expansion keeps important original terms;
- filtering removes only the intended sources;
- reranking moves expected sources upward;
- direct answers return `None` when evidence is insufficient.

For profile behavior that depends on retrieved sources, build `DocumentRecord`
and `RetrievalResult` fixtures directly. This keeps tests fast and independent
from MMORE indexes or local LLM models.
