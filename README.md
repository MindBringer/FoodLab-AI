# FoodLab

Modulare AI-, Dokumenten- und Retrieval-Plattform für lokale oder hybride Deployments.

FoodLab ist kein einzelner Fachprozess und keine einzelne Benutzeroberfläche, sondern die gemeinsame Verarbeitungs- und Wissensbasis für mehrere Eingangskanäle und Use Cases. Externe Systeme, Frontends und Automationen können auf denselben Core und dieselben internen Dienste aufsetzen, ohne Parsing, RAG, LLM-Anbindung, Audio oder Workflow-Logik jeweils neu erfinden zu müssen.

---

## Zielsetzung

FoodLab stellt einen belastbaren Kern für dokumenten-, text- und wissensgetriebene Fachprozesse bereit.

Der Fokus liegt auf:

- einer stabilen Core-API für externe und interne Einstiegspunkte
- einer gemeinsamen Basis für Parsing, OCR, RAG, Audio und LLM-Nutzung
- einer klaren Trennung zwischen Einstiegskanälen, Produktkern und AI-Runtime
- normierten, versionierten JSON-Ergebnissen statt freier Modellantworten
- einfacher Sicherung, Wiederherstellung und Wartung
- hohem Sicherheitsniveau bei lokaler oder hybrider Betriebsform
- horizontaler Skalierbarkeit ohne Architekturbruch

FoodLab ist damit die einheitliche Plattform unter mehreren Nutzungsszenarien, nicht die UI oder Prozesslogik eines einzelnen Anwendungsfalls.

---

## Leitbild

FoodLab bündelt gemeinsame AI- und Dokumentfunktionen zentral und stellt sie über stabile Schnittstellen bereit.

Das bedeutet:

- Power Automate kann Dokumente oder Texte einreichen und strukturierte Ergebnisse erhalten.
- Ein Ticketsystem kann dieselbe Plattform für Klassifikation, Analyse und Wissensaufbau nutzen.
- Ein Frontend kann direkte Chat-, Agenten- oder Recherchefunktionen auf denselben Core und dieselben Wissensdienste aufsetzen.
- Weitere Eingänge wie Webhooks, Watch-Folder, Mail-Ingest oder Fachanwendungen können anschließen, ohne die darunterliegende Plattform zu duplizieren.

---

## Mehrere Eingangskanäle / Startpfade

FoodLab unterstützt bewusst mehrere gleichwertige Einstiegspfade.

### 1. Prozesssysteme und Automatisierung

Beispiele:

- Power Automate
- M365-nahe Workflows
- n8n
- Webhooks
- Batch- oder File-Drop-Prozesse

Typischer Modus:

- Text oder Datei wird eingereicht
- FoodLab analysiert
- Ergebnis wird als kontrolliertes JSON zurückgegeben
- Folgeprozesse arbeiten mit stabilen Strukturen statt mit Freitext

### 2. Fachanwendungen / Use-Case-spezifische Oberflächen

Beispiele:

- Ticketsystem
- Power App
- interne Formulare
- domänenspezifische Oberflächen

Diese Systeme liefern Kontext, Pflichtfelder, UX und Prozesslogik, verwenden aber dieselbe Verarbeitungsbasis darunter.

### 3. Direktes Frontend / Chat / Agenten

FoodLab kann zusätzlich eine direkte Benutzeroberfläche für:

- Chat mit LLM
- agentische Assistenz
- semantische Recherche über RAG
- Debugging / Operations
- manuelle Uploads und Analysen

bereitstellen.

Das Frontend ist damit kein Widerspruch zum API-zentrierten Kern, sondern ein weiterer kontrollierter Zugriffspfad auf dieselbe Plattform.

### 4. Interne oder technische Ingestion-Pfade

Beispiele:

- Watch-Folder
- Mail-Ingest
- SharePoint-Exporte
- geplante Synchronisationen
- systeminterne Jobs

Auch diese Pfade sollen dieselben Parsing-, Normalisierungs- und Wissensdienste verwenden.

---

## Architekturprinzipien

### 1. Shared Platform statt Einzellösungen

Parsing, OCR, Embeddings, Retrieval, LLM-Routing, Audio und Workflow-Bausteine werden zentral bereitgestellt und von mehreren Einstiegskanälen gemeinsam genutzt.

### 2. Core first

Die Core-API ist der offizielle und stabile Einstiegspunkt für externe Integrationen. Interne Hilfsdienste bleiben austauschbar und sind nicht Teil des externen Produktvertrags.

