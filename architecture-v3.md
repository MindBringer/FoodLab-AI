# FoodLab/pmx/Notes v3 – Zielarchitektur

## Ziel
Ein lokaler, modularer On-Prem-AI-Stack auf Proxmox mit:
- stabilem Core-API-Einstieg für M365 / SharePoint / Power Automate / Frontends
- zentraler Qdrant-Datenbank
- zentraler LLM-Schicht mit Backend-Routing
- sauberer Ingestion/Parsing/Chunking/Embedding-Pipeline
- Audio-Funktionen (Transcribe, Speaker, optional Diarization)
- idempotentem Setup
- belastbarem Backup- und Restore-Konzept

## Leitprinzipien
1. **Core first**: Nur die Core API ist der offizielle Integrationspunkt.
2. **Internal by default**: RAG, Embedding, Parsing, Qdrant, LLM, Audio sind intern.
3. **GPU-aware**: NVIDIA bevorzugt vLLM, AMD bevorzugt Ollama.
4. **Portable data**: Rohdaten, extrahierter Text, Chunks und Konfigurationen bleiben reproduzierbar.
5. **Idempotent deployable**: Mehrfacher Script-Lauf aktualisiert, zerstört aber nicht ungefragt Daten.

## Topologie

### VM 1 – ai-gpu01
Ubuntu Server 24.04 LTS

Rolle:
- LLM-Serving
- Audio-Services
- Modell- und Cache-Speicher

Container:
- llm-router
- vllm (NVIDIA)
- ollama (AMD/Fallback)
- audio-api
- optional diarize-service

### VM 2 – ai-svc01
Ubuntu Server 24.04 LTS

Rolle:
- FoodLab Core API
- Worker
- Parsing/OCR/Mail-Ingest
- Embedding-Service
- RAG
- Qdrant
- Postgres
- Redis
- n8n
- Frontend
- Nginx

Container:
- nginx
- core-api
- worker
- postgres
- redis
- parser-service
- ocr-service
- mail-ingest-service
- embedding-service
- rag-service
- qdrant
- n8n
- frontend

## Datenfluss
1. Quelle liefert Dokument/Text/Audio via `/api/*`, Watch-Ordner oder `/webhook/*`.
2. Core API erzeugt Job in Postgres + Queue in Redis.
3. Worker zieht Job und ruft intern Parser/OCR/Mail-Ingest auf.
4. Normalisiertes Dokument wird in Chunks zerlegt.
5. Embedding-Service erzeugt Vektoren.
6. RAG-Service schreibt Chunks + Metadaten nach Qdrant.
7. Abfragen gehen über Core/Frontend/n8n -> RAG -> LLM Router -> vLLM oder Ollama.

## Netzwerkzonen

### Extern freigegeben
- `/api/*` -> core-api
- `/ui/*` -> frontend
- `/webhook/*` -> n8n
- optional `/audio/*` -> audio-api

### Nur intern
- `/internal/parse/*`
- `/internal/ocr/*`
- `/internal/mail/*`
- `/internal/embed/*`
- `/internal/rag/*`
- `/internal/llm/*`
- Qdrant, Redis, Postgres nie direkt extern

## API-Kontrakte

### Stabil/offiziell
- `GET /health`
- `POST /api/v1/jobs/text`
- `POST /api/v1/jobs/submit`
- `GET /api/v1/jobs/{job_id}`
- `GET /api/v1/jobs/{job_id}/result`

### Intern
- `POST /internal/parse/document`
- `POST /internal/ocr/document`
- `POST /internal/mail/ingest`
- `POST /internal/embed/texts`
- `POST /internal/rag/index`
- `POST /internal/rag/query`
- `POST /internal/llm/chat`
- `POST /internal/audio/transcribe`
- `POST /internal/audio/speakers/enroll`
- `POST /internal/audio/speakers/identify`

## Parser- und Ingestion-Pipeline

### Quellen
- Power Automate HTTP
- On-Prem Gateway File Drop
- SharePoint Exporte
- E-Mail (EML/MSG)
- Frontend Upload
- n8n
- Watch-Ordner

### Parser je Dateityp
- PDF: `pymupdf` / `pdftotext`, bei Scan `ocrmypdf` + `tesseract`
- DOCX/XLSX/PPTX: `python-docx`, `openpyxl`, `python-pptx`, optional `libreoffice --headless`
- Generisch: `Apache Tika`
- EML: MIME-Parser
- MSG: `extract-msg`
- Bilder: `tesseract`

