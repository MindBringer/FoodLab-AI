# worker Startfassung

Diese Startfassung verarbeitet Jobs aus Redis und schreibt Resultate nach Postgres.

## Aufgaben

- Jobs via `BLPOP` aus Redis lesen
- Status auf `processing` setzen
- Input aus Text oder Datei verarbeiten
- Ergebnis gegen `schema-registry` validieren
- Ergebnis durch `rule-engine` prüfen
- Status / Ergebnis nach Postgres schreiben
- DLQ bei wiederholtem Fehler

## Hinweis

Die Funktion `derive_structured_result()` ist bewusst als MVP gehalten.
Dort ersetzt du später die Heuristik durch:
- parser-service Response-Mapping
- llm-router Aufruf
- RAG-Integration
- task-spezifische Extraktion
