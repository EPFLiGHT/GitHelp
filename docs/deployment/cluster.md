# Using GitHelp on the EPFL lab server

GitHelp is deployed on the EPFL GPU server and is accessible from the EPFL network or VPN at:

```text
http://gpu217.rcp.epfl.ch:1312/githelp/
```

The final `/` is important for Streamlit to load correctly behind the `/githelp` path.

## What GitHelp does

GitHelp is a conversational assistant for exploring software repositories. It lets users ask natural-language questions about a project and retrieves relevant source documents before generating an answer.

GitHelp can inspect:

- documentation files;
- configuration files;
- repository structure;
- Python modules, docstrings, and function signatures;
- generated GitHelp and MMORE corpora.

Typical questions include:

```text
How do I install this project?
```

```text
How do I configure indexing?
```

```text
Where is this function implemented?
```

```text
What does this configuration file do?
```

```text
Which sources support the answer?
```

## Basic user workflow

### 1. Open the interface

Open:

```text
http://gpu217.rcp.epfl.ch:1312/githelp/
```

If the page is not reachable, connect to the EPFL VPN and try again.

### 2. Load a repository

Users can either:

- clone a public GitHub repository from the interface;
- or use a repository that already exists on the server.

Repositories cloned by GitHelp are stored under:

```text
data/repositories/
```

Inside the Docker container, the same folder is visible as:

```text
/app/data/repositories/
```

This distinction matters: GitHelp runs inside Docker, so local paths entered in the interface should use container paths, for example:

```text
/app/data/repositories/mmore
```

and not server paths such as:

```text
/home/githelp/GitHelp/data/repositories/mmore
```

### 3. Build the GitHelp corpus

The GitHelp corpus extracts useful content from the repository, including documentation, configuration files, repository structure, and Python API information.

Generated project files are stored under:

```text
data/projects/
```

Inside the container, this corresponds to:

```text
/app/data/projects/
```

### 4. Export to MMORE format

When using the MMORE backend, the GitHelp corpus is exported to an MMORE-compatible JSONL file, typically stored as:

```text
/app/data/projects/<project_name>/mmore_corpus.jsonl
```

### 5. Build the MMORE index

After exporting the corpus, build the MMORE index from the interface.

This step can take some time, especially on the first run, because models may need to be downloaded and loaded. Subsequent runs are usually faster thanks to the persistent Hugging Face cache.

### 6. Select the retrieval backend

Use the simple backend first when checking whether a corpus was built correctly.

Use the MMORE backend after the MMORE index has been built.

### 7. Ask questions

Once the corpus and index are ready, ask questions in the chat interface.

Always inspect the retrieved sources when accuracy matters. GitHelp is designed to provide source-grounded answers, but the retrieved documents should still be checked for important use cases.

## Recommended first test

After loading a repository, start with simple questions:

```text
How do I install this project?
```

```text
What are the main modules of this repository?
```

```text
How do I configure indexing?
```

Then move to more specific questions about files, functions, or configuration options.

## Notes and limitations

- The deployed interface is intended for internal EPFL/lab use.
- Public GitHub repositories can be cloned from the interface.
- Private repositories may require additional authentication setup.
- The first model loading step can be slow.
- MMORE indexing can take time on larger repositories.
- The Docker image is CUDA-enabled and can access the server GPUs.
- The current deployment uses Traefik and is served under `/githelp`.
- If the interface loads as a blank page, make sure the URL ends with `/`.

## Maintainer guide

### SSH access

From a local machine, configure SSH with:

```sshconfig
Host moove-gpus
    HostName gpu217.rcp.epfl.ch
    User githelp
```

Then connect with:

```bash
ssh moove-gpus
```

### Repository location on the server

The GitHelp repository is located at:

```text
~/GitHelp
```

Go to the project folder:

```bash
cd ~/GitHelp
```

### Check the current deployment

List running containers:

```bash
docker ps
```

Check the GitHelp service:

```bash
docker compose ps
```

Inspect logs:

```bash
docker compose logs -f githelp
```

Check that GitHelp responds inside the container:

```bash
docker exec -it githelp curl http://localhost:8501/_stcore/health
```

Expected output:

```text
ok
```

### Update the deployed version

From the server:

```bash
cd ~/GitHelp
git pull
docker compose up -d --build
```

Then check logs:

```bash
docker compose logs -f githelp
```

### Restart GitHelp

```bash
cd ~/GitHelp
docker compose restart githelp
```

### Stop GitHelp

```bash
cd ~/GitHelp
docker compose down
```

### Rebuild from scratch

Use this when dependencies or the Dockerfile changed:

