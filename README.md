# FoodLab v3 application bundle

This bundle implements the first runnable version of the v3 architecture:

- `core-api`: stable integration surface for jobs
- `worker`: background ingestion/query execution
- `parser-service`: Office/PDF/Text/Email parsing with OCR fallback
- `embedding-service`: embeddings via Ollama or deterministic fallback
- `rag-service`: chunking, Qdrant upsert, retrieval
- `llm-router`: routes chat/generation to vLLM or Ollama
- `audio-api`: transcription and speaker enrollment/identify
- updated compose files for `svc` and `ai` roles

The services are designed for Ubuntu 24.04 LTS, Docker Compose and a 2-VM Proxmox layout.
