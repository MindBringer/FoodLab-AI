# Architektur

## Architekturprinzip

FoodLab trennt Fachlogik, Integrationsschnittstellen und AI-Runtime bewusst voneinander. Die Architektur ist darauf ausgelegt, dass externe Systeme nur mit einer stabilen Core-API sprechen, während Modellserver, RAG, Audio und weitere Spezialdienste intern austauschbar bleiben.

---

## Architekturschichten

### 1. Integration Layer

Verantwortung:

- Entgegennahme externer Requests
- API-Key-Authentifizierung
- OpenAPI / Connector-Vertrag
- synchrone oder asynchrone Job-Einreichung

Dienst:

- `foodlab-api`

### 2. Core Processing Layer

Verantwortung:

- Jobverwaltung
- Dateiregistrierung
- Worker-Orchestrierung
- Ergebnisaggregation
- technische und fachliche Normalisierung

Dienste:

- `foodlab-worker`
- `postgres`
- Dateispeicher

### 3. Extraction Layer

Verantwortung:

- Textentnahme aus Uploads
- generische Office-/Dokument-Extraktion
- vorbereitende Regelanalyse

Dienste:

- `tika`
- Regex-/Regelmodule im Worker

### 4. AI Runtime Layer

Verantwortung:

- einheitliche Modellansteuerung
- Routing zwischen Backends
- Hardware-spezifische Ausführung

Dienste:

- `llm-router`
- `vllm`
- `ollama`

### 5. Extension Layer

Verantwortung:

- Retrieval
- Audio
- Workflow-Automatisierung
- internes UI / BFF

Dienste:

- `qdrant`
- `rag`
- `audio-api`
- `n8n`
- `frontend`

---

## Knotenmodell

### Service Node

Der Service Node enthält alle komponenten, die aus fachlicher Sicht das Produkt definieren:

- `foodlab-api`
- `foodlab-worker`
- `postgres`
- `tika`
- `qdrant` optional
- `rag` optional
- `n8n` optional
- `frontend` optional

### GPU Node

Der GPU Node bündelt AI-Runtime und modellnahe Spezialdienste:

- `llm-router`
- `vllm`
- `ollama`
- `audio-api`

### Gemeinsames Netz

Beide Knoten sind über ein dediziertes Bridge-Netz miteinander verbunden. Die Service-Seite sieht nur die abstrakte LLM-Schnittstelle, nicht die intern gewählte Inferenz-Engine.

---

## Request-Fluss

### Extern

```text
Client -> foodlab-api -> Postgres / File Storage -> foodlab-worker
```

### Intern

```text
foodlab-worker -> Tika -> Regex / Vorlogik -> llm-router -> vLLM oder Ollama
```

### Optional intern

```text
frontend -> BFF -> API / RAG / Audio / n8n
```

---

## Kern-Entscheidungen

### 1. Kein direkter Zugriff auf Modellserver

Externe Clients greifen nie direkt auf `llm-router`, `vllm` oder `ollama` zu. Dadurch bleibt die Fachschnittstelle stabil, obwohl sich die AI-Runtime ändern darf.

### 2. Joborientierte Verarbeitung

Statt eines reinen Completion-Endpunkts verwendet FoodLab ein Jobmodell. Das ist für große Dateien, Zeitlimits, Retries und Nachvollziehbarkeit robuster.

### 3. Kombination aus Regeln und LLM

Regex- und Vorlogik liefern erste strukturierte Hinweise. Das Modell ergänzt und konsolidiert. Dadurch sinkt das Risiko freier Halluzinationen und die Nachbearbeitung wird einfacher.

### 4. Core und Extensions getrennt

RAG, Audio, UI und Workflow-Automatisierung sind wertvoll, aber nicht Teil des zwingenden Produktkerns. Diese Trennung reduziert Komplexität im externen Vertrag.

---

## Datenhaltung

### Persistente Kernobjekte

- Jobs
- Job-Dateien
- extrahierte Texte
- Teilresultate
- Finalresultate
- Fehlerzustände

### Storage-Orte

- Inbox für Uploads
- Results für Ergebnisartefakte
- Postgres für Status und strukturierte Metadaten
- optional Qdrant für Retrieval- und Audio-Vektoren

---

## Sicherheitsmodell

### Mindeststandard

- API-Key für externe Core-Requests
- keine Exponierung interner Hilfsdienste
- Trennung intern / extern auf Netzwerkebene
- kontrollierte Upload-Größen
- klare Fehlerantworten

### Ausbau

- Reverse Proxy
- TLS intern oder am Edge
- Mandantenfähigkeit
- feingranulare Rollen / Tokens
- Audit-Logging

---

## Technische Schulden / offene Architekturpunkte

### Noch zu konsolidieren

- Referenzimplementierung nutzt lokal direkt Ollama; Zielarchitektur soll über `llm-router` gehen.
- Podman-Referenz und Docker-Compose-Zielbild müssen zusammengeführt werden.
- Ergebnisformat ist strukturiert, aber noch nicht als hartes API-Schema versioniert.
- E-Mail-spezifische Fachparser fehlen noch.
- Healthchecks, Readiness und Observability fehlen in produktionsreifer Form.

---

## Zielarchitektur in einem Satz

FoodLab ist eine joborientierte Core-Plattform für strukturierte Dokument- und Texteingänge, die ihre Fachschnittstelle stabil hält und ihre AI-Runtime intern flexibel austauschbar betreibt.
