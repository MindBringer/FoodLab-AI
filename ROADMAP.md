# Roadmap

## Phase 1 – Kern stabilisieren

- `foodlab-api` und `foodlab-worker` als feste Core-Dienste definieren
- Ergebnis-Envelope versionieren
- JSON-Schema / Pydantic-Validierung ergänzen
- Fehlercodes standardisieren
- Healthchecks und Readiness ergänzen
- Upload-Limits, Timeouts und Logging härten

## Phase 2 – Runtime entkoppeln

- Worker nicht mehr direkt gegen Ollama laufen lassen
- `llm-router` als einzige LLM-Zugriffsschicht etablieren
- Providerwahl und Fallbacks zentralisieren
- svc/gpu-Zielarchitektur als Standarddeployment festziehen

## Phase 3 – Dokumentdomäne ausbauen

- Parser für `eml` / `msg`
- HTML-zu-Text und Header-Extraktion
- XLSX-spezifische Tabellenlogik
- Dokumentklassifikation
- aufgabenspezifische Prompt- und Schemaschicht

## Phase 4 – Skalierung und Betrieb

- optionale Queue mit Redis
- mehrere Worker-Instanzen
- Observability
- Audit Trail
- Backup / Restore
- Mandantenfähigkeit

## Phase 5 – Interne Erweiterungen produktionsreif machen

- RAG mit belastbarer Embedding-Strategie
- Audio mit echter ASR / Diarization
- n8n als optionaler Workflow-Layer
- Frontend als Operations-UI
