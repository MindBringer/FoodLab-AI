# Power-Automate-Integration

## Ziel

Power Automate soll den FoodLab-Kern sicher und stabil nutzen können, ohne Details der internen AI-Runtime kennen zu müssen. Der Integrationspunkt ist ausschließlich die Core-API.

---

## Zielpfad

```text
Power Automate -> On-Premises Data Gateway -> foodlab-api
```

Nicht vorgesehen:

- direkter Zugriff auf `llm-router`
- direkter Zugriff auf `vllm` oder `ollama`
- direkter Zugriff auf `rag`, `audio` oder `frontend`

---

## Geeignete Kern-Endpunkte

### Health

`GET /health`

Verwendung:

- Konnektivität prüfen
- Monitoring / einfache Vorprüfung im Flow

### Textjob

`POST /api/v1/jobs/text`

Geeignet für:

- Mail-Bodies
- Plaintext-Inhalte
- aus Flows zusammengesetzte Texte

### Datei-Job

`POST /api/v1/jobs/submit`

Geeignet für:

- einzelne Dateien
- mehrere Dateien pro Job
- binäre Uploads inklusive `xlsx`, `pdf`, `txt` und weiterer Dokumentformate

### Jobstatus

`GET /api/v1/jobs/{job_id}`

Geeignet für:

- Polling
- technische Fortschrittsanzeige
- Debugging

### Jobresultat

`GET /api/v1/jobs/{job_id}/result`

Geeignet für:

- schlanke Ergebnisabholung
- Weiterverarbeitung im Flow

---

## Empfohlene Betriebsmodi

### 1. Synchron für kleine Eingaben

Für kurze Texte oder kleine Dokumente:

- Request mit `wait=true`
- Ergebnis direkt im selben Flow-Schritt verarbeiten

Geeignet für:

- kurze E-Mail-Bodies
- kleine Textdateien
- einfache Klassifikation oder Extraktion

### 2. Asynchron für größere oder langsamere Jobs

Für größere Uploads:

- Job einreichen
- `job_id` speichern
- per Polling den Status prüfen
- Ergebnis in separatem Schritt abholen

Geeignet für:

- `xlsx`
- größere Dokumente
- mehrteilige Uploads
- längere Modelllaufzeiten

---

## Empfohlenes Request-Modell

### Textfall

Power Automate sendet ein JSON mit:

- `text`
- `prompt`
- `source_name`
- `correlation_id`
- optional `wait`
- optional `timeout_seconds`

### Dateifall

Power Automate sendet multipart/form-data mit:

- `files`
- `prompt`
- `correlation_id`
- optional `wait`
- optional `timeout_seconds`

---

## Empfohlenes Antwortmodell

### Kurzfristig

Das aktuelle Referenzmodell liefert:

- `job_id`
- `status`
- `correlation_id`
- `submitted_files`
- `result`
- `error`

### Zielzustand

Für produktive Flows sollte das Ergebnis vereinheitlicht werden:

```json
{
  "success": true,
  "schema_version": "1.0",
  "job_id": "...",
  "status": "done",
  "data": {
    "document_type": "string|null",
    "findings": [],
    "warnings": []
  },
  "meta": {
    "provider": "string",
    "model": "string",
    "processing_ms": 0
  },
  "errors": []
}
```

---

## Authentifizierung

### Aktueller Ansatz

- Header: `X-API-Key`
- alternativ Query-Parameter möglich, aber nicht bevorzugt

### Empfehlung

Im Flow immer den Header verwenden und Secrets nur in geschützten Verbindungsdefinitionen bzw. Gateway-/Connector-Einstellungen halten.

---

## Typische Flow-Muster

### Muster A: Mail-Body analysieren

1. Eingangsmail erhalten
2. Body extrahieren
3. `POST /api/v1/jobs/text`
4. normiertes JSON in weitere Schritte übernehmen

### Muster B: Anhang analysieren

1. Mail mit Anhang erhalten
2. Dateiinhalt lesen
3. `POST /api/v1/jobs/submit`
4. bei `wait=false`: `job_id` speichern
5. per `GET /api/v1/jobs/{job_id}/result` abholen

### Muster C: Mehrere Dokumente pro Vorgang

1. relevante Dateien sammeln
2. gemeinsam als ein Job einreichen
3. aggregiertes Resultat im Folgeprozess nutzen

---

## Wichtigste Designregeln für stabile Flows

- keine direkte Abhängigkeit vom Modellformat
- keine Verarbeitung freier LLM-Texte im Flow
- immer mit serverseitig normiertem JSON arbeiten
- asynchron arbeiten, sobald Dateigröße oder Laufzeit unsicher ist
- `correlation_id` aus dem Quellprozess mitführen

---

## Noch offene Punkte für produktiven Einsatz

- versioniertes API-Schema
- serverseitige harte JSON-Validierung
- domänenspezifische Felddefinitionen
- saubere Fehlercodes für Fach- und Technikfehler
- Connector-freundliche Response-Typen ohne wechselnde Form
- spezialisierte E-Mail- und XLSX-Parser für höhere Extraktionsqualität
