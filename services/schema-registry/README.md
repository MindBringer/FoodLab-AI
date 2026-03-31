# schema-registry

Leichtgewichtiger Service für versionierte JSON-Schemas und serverseitige Validierung.

## Verzeichnisstruktur

```text
schema-registry/
├── app.py
├── requirements.txt
├── Dockerfile
└── schemas/
    ├── common/
    └── tasks/
```

## Endpunkte

- `GET /health`
- `GET /schemas`
- `GET /schemas/{schema_name}`
- `GET /schemas/{schema_name}/{schema_version}`
- `POST /validate`

## Beispiel

```bash
curl -s http://localhost:8095/validate \
  -H 'Content-Type: application/json' \
  -d '{
    "schema_name": "tasks/document_analysis",
    "schema_version": "1.0.0",
    "payload": {
      "document_type": "contract",
      "findings": [],
      "warnings": []
    }
  }'
```
