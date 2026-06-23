# Using GitHelp on the EPFL lab server

GitHelp is deployed internally on the EPFL network at:

```text
http://gpu217.rcp.epfl.ch/githelp
```

The service is available from the EPFL network or VPN.

### What GitHelp does

GitHelp lets users ask natural-language questions about a software repository. It can inspect documentation, configuration files, repository structure, and Python API documentation. It retrieves source documents first, then generates source-grounded answers.

Typical questions include:

* How do I install this project?
* How do I configure indexing?
* Where is this function implemented?
* What does this configuration file do?
* Which sources support the answer?

Basic workflow

1. Open the GitHelp interface:
```text
http://gpu217.rcp.epfl.ch/githelp
```

2. Load a target repository.

You can either use a local repository already available on the server, or clone a public GitHub repository from the interface.

Public GitHub repositories are stored under: `data/repositories/`



3. Build the corpus.

This extracts useful documentation, configuration files, repository structure, and Python docstrings/signatures into a GitHelp corpus.

Generated project files are stored under: `data/projects/``

4. Select the retrieval backend.

Use the simple backend first. It is deterministic and usually enough for checking whether the corpus was built correctly.

Use the MMORE backend when an MMORE index has been built.

5. Ask questions.

GitHelp retrieves relevant sources before answering. Always inspect the retrieved sources when checking the reliability of an answer.

### Recommended first test

After loading a repository, ask simple questions first: `How do I install this project?``.  

## For maintainers

To update the deployed version:
```bash
ssh moove-gpus
cd GitHelp
git pull
docker compose up -d --build
```

To inspect logs:
```bash
docker compose logs -f githelp
```

To restart the service:
```bash
docker compose restart githelp
```