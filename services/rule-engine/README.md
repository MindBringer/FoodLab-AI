# rule-engine

Leichtgewichtiger Service für regelbasierte Validierung und Warnungen über strukturierten Ergebnissen.

## Endpunkte

- `GET /health`
- `GET /rules`
- `POST /evaluate`

## Beispiel

```bash
curl -s http://localhost:8096/evaluate \
  -H 'Content-Type: application/json' \
  -d '{
    "rule_set": "document_analysis_v1",
    "payload": {
      "document_type": "lab_report",
      "findings": [
        {"parameter": "Blei", "value": 0.15, "unit": "mg/kg"}
      ]
    }
  }'
```
