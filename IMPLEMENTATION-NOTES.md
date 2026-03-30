This is the first runnable implementation bundle for the v3 target architecture.

What is real:
- Core job API with Postgres persistence
- Worker that parses files and ingests/querys through RAG
- Parser service for TXT/MD/CSV/JSON/PDF/DOCX/XLSX/PPTX/EML/MSG
- OCR fallback for PDFs via `ocrmypdf`
- Embedding service via Ollama embeddings or hash fallback
- RAG service with Qdrant and answer generation via `llm-router`
- LLM router for vLLM vs Ollama
- Audio service with faster-whisper transcription and simple speaker enrollment/identify

What is still deliberately basic:
- no advanced queue/bus yet
- no mail polling connector yet
- no full frontend
- speaker identification is lightweight MFCC-based, not pyannote-grade
