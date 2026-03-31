# core-api Startfassung

Diese Startfassung stellt die öffentliche Kern-API bereit und verdrahtet:

- Job-Anlage in Postgres
- Queue-Push nach Redis
- Datei-Upload oder Text-Submit
- Job-Status und Result-Abfrage

## Endpunkte

- `GET /health`
- `POST /api/v1/jobs/text`
- `POST /api/v1/jobs/submit`
- `GET /api/v1/jobs/{job_id}`
- `GET /api/v1/jobs/{job_id}/result`

## Erwartete Infrastruktur

- Postgres
- Redis
- Worker
- parser-service
- rag-service
- schema-registry
- rule-engine