```bash
cd ~/GitHelp
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Verify GPU access

Check GPU availability on the host:

```bash
nvidia-smi
```

Check GPU availability inside the GitHelp container:

```bash
docker exec -it githelp python -c "import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available()); print(torch.cuda.device_count())"
```

Expected output should show CUDA available, for example:

```text
2.6.0+cu124
12.4
True
4
```

### Monitor GPU usage

While GitHelp is generating an answer, run:

```bash
watch -n 1 nvidia-smi
```

This shows whether the LLM is using GPU memory and compute.

## Docker deployment details

GitHelp is served through Traefik.

The working URL is:

```text
http://gpu217.rcp.epfl.ch:1312/githelp/
```

The Docker Compose configuration connects GitHelp to the external Traefik network and exposes the internal Streamlit service on port `8501`.

A typical Traefik label configuration is:

```yaml
labels:
  - traefik.enable=true
  - traefik.http.routers.githelp.entrypoints=web
  - traefik.http.routers.githelp.rule=PathPrefix(`/githelp`)
  - traefik.http.middlewares.strip-githelp.stripprefix.prefixes=/githelp
  - traefik.http.routers.githelp.middlewares=strip-githelp
  - traefik.http.services.githelp.loadbalancer.server.port=8501
```

The GitHelp and Traefik containers must be on the same Docker network. On the current server, the network is:

```text
traefik
```

To verify:

```bash
docker inspect root-traefik-1 --format '{{json .NetworkSettings.Networks}}'
docker inspect githelp --format '{{json .NetworkSettings.Networks}}'
```

Both containers should appear on the same network.

## Important path conventions

GitHelp runs inside Docker.

Server path:

```text
/home/githelp/GitHelp/data/repositories/<repo_name>
```

Container path:

```text
/app/data/repositories/<repo_name>
```

When entering a local repository path in the GitHelp interface, use the container path:

```text
/app/data/repositories/<repo_name>
```

The same applies to project data:

```text
/app/data/projects/<project_name>
```

## Manual MMORE index build

If indexing fails from the interface, enter the container:

```bash
docker exec -it githelp bash
```

Then run:

```bash
/opt/conda/bin/python /app/scripts/build_index.py \
  --documents-path /app/data/projects/<project_name>/mmore_corpus.jsonl \
  --collection-name <project_name>_docs
```

Example:

```bash
/opt/conda/bin/python /app/scripts/build_index.py \
  --documents-path /app/data/projects/multimeditron/mmore_corpus.jsonl \
  --collection-name multimeditron_docs
```

A successful run ends with:

```text
MMORE index built successfully
```

## Troubleshooting

### The browser says “site can’t be reached”

Check that the URL includes port `1312` and ends with `/`:

```text
http://gpu217.rcp.epfl.ch:1312/githelp/
```

If outside EPFL, connect to the EPFL VPN.

### The page is blank

Use the URL with the final slash:

```text
http://gpu217.rcp.epfl.ch:1312/githelp/
```

Then refresh the page.

### `curl localhost:8501` fails on the server

This is expected if port `8501` is not published on the host. GitHelp is routed through Traefik.

Instead, test inside the container:

```bash
docker exec -it githelp curl http://localhost:8501/_stcore/health
```

### GitHelp works in the container but not in the browser

Check Traefik:

```bash
docker ps
docker network ls
docker inspect githelp --format '{{json .Config.Labels}}'
```

Also check that Traefik and GitHelp share the same Docker network.

### MMORE indexing complains about FAISS AVX512 or AVX2

Warnings such as:

```text
Could not load library with AVX512 support
Could not load library with AVX2 support
Successfully loaded faiss
```

are not necessarily errors. If FAISS eventually loads successfully, the problem is elsewhere.

### Transformers complains that torch must be at least 2.6

Use a CUDA-enabled PyTorch image with torch >= 2.6, for example:

```dockerfile
FROM pytorch/pytorch:2.6.0-cuda12.4-cudnn9-runtime
```

Then rebuild:

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

### The model is slow

The first run may be slow because Hugging Face models are downloaded and cached.

Check whether the GPU is being used:

```bash
watch -n 1 nvidia-smi
```

Also check from inside the container:

```bash
docker exec -it githelp python -c "import torch; print(torch.cuda.is_available())"
```

If this prints `False`, the container is not using CUDA.

## Current validated setup

The current deployment has been validated with:

```text
Docker Compose
Traefik routing under /githelp
CUDA-enabled PyTorch
torch 2.6.0+cu124
CUDA 12.4
Tesla V100 GPUs visible from inside the container
MMORE index build working
Streamlit interface accessible from the EPFL network/VPN
```