### 3. Internal by default

RAG, Parsing, Embedding, LLM-Backend, Audio, Queue, Datenbanken und Hilfsdienste sind standardmäßig intern. Exponiert wird nur, was fachlich und sicherheitstechnisch nötig ist.

### 4. Joborientierte Verarbeitung

FoodLab verarbeitet Texte, Dateien und künftig weitere Eingaben bewusst jobbasiert. Das erhöht Robustheit, Nachvollziehbarkeit, Retry-Fähigkeit und Skalierbarkeit.

### 5. Regeln plus LLM

Regelbasierte Vorprüfung, Extraktion und Normalisierung bleiben Pflicht. LLMs ergänzen die Fachlogik, ersetzen sie aber nicht.

### 6. JSON als Produktvertrag

Das Ergebnisformat ist serverseitig kontrolliert, validiert und versioniert. Maßgeblich ist nicht, was das Modell „ungefähr“ ausgibt, sondern was die Plattform als belastbares API-Ergebnis garantiert.

### 7. Zentrale Wissensbasis

Retrieval und semantische Suche sind keine Einzelfunktion eines Use Cases, sondern eine gemeinsame Plattformfähigkeit. Mehrere Systeme können auf denselben Wissensbestand aufsetzen.

---

## Architekturebenen

### 1. Entry / Experience Layer

Diese Schicht bildet alle Einstiegspunkte und Benutzerkontakte ab.

Beispiele:

- Power Automate
- Ticketsystem / Power App
- Frontend / Chat / Agenten
- n8n-Workflows
- Webhooks
- Watch-Folder / Mail-Ingest
- weitere Fachanwendungen

Verantwortung:

- Benutzerführung
- fachlicher Kontext
- Trigger und Orchestrierung
- Übergabe strukturierter Eingaben an den Core

### 2. Integration Layer

Verantwortung:

- Annahme externer Requests
- API-Key- oder Token-basierte Authentifizierung
- OpenAPI / Schnittstellenvertrag
- synchrone oder asynchrone Job-Einreichung
- Status- und Ergebnisabholung

Dienst:

- `foodlab-api`

### 3. Core Processing Layer

Verantwortung:

- Jobverwaltung
- Dateiregistrierung
- Orchestrierung
- Status und Fortschritt
- Ergebnisaggregation
- fachliche und technische Normalisierung
- Übergang zwischen Eingabekanälen und internen Diensten

Dienste:

- `foodlab-worker`
- `postgres`
- Dateispeicher
- optional Queue

### 4. Ingestion / Extraction Layer

Verantwortung:

- Entgegennahme und Extraktion von Texten und Dokumenten
- Parsing nach Dateityp
- OCR bei gescannten Dokumenten
- E-Mail- und Attachment-Verarbeitung
- domänenspezifische Vorverarbeitung

Dienste:

- `parser-service`
- `tika`
- `ocr-service`
- `mail-ingest-service`
- Regex- und Regelmodule

### 5. Knowledge / Retrieval Layer

Verantwortung:

- Dokumentnormalisierung
- Chunking
- Embeddings
- Indexierung
- semantische Suche
- zitierfähige Retrieval-Ergebnisse
- zentrale Wissenshaltung für mehrere Consumer

Dienste:

- `embedding-service`
- `rag-service`
- `qdrant`

### 6. AI Runtime Layer

Verantwortung:

- einheitliche interne Modellansteuerung
- Backend-Routing
- Providerwahl und Fallbacks
- hardwareabhängige Ausführung

Dienste:

- `llm-router`
- `vllm`
- `ollama`

### 7. Audio Layer

Verantwortung:

- Transkription
- Speaker Enrollment / Identify
- optionale Diarization
- Audio-Metadaten

Dienste:

- `audio-api`
- optional separater Diarization-Service

### 8. Workflow / Operations Layer

Verantwortung:

- Automatisierung
- technische und operative Workflows
- internes UI / BFF
- Monitoring-nahe Hilfsfunktionen

Dienste:

- `n8n`
- `frontend`
- optional Reverse Proxy / Nginx

---

## Gesamtbild

