# Maintaining the EPFL deployment

This page contains server-side commands for GitHelp maintainers. User-facing
instructions are in {doc}`cluster`; operational failures are covered in
{doc}`troubleshooting`.

## SSH access

A local SSH alias can be configured as:

```text
Host moove-gpus
    HostName gpu217.rcp.epfl.ch
    User githelp
```

Then connect with:

```bash
ssh moove-gpus
```

## Repository location

The deployed checkout is expected at:

```text
~/GitHelp
```

All commands below assume:

```bash
cd ~/GitHelp
```

## Check the current deployment

List the running service and inspect its logs:

```bash
docker compose ps
docker compose logs -f githelp
```

Check the Streamlit health endpoint inside the container:

```bash
docker exec -it githelp curl http://localhost:8501/_stcore/health
```

The expected response is `ok`.

## Update the deployment

```bash
git pull
docker compose up -d --build
docker compose ps
```

Inspect the logs after an update:

```bash
docker compose logs -f githelp
```

## Restart or stop GitHelp

Restart only the GitHelp service:

```bash
docker compose restart githelp
```

Stop the Compose application:

```bash
docker compose down
```

## Rebuild the image without cache

Use a clean image rebuild after dependency or Dockerfile changes:

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

## Verify GPU access

Check the host first:

```bash
nvidia-smi
```

Then inspect PyTorch inside the container:

```bash
docker exec -it githelp python -c "import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available()); print(torch.cuda.device_count())"
```

The current Docker image is based on CUDA-enabled PyTorch 2.6. The exact device
count depends on `NVIDIA_VISIBLE_DEVICES`; `docker-compose.yml` currently selects
GPU `1`, so do not assume that every host GPU will be visible in the container.

Monitor the selected GPU while generating an answer:

```bash
watch -n 1 nvidia-smi
```

## Docker and Traefik routing

The Compose service:

- runs Streamlit on internal port `8501`;
- joins the external `traefik` network;
- exposes no Streamlit host port in the server Compose file;
- uses Traefik's `/githelp` route and strips that prefix before forwarding;
- mounts `./data` at `/app/data`;
- keeps Hugging Face models in the `githelp_hf_cache` volume.

Verify that GitHelp and Traefik share a network:

```bash
docker inspect root-traefik-1 --format '{{json .NetworkSettings.Networks}}'
docker inspect githelp --format '{{json .NetworkSettings.Networks}}'
```

## Host and container paths

GitHelp can only read paths visible inside its container.

| Purpose | Host path | Container path |
|---|---|---|
| Cloned repositories | `/home/githelp/GitHelp/data/repositories/` | `/app/data/repositories/` |
| Project corpora | `/home/githelp/GitHelp/data/projects/` | `/app/data/projects/` |
| MMORE database | `/home/githelp/GitHelp/data/indexes/mmore/` | `/app/data/indexes/mmore/` |

Always enter the container path in the Streamlit project form.

## Build the MMORE index manually

The Streamlit **Build MMORE index** action is preferred because it builds the
corpus, exports it, and indexes it consistently. If indexing must be rerun from
the shell:

```bash
docker exec -it githelp bash
```

Then run inside the container:

```bash
/opt/conda/bin/python /app/scripts/build_index.py \
  --documents-path /app/data/projects/<project_name>/mmore_corpus.jsonl \
  --collection-name mmore_docs
```

The application currently retrieves from the shared `mmore_docs` collection.
Using a different collection name requires corresponding retrieval
configuration and code changes. Building the index resets the local Milvus Lite
database, so this command replaces the previously indexed native project.

A successful run ends with:

```text
MMORE index built successfully
```

## Security note

GitHelp uses a local Milvus Lite database by default. If an external Milvus
service is introduced, keep it on an internal Docker network and do not publish
its ports on `0.0.0.0` unless access controls have been designed explicitly.