### Normalisiertes Zwischenformat
```json
{
  "doc_id": "uuid",
  "source_type": "pdf|docx|xlsx|pptx|email|text|audio",
  "source_name": "string",
  "title": "string|null",
  "language": "de|en|...",
  "created_at": "ISO-8601|null",
  "sections": [],
  "attachments": [],
  "metadata": {}
}
```

## Chunking
Regeln:
- heading-aware
- paragraph-aware
- table-aware
- page-aware
- slide-aware
- mail-thread-aware

Chunk-Metadaten:
- `doc_id`
- `chunk_id`
- `source_type`
- `source_name`
- `page|sheet|slide`
- `mail_subject`
- `mail_from`
- `language`
- `embedding_model`
- `chunk_version`
- `security_label`

## Embedding-Strategie
Eigener Dienst statt direkt im RAG-Service.

Empfohlene Modelle:
- `nomic-embed-text`
- `BAAI/bge-m3`
- `intfloat/multilingual-e5-large`

Betriebsmodi:
- CPU-Fallback
- GPU-Batch auf ai-gpu01 optional
- Modellversion wird als Metadatum gespeichert

## LLM-Strategie

### LLM Router
Aufgabe:
- Requests entgegennehmen
- passendes Backend auswählen
- einheitliche interne API anbieten

### Routing
- NVIDIA vorhanden -> `vllm`
- AMD vorhanden -> `ollama`
- CPU/Fallback -> `ollama`

### Modellklassen
- Chat/Analyse: Qwen2.5-7B, Mistral-7B, Gemma 3 4B
- Fast/Low-cost: 3B/4B Klassen
- Embeddings separat

## Audio-Strategie
- `audio-api` auf ai-gpu01
- `faster-whisper` für Transkription
- Speaker Enrollment/Identify mit Embeddings in Qdrant Collection `audio_speakers`
- optional `pyannote.audio` oder separater Diarize-Service

## Speicherlayout

### ai-gpu01
```text
/srv/ai-gpu/
  compose/
  env/
  models/
    vllm/
    ollama/
  cache/
    huggingface/
    whisper/
  audio/
    input/
    processed/
    speakers/
  logs/
  backups/
```

### ai-svc01
```text
/srv/foodlab/
  compose/
  env/
  data/
    inbox/
    staging/
    raw/
    parsed/
    chunks/
    ocr/
    mail/
    results/
    exports/
  postgres/
  qdrant/
  redis/
  n8n/
    data/
    files/
    flows/
  frontend/
  backups/
  openapi/
```

## Backup-Konzept

### Schichten
1. Proxmox-Snapshots vor Änderungen
2. Applikationskonsistente Sicherung
   - Postgres Dump/WAL
   - Qdrant Snapshots
   - n8n Daten + Flow-Export
3. Dateisystem-Backup
   - Rohdateien
   - OCR-Ausgaben
   - extrahierter Text
   - Chunks
   - Config und Compose-Dateien
4. Off-host Backup via `restic` oder `borg`

### Restore-Fälle
- nur Postgres
- nur Qdrant
- nur Dokumentenspeicher
- komplette Services-VM
- komplette GPU-VM

## Sicherheit
- TLS am Reverse Proxy
- Core API immer mit API-Key
- n8n UI mit Basic Auth
- Webhooks separat absichern
- interne Dienste ohne öffentliche Exposition
- Qdrant/Postgres/Redis nur internes Netz

## Monitoring/Healthchecks
- `/health` pro Service
- Docker Healthchecks
- Backup-Logs
- optional Prometheus/Loki/Grafana später

## Deployment-Reihenfolge

### GPU-VM
1. Docker + GPU Runtime
2. llm-router
3. vllm oder ollama
4. audio-api
5. Healthcheck

### Services-VM
1. Postgres
2. Redis
3. Qdrant
4. Parser/OCR/Mail-Ingest
5. Embedding-Service
6. RAG-Service
7. Core API
8. Worker
9. n8n
10. Frontend
11. Nginx
12. Backups/Timer

## Idempotentes Setup
- `.env` wird nicht ungefragt überschrieben
- Compose-Dateien werden deterministisch geschrieben
- Container werden neu gebaut/neu gestartet
- Daten werden nur mit `--full-reset` oder `--install-from-scratch` gelöscht
- Interaktive Fragen nur beim Erstlauf oder wenn Werte fehlen