```text
Power Automate / Ticketsystem / Frontend / Webhooks / Watch-Folder / weitere Clients
                                     |
                                     v
                               foodlab-api
                                     |
                     +---------------+----------------+
                     |                                |
                     v                                v
                Postgres / Queue                 foodlab-worker
                                                         |
                +--------------------+-------------------+-------------------+
                |                    |                   |                   |
                v                    v                   v                   v
          Parsing / OCR        Regex / Fachlogik   Knowledge / RAG      LLM-Aufruf
                |                                      |                   |
                v                                      v                   v
        parser / tika / OCR                  embedding / qdrant      llm-router
                                                                            |
                                           +--------------------------------+-------------------+
                                           |                                                    |
                                           v                                                    v
                                         vLLM                                                 Ollama
                                       (NVIDIA)                                       (CPU/AMD/Fallback)
```

---

## Rollenmodell

### Service Node (`svc`)

Der Service Node enthält die produktnahe Plattformlogik und die meisten persistierenden Kernkomponenten.

Typische Dienste:

- `foodlab-api`
- `foodlab-worker`
- `postgres`
- `redis` optional bzw. perspektivisch Standard für Queueing
- `parser-service`
- `tika`
- `ocr-service`
- `mail-ingest-service`
- `embedding-service`
- `rag-service`
- `qdrant`
- `n8n`
- `frontend`
- `nginx`

### GPU Node (`gpu`)

Der GPU Node kapselt runtime-nahe AI-Dienste und spezialisierte Beschleunigung.

Typische Dienste:

- `llm-router`
- `vllm`
- `ollama`
- `audio-api`
- optional Diarization-Service

### Gemeinsames Netz

Die Knoten kommunizieren über dedizierte interne Netzsegmente. Extern sichtbar ist nur die definierte Zugriffsschicht, nicht die darunterliegenden Hilfsdienste oder Modellserver.

---

## Core vs. Shared Internals vs. Use Cases

### Core

Alles, was für den stabilen Produktkern zwingend erforderlich ist:

- `foodlab-api`
- `foodlab-worker`
- `postgres`
- Dateispeicher
- definierte interne Anbindung an Parsing- und LLM-Schicht

### Shared Internal Services

Gemeinsame Fähigkeiten, die von mehreren Use Cases genutzt werden:

- Parsing
- OCR
- Mail-Ingest
- Embeddings
- RAG / Qdrant
- Audio
- Queue
- n8n
- Frontend / BFF
- Reverse Proxy
- Monitoring / Audit / Backups

### Use Cases / Consumer

Aufsetzende Systeme, die FoodLab nutzen, aber nicht der Plattformkern selbst sind:

- Power-Automate-Integration
- Ticketsystem
- direkte Chat-/Agenten-Oberfläche
- interne Recherche- oder Wissensoberflächen
- weitere Fachprozesse

Diese Trennung verhindert, dass jeder neue Anwendungsfall eigene Parsing-, LLM- oder RAG-Infrastruktur mitbringt.

---

## FoodLab-Kern

Der FoodLab-Kern ist eine joborientierte Eingangs- und Verarbeitungsplattform für Texte, Dateien und künftig weitere Eingangstypen.

### Aufgaben des Kerns

- Annahme von Texten, Dateien und Metadaten
- persistente Ablage der Eingänge
- Erstellung und Verwaltung von Jobs
- Aufruf interner Parsing- und Ingestion-Dienste
- fachliche Vorverarbeitung per Regeln / Regex
- Prompt-Aufbau und Modellorchestrierung
- Nutzung von Retrieval, wenn fachlich sinnvoll
- Normalisierung und Aggregation der Ergebnisse
- Bereitstellung stabiler JSON-Ergebnisse
- Nachvollziehbarkeit über Jobstatus, Resultate und Fehler

### Warum jobbasiert

Das Jobmodell ist bewusst gewählt, weil es robuster ist als reine Completion-Endpunkte:

- große Dateien können asynchron verarbeitet werden
- Clients müssen keine langen HTTP-Requests offenhalten
- Retries und Leasing sind sauber abbildbar
- Teilresultate und Fehler bleiben nachvollziehbar
- mehrstufige Pipelines werden möglich
- mehrere Einstiegspfade können dieselbe Abarbeitungslogik nutzen

---

## API-Konzept

Die Core-API ist die offizielle Integrationsfläche für externe Systeme und aufsetzende Anwendungen.

### Leitprinzipien

- keine direkte Anbindung externer Systeme an Modellserver
- keine direkte Exponierung von Qdrant, Embedding, Parsing oder Audio
- Authentifizierung über API-Key, später ausbaubar auf feinere Token-/Rollenmodelle
- JSON-first
- OpenAPI als stabiler Vertragsbestandteil
- klare Trennung zwischen offiziellen und internen Endpunkten

