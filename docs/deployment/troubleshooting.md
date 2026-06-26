# Deployment troubleshooting

This page covers common problems with the EPFL Docker deployment. Start with the
user guide in {doc}`cluster` and the maintenance checks in {doc}`maintainer`.

## The browser cannot reach the site

Use the full URL, including port `1312` and the final slash:

<http://gpu217.rcp.epfl.ch:1312/githelp/>

Connect to the EPFL VPN when outside the EPFL network. If the service is still
unreachable, a maintainer should run:

```bash
docker compose ps
docker compose logs --tail=100 githelp
```

## The page is blank

Confirm that the URL ends with `/`, then perform a hard refresh:

<http://gpu217.rcp.epfl.ch:1312/githelp/>

Check that the GitHelp and Traefik containers share the `traefik` network and
that the labels in `docker-compose.yml` are attached to the running container.

## `curl localhost:8501` fails on the host

This is expected for the server Compose file because port `8501` is not
published on the host. Traefik reaches it through the Docker network.

Test inside the container instead:

```bash
docker exec -it githelp curl http://localhost:8501/_stcore/health
```

## GitHelp is healthy but Traefik does not route it

Inspect the labels and networks:

```bash
docker inspect githelp --format '{{json .Config.Labels}}'
docker inspect githelp --format '{{json .NetworkSettings.Networks}}'
docker inspect root-traefik-1 --format '{{json .NetworkSettings.Networks}}'
```

Both services must share the external `traefik` network. The configured router matches /githelp, strips that prefix, and forwards the remaining path to Streamlit running at / inside the container.

## A local project path does not exist

Paths entered in Streamlit are evaluated inside the GitHelp container. Use:

```text
/app/data/repositories/<repository_folder>
```

not the corresponding host path under `/home/githelp/GitHelp/`.

## MMORE indexing reports FAISS AVX warnings

Messages such as these are not necessarily fatal:

```text
Could not load library with AVX512 support
Could not load library with AVX2 support
Successfully loaded faiss
```

If FAISS eventually reports a successful load, inspect the later exception or
the Streamlit build output for the actual failure.

## Transformers or tokenizer incompatibility

GitHelp pins Transformers below version 5 because the current MMORE sparse-model
path depends on Transformers 4 APIs:

```text
transformers>=4.51.0,<5
```

Confirm the installed version inside the container:

```bash
docker exec -it githelp python -c "import transformers; print(transformers.__version__)"
```

Rebuild the Docker image without cache if its dependency layer is stale.

## PyTorch is too old

The Dockerfile uses:

```dockerfile
FROM pytorch/pytorch:2.6.0-cuda12.4-cudnn9-runtime
```

After changing the base image or dependencies, rebuild cleanly:

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

## CUDA is unavailable in the container

Check PyTorch and the selected devices:

```bash
docker exec -it githelp python -c "import torch; print(torch.version.cuda); print(torch.cuda.is_available()); print(torch.cuda.device_count())"
```

The server Compose file requests GPU access and currently sets
`NVIDIA_VISIBLE_DEVICES=1`. A device count of one can therefore be correct even
when the host has several GPUs. If CUDA is unavailable, verify the NVIDIA
Container Toolkit and Docker GPU configuration on the host.

## The first answer is slow

The local Qwen model is loaded on the first LLM request and then cached by
Streamlit. Hugging Face files are also cached in the persistent
`githelp_hf_cache` volume. Check GPU activity with:

```bash
watch -n 1 nvidia-smi
```

## The selected MMORE backend returns unexpected sources

Open **Latest answer sources and diagnostics** and check the reported mode:

```text
native_index
corpus_fallback
```

`corpus_fallback` means native retrieval failed and GitHelp used lexical
retrieval over the exported MMORE corpus. If the mode is `native_index`, verify
that the shared index was most recently built from the selected project's
`mmore_corpus.jsonl`.

The application currently uses `mmore_docs`. An index manually built under a
different collection name will not be queried by the default retrieval config.

## The MMORE index is incomplete

A failed build can leave incomplete local metadata. Rebuild through the
Streamlit **Build MMORE index** action or use the manual command documented in
{doc}`maintainer`. The index wrapper resets the local Milvus Lite database before
building, so confirm that replacing the currently indexed project is intended.

## Validated deployment characteristics

The repository deployment configuration is designed for:

- Docker Compose;
- Traefik routing under `/githelp`;
- CUDA-enabled PyTorch 2.6 with CUDA 12.4;
- persistent project data and Hugging Face caches;
- Tesla V100-class server GPUs;
- MMORE index building and Streamlit access from the EPFL network or VPN.

Runtime availability should still be verified with the health, log, and GPU
commands above after each deployment update.