### Offizielle Kern-Endpunkte

- `GET /health`
- `POST /api/v1/jobs/text`
- `POST /api/v1/jobs/submit`
- `GET /api/v1/jobs/{job_id}`
- `GET /api/v1/jobs/{job_id}/result`

### Interne Dienste

Beispiele für interne Endpunkte bzw. interne Serviceverträge:

- Parsing
- OCR
- Mail-Ingest
- Embeddings
- RAG Index / Query
- interne LLM-Calls
- Audio-Funktionen

Diese sind nicht Teil des externen Vertrags und sollen nur kontrolliert intern erreichbar sein.

---

## Sync- und Async-Modus

### Synchron

Für kleine oder schnelle Eingaben kann der Client auf Abschluss warten.

Geeignet für:

- kurze Texte
- kleine Dokumente
- einfache Klassifikation oder Extraktion
- direkte Frontend- oder Flow-Schritte mit kurzer Laufzeit

### Asynchron

Für größere oder langsamere Jobs wird ein Job erzeugt und später abgefragt.

Geeignet für:

- PDFs
- Office-Dokumente
- E-Mails mit Anhängen
- Retrieval- oder Agentenketten
- komplexere Analysen
- Batch- oder Workflow-Verarbeitung

---

## Gemeinsame Wissensbasis / RAG

RAG ist keine Insellösung eines einzelnen Features, sondern eine zentrale Plattformfähigkeit.

### Zielbild

- zentrale Vektorhaltung
- zentrale Chunk- und Metadatenlogik
- mehrere Datenquellen
- mehrere Abfragepfade
- einheitliche Embedding-Strategie
- Wiederverwendung desselben Wissensbestands durch verschiedene Einstiegskanäle

### Typische Quellen

- verarbeitete Dokumente
- SharePoint-basierte Wissensbestände
- Support-Dokumentation
- hochgeladene Referenzdokumente
- strukturierte oder halbstrukturierte Fachunterlagen

### Typische Consumer

- Chat / Agenten
- interne Recherche
- Ticketsystem
- Automationen
- analytische oder dokumentbezogene Assistenzfunktionen

### Grundregel

Qdrant bzw. der Retrieval-Bestand ist in der Regel ein sekundärer Such- und Arbeitsindex. Führende Primärsysteme für Stammdaten, Geschäftsobjekte oder revisionsrelevante Dokumentation bleiben fachlich getrennt.

---

## Frontend / Chat / Agenten

FoodLab kann neben der API eine direkte Oberfläche bereitstellen.

### Mögliche Rollen des Frontends

- manuelle Dokumentanalyse
- semantische Recherche
- Chat mit LLM
- Agentenfunktionen
- Operations- und Debugging-UI
- kontrollierter Zugriff auf interne Shared Services

### Architekturelle Einordnung

Das Frontend ist kein Ersatz für den Core und auch kein Sonderweg. Es ist ein weiterer Einstiegskanal, der dieselben Kern- und Wissensdienste nutzt.

Damit bleibt Folgendes erhalten:

- direkte Benutzerinteraktion
- schnelle Validierung neuer Fähigkeiten
- einheitliche Backend-Basis
- keine doppelte Logik neben Power Automate oder Ticketsystem

---

## Beispielhafte Use Cases

### 1. Power-Automate-Analyse

```text
Power Automate -> Core API -> Job -> Parsing / Regeln / LLM -> JSON-Ergebnis zurück an Power Automate
```

### 2. Ticketsystem

```text
Power App / Ticketsystem -> Core API -> Analyse -> Ergebnis -> Dokumentation / Wissensaufbau / Nachverfolgung
```

### 3. Chat / Agent

```text
Frontend -> BFF / Core / RAG -> LLM Router -> Antwort mit optionalem Retrieval-Kontext
```

### 4. Wissensindizierung

```text
Dokumentquelle / Upload / Sync -> Parsing -> Chunking -> Embedding -> Qdrant
```

Diese Abläufe nutzen dieselbe Plattformbasis, unterscheiden sich aber im Einstiegspunkt und in der Prozesslogik.

---

## Daten- und Ingestion-Modell

### Quellen

- Text
- Datei-Uploads
- E-Mail
- SharePoint-Exporte
- Webhooks
- Watch-Folder
- Audio
- manuelle Eingaben über Frontend

### Normalisiertes Zwischenformat

Ziel ist eine interne Normalisierung, damit nachgelagerte Dienste nicht für jeden Eingangskanal neu implementiert werden müssen.

Enthalten sein sollen unter anderem:

- Dokument-ID
- Quelle und Eingangskanal
- Dateityp / Source Type
- Titel / Name
- Sprache
- Abschnitte / Seiten / Anhänge
- Metadaten
- Sicherheitslabel
- Referenzen auf Primärsysteme

### Dateitypen

Bereits bzw. perspektivisch relevant:

- `txt`
- `md`
- `csv`
- `json`
- `pdf`
- `docx`
- `xlsx`
- `pptx`
- `eml`
- `msg`
- Bilder für OCR
- Audio

---

## Normiertes JSON

Der Zielzustand ist ein serverseitig validiertes, versioniertes und stabil nutzbares Ergebnisformat.

### Zielprinzipien

- feste Top-Level-Struktur
- Schema-Version
- Trennung von Fachdaten und technischen Metadaten
- strukturierte Fehlerliste
- konsistente Felder über mehrere Einstiegskanäle hinweg
- Erweiterbarkeit ohne Vertragsbruch

### Beispiel

```json
{
  "success": true,
  "schema_version": "1.0",
  "job_id": "...",
  "status": "done",
  "data": {
    "document_type": "lab_report",
    "sample_type": null,
    "product_name": null,
    "findings": [],
    "warnings": []
  },
  "meta": {
    "provider": "vllm",
    "model": "Qwen/Qwen2.5-7B-Instruct",
    "processing_ms": 0,
    "entry_channel": "power_automate"
  },
  "errors": []
}
```

Langfristig sollen Fachschemas je Task oder Dokumentklasse auswählbar und serverseitig hart validierbar sein.

---

## Sicherheit

FoodLab ist auf hohe Sicherheit bei lokaler oder hybrider Betriebsform ausgelegt.

### Mindeststandard

- nur definierte externe Eintrittspunkte
- API-Key oder Token an der Core-API
- keine direkte Exponierung interner Hilfsdienste
- Trennung interner und externer Netze
- kontrollierte Upload-Limits
- klare Fehlerantworten
- reproduzierbare Datenhaltung

### Zielausbau

- Reverse Proxy als definierte Eintrittsschicht
- TLS am Edge und bei Bedarf intern
- feingranulare Rollen / Tokens / Service-Identitäten
- Tenant- oder Bereichstrennung bei Bedarf
- Audit-Logging
- sichere Secret-Verwaltung
- restriktive Standard-Exposition
- Hardening der internen Servicekommunikation

### Sicherheitsgrundsatz

Kein Consumer darf interne Systemdetails oder Modellserver direkt kennen müssen. Sicherheit und Austauschbarkeit hängen direkt zusammen.

---

## Backup, Restore und Wartung

FoodLab soll einfach zu sichern, reproduzierbar wiederherzustellen und mit geringer Betriebsvarianz wartbar sein.

### Sicherungsebenen

- VM- oder Host-Snapshots vor größeren Änderungen
- applikationskonsistente Sicherung von Postgres
- Qdrant-Snapshots
- Sicherung von Rohdateien, OCR-Ergebnissen, extrahiertem Text, Chunks und Resultaten
- Sicherung von Konfiguration, Compose-Dateien und OpenAPI-Artefakten
- Off-host-Backup

### Restore-Fälle

- nur Datenbank
- nur Wissensindex
- nur Dateispeicher
- kompletter Service-Node
- kompletter GPU-Node
- vollständige Wiederherstellung der Plattform

### Wartungsprinzipien

- idempotentes Setup
- deterministische Deployments
- `.env` nicht ungefragt überschreiben
- Daten nur bei explizitem Reset löschen
- möglichst geringe Zahl konkurrierender Betriebsmodi
- klare Upgrade- und Migrationspfade

---

## Skalierung

FoodLab ist technisch auf horizontale und funktionale Skalierung ausgelegt.

### Skalierungsachsen

- mehrere Worker-Instanzen
- Queue-basierte Entkopplung
- separater GPU-Node
- mehrere GPU-Nodes perspektivisch
- zentrale LLM-Zugriffsschicht
- zentrale RAG-Datenhaltung
- getrennte Skalierung von API, Worker, Retrieval und Runtime

### Warum das trägt

Mehrere Einstiegspfade nutzen denselben Unterbau. Dadurch steigt die Zahl der Use Cases, ohne dass jede neue Lösung eigene Infrastruktur für Parsing, Wissen und Modellzugriff aufbauen muss.

---

## Observability und Betrieb

FoodLab soll mittelfristig produktionsreif observierbar werden.

### Zielbestandteile

- `/health` pro Dienst
- Readiness-Probes
- zentrales Logging
- Metriken
- Tracing
- Audit-Trail
- Backup-Logs
- Betriebs-Dashboards

Diese Fähigkeiten sind kein Nebenthema, sondern Teil der Produktreife.

---

## Verhältnis zu aufsetzenden Systemen

### Power Automate

Power Automate ist ein wichtiger, aber nicht exklusiver Consumer. Es nutzt die Core-API, nicht die internen Modell- oder Retrieval-Dienste direkt.

### Ticketsystem

Das Ticketsystem ist ein Use Case auf Basis derselben Plattform. Es bringt Fachprozess, UX, Pflichtfelder, Nachverfolgung und Dokumentation mit, ersetzt aber nicht FoodLab als gemeinsame Verarbeitungsbasis.

### Frontend / Chat / Agent

Das Frontend ist ein weiterer Consumer derselben Plattform und bleibt ausdrücklich möglich.

---

## Repository-Struktur (Sollbild)

```text
.
├── README.md
├── docs/
│   ├── ARCHITEKTUR.md
│   ├── POWER-AUTOMATE-INTEGRATION.md
│   ├── ROADMAP.md
│   └── USE-CASES.md
├── compose/
│   ├── docker-compose.svc.yml
│   └── docker-compose.ai.yml
├── services/
│   ├── foodlab-api/
│   ├── foodlab-worker/
│   ├── parser-service/
│   ├── ocr-service/
│   ├── mail-ingest-service/
│   ├── embedding-service/
│   ├── rag-service/
│   ├── llm-router/
│   ├── audio-api/
│   └── frontend/
└── scripts/
    ├── setup-stack-v3-apps.sh
    └── foodlab_install.sh
```

---

## Prioritäten für die nächste Konsolidierungsstufe

### 1. Core härten

- Ergebnis-Envelope versionieren
- Pydantic-/JSON-Schema-Validierung erzwingen
- Fehlercodes standardisieren
- Healthchecks und Readiness vervollständigen
- Upload-Limits, Timeouts und Logging härten

### 2. Runtime konsequent entkoppeln

- Worker ausschließlich über `llm-router`
- Providerwahl und Fallbacks zentral
- svc/gpu-Zielarchitektur als Standard

### 3. Ingestion- und Dokumentdomäne ausbauen

- spezialisierte Parser für `eml` / `msg`
- HTML-/Plaintext-Trennung
- Header-Extraktion
- XLSX- und domänenspezifische Parser
- Dokumentklassifikation
- task- und dokumentspezifische Schemas

### 4. Shared Knowledge sauber operationalisieren

- Embedding-Service als Standard
- zentrale Chunk-/Metadatenregeln
- Primärsysteme vs. Retrieval-System klar trennen
- Indizierung aus mehreren Quellen sauber definieren

### 5. Betrieb produktionsreif machen

- Queue
- horizontale Worker-Skalierung
- Audit-Trail
- Observability
- Backup- und Restore-Prozeduren
- Rollen- und Sicherheitsmodell

---

## Statusbewertung

FoodLab ist nicht nur Infrastruktur und nicht nur ein einzelner Fachprozess. Es ist als gemeinsame Plattformbasis für mehrere Eingangskanäle und Use Cases erkennbar.

Der nächste Reifegrad besteht darin,

- die Mehrkanal-Architektur explizit durchzuziehen,
- die gemeinsamen Shared Services verbindlich zu machen,
- den Core-Vertrag zu härten,
- die zentrale Wissenshaltung auszubauen
- und den Betrieb auf Sicherheit, Wartbarkeit und Skalierung zu standardisieren.

---

## Zielarchitektur in einem Satz

FoodLab ist eine joborientierte Core-Plattform für strukturierte Dokument-, Text-, Wissens- und AI-Verarbeitung, die mehrere Einstiegskanäle auf einer gemeinsamen sicheren und wartbaren Basis zusammenführt und ihre internen AI- und Retrieval-Dienste flexibel austauschbar betreibt.
