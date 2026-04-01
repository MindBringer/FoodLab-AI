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

## Installation (from scratch)

### 1. Repo klonen

cd /opt
sudo git clone https://github.com/MindBringer/FoodLab-AI.git
sudo chown -R $USER:$USER /opt/FoodLab-AI

### 2. Base installieren

cd /opt/FoodLab-AI
sudo bash install-base.sh

Installiert:

- Docker
- Git
- Tools

### 3. Bootstrap

cd /opt/FoodLab-AI
bash bootstrap-foodlab.s

- legt /srv/foodlab bzw. /srv/ai-gpu an
- erstellt .env

### 4. Stack starten

Service-Node:
bash setup-stack.sh svc

GPU-Node:
bash setup-stack.sh gpu

### 5. Konfiguration
.env:
LLM_ROUTER_URL=http://<IP GPU-Node>:8091
QDRANT_URL=http://<IP SVC-Node>:6333
REDIS_URL=redis://<IP SVC-Node>:6379/0

Wichtig: Cross-Host immer über IP, nicht Service-Name

## Mehrere Eingangskanäle / Startpfade

FoodLab unterstützt bewusst mehrere gleichwertige Einstiegspfade.

### 1. Prozesssysteme und Automatisierung

Features:

- strukturierte Extraktion via LLM
- Hybrid-Logik (Heuristik + LLM)
- Schema-Validierung
- parameterbasierte Rule-Engine
- RAG vorbereitet
- Queue-basierte Verarbeitung

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

## Dokumentquellen, DMS und Knowledge Layer

FoodLab ist kein Dokumentenmanagementsystem und kein führendes Ablagesystem.

Führende Primärsysteme bleiben je nach Einsatzfall insbesondere:

- SharePoint
- Nextcloud
- Fileserver
- E-Mail-Systeme
- weitere Fachsysteme mit dokumentbezogenen Anhängen oder Exporten

Diese Systeme bleiben verantwortlich für:

- Ablage
- Versionierung
- Berechtigungen
- Lebenszyklus
- Revision / Audit
- Lösch- und Aufbewahrungsregeln

FoodLab ergänzt diese Systeme um:

- Parsing und OCR
- strukturierte Extraktion
- Dokumentklassifikation
- Tagging
- semantische Indizierung
- Similar Documents
- kontextbasierte Q&A
- workflowfähige, strukturierte Ergebnisse

Der Retrieval-Bestand in Qdrant ist damit bewusst ein sekundärer Such-, Analyse- und Arbeitsindex, kein führendes Dokumentensystem.

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

### 8. Primärsysteme bleiben führend

FoodLab verwaltet nicht die fachliche Wahrheit der Dokumente. Es erzeugt aus Primärquellen einen verarbeitbaren, durchsuchbaren und KI-nutzbaren Wissensbestand.

### 9. Verträge und Validierung vor Komfort

Schemas, Versionierung, Regelvalidierung und kontrollierte Fehlerantworten sind Teil des Produktkerns und keine spätere Kosmetik.

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
- Queue-basierte Entkopplung zwischen API und Verarbeitung
- Retry, Leasing und Fehlerbehandlung

Dienste:

- `foodlab-worker`
- `postgres`
- Dateispeicher
- `redis` als Standard-Queue

### 4. Ingestion / Extraction Layer

Verantwortung:

- Entgegennahme und Extraktion von Texten und Dokumenten
- Parsing nach Dateityp
- OCR bei gescannten Dokumenten
- E-Mail- und Attachment-Verarbeitung
- domänenspezifische Vorverarbeitung
- Import aus externen Dokumentquellen
- Änderungs- und Reingestion-Logik

Dienste:

- `parser-service`
- `tika`
- `ocr-service`
- `mail-ingest-service`
- SharePoint-Connector
- Nextcloud-Connector
- Fileserver-Watch-Folder
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
- Similar Documents
- Metadaten- und Filterabfragen
- referenzierte Antworten mit Quellenbezug

Dienste:

- `embedding-service`
- `rag-service`
- `qdrant`

### 6. Document Intelligence Layer

Verantwortung:

- Integration externer Dokumentquellen in den Wissensbestand
- Dokumentklassifikation
- Tagging
- strukturierte Dokumentmetadaten
- Verknüpfung zwischen Primärsystem, Index und Fachprozess
- Vorbereitung dokumentbasierter Abfragen und Extraktionen

Typische Fähigkeiten:

- Klassifikation nach Dokumenttyp
- Erkennung fachlicher Kategorien
- Tagging per Regeln und LLM
- Extraktion relevanter Metadaten
- Aktualisierung bei Dokumentänderungen
- Reindizierung und Löschsynchronisation

Hinweis:

Dieser Layer erweitert bestehende DMS- oder Dateisysteme, ersetzt sie aber nicht.

### 7. Validation / Contract Layer

Verantwortung:

- zentrale Verwaltung versionierter JSON-Schemas
- Ergebnisvalidierung
- task- und dokumentspezifische Vertragsdefinition
- fachliche Regelvalidierung
- Grenzwert- und Plausibilitätsprüfungen

Dienste:

- `schema-registry`
- `rule-engine`

### 8. AI Runtime Layer

Verantwortung:

- einheitliche interne Modellansteuerung
- Backend-Routing
- Providerwahl und Fallbacks
- hardwareabhängige Ausführung

Dienste:

- `llm-router`
- `vllm`
- `ollama`

### 9. Audio Layer

Verantwortung:

- Transkription
- Speaker Enrollment / Identify
- optionale Diarization
- Audio-Metadaten

Dienste:

- `audio-api`
- optional separater Diarization-Service

### 10. Workflow / Operations Layer

Verantwortung:

- Automatisierung
- technische und operative Workflows
- internes UI / BFF
- Monitoring-nahe Hilfsfunktionen
- Compliance-nahe Nachverfolgbarkeit

Dienste:

- `n8n`
- `frontend`
- optional Reverse Proxy / Nginx
- Audit-Logging / zentrale Logsammlung perspektivisch

---

## Architektur

2-Host-Setup:

- **svc (Service Node)**
  - core-api
  - worker
  - parser-service
  - rule-engine
  - schema-registry
  - embedding-service
  - rag-service
  - postgres / redis / qdrant / n8n

- **gpu (AI Node)**
  - llm-router
  - vllm
  - optional: audio-api

Kommunikation:
- svc → gpu über **Host-IP + Port**
- kein Docker-DNS über Host-Grenzen hinweg

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
                         Postgres / Redis Queue   foodlab-worker
                                                         |
          +-------------------+--------------------+--------------------+-------------------+
          |                   |                    |                    |                   |
          v                   v                    v                    v                   v
   Ingestion / Sync      Parsing / OCR      Rule Engine /         Knowledge / RAG      LLM-Aufruf
   SharePoint /          parser / tika      Schema Validation     embedding / qdrant   llm-router
   Nextcloud / Filer     / OCR              rule-engine /         / rag-service               |
                                             schema-registry                                 |
                                                                                  +----------+-----------+
                                                                                  |                      |
                                                                                  v                      v
                                                                                vLLM                   Ollama
                                                                              (NVIDIA)        (CPU / AMD / Fallback)
```

---

## Rollenmodell

### Service Node (`svc`)

Der Service Node enthält die produktnahe Plattformlogik und die meisten persistierenden Kernkomponenten.

Typische Dienste:

- `foodlab-api`
- `foodlab-worker`
- `postgres`
- `redis`
- `parser-service`
- `tika`
- `ocr-service`
- `mail-ingest-service`
- SharePoint-Connector
- Nextcloud-Connector
- Fileserver-Watch-Folder
- `embedding-service`
- `rag-service`
- `qdrant`
- `schema-registry`
- `rule-engine`
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
- `redis`
- Dateispeicher
- definierte interne Anbindung an Parsing-, Vertrags- und LLM-Schicht

### Shared Internal Services

Gemeinsame Fähigkeiten, die von mehreren Use Cases genutzt werden:

- Parsing
- OCR
- Mail-Ingest
- DMS-/Dokumentenquellen-Ingestion
- Embeddings
- RAG / Qdrant
- Rule Engine
- Schema Registry
- Audio
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
- dokumentenbasierte Such- und Auskunftsfunktionen
- weitere Fachprozesse

Diese Trennung verhindert, dass jeder neue Anwendungsfall eigene Parsing-, LLM-, Vertrags- oder RAG-Infrastruktur mitbringt.

---

## Use Case: Dokumentenmanagement + RAG

FoodLab kann als intelligente Wissens- und Suchschicht über bestehenden Dokumentensystemen eingesetzt werden.

### Zielbild

- Dokumente bleiben in:
  - SharePoint
  - Nextcloud
  - Fileservern

- FoodLab ergänzt:
  - semantische Suche (RAG)
  - Dokumentklassifikation
  - automatisches Tagging
  - Similar Documents
  - inhaltsbasierte Q&A
  - strukturierte Extraktion
  - referenzierte Antworten mit Quellen

### Architekturprinzip

FoodLab ist kein Dokumentenmanagementsystem.

Es erweitert bestehende Systeme um:

- semantische Indizierung
- KI-gestützte Analyse
- zentrale Wissensbasis
- workflowfähige Dokumentintelligenz

Der Retrieval-Index ist ein sekundärer Arbeitsindex, kein führendes System.

### Typische Funktionen

- Suche nach Inhalt statt Dateiname
- Fragen über Dokumentbestände
- automatische Klassifikation, z. B. Vertrag, Rechnung, Richtlinie oder Support-Dokument
- Extraktion von Daten, z. B. Fristen, Beträge, Ansprechpartner oder Gültigkeiten
- Similar Documents / ähnliche Fälle
- RAG-gestützte Assistenz mit Quellenbezug
- Filterung nach Metadaten, Abteilung, Dokumenttyp oder Sicherheitskontext

### Typischer Ablauf

1. Dokument liegt in SharePoint / Nextcloud / Fileserver
2. Ingestion-Service erkennt Änderung oder neuen Eingang
3. Dokument wird referenziert und nicht zum führenden Primärdatensatz umdefiniert
4. Dokument wird geparst (Tika / OCR)
5. Text und Metadaten werden normalisiert
6. Text wird in Chunks zerlegt
7. Embeddings werden erzeugt
8. Speicherung in Qdrant
9. Optional:
   - Klassifikation
   - Tagging
   - strukturierte Extraktion
   - Similarity-Berechnung

### Abfrage

- Core API
- Frontend / Chat
- Power Automate
- Ticketsystem
- n8n / Automationen

### Beispiel

„Zeige alle Dokumente mit Kündigungsfrist größer als drei Monate und ähnlichen Klauseln wie im Referenzvertrag.“

→ Retrieval + strukturierte Extraktion + Metadatenfilter + Similarity

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
- Schema- und Regelvalidierung
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
- keine direkte Exponierung von Qdrant, Embedding, Parsing, Rule Engine oder Audio
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

### Perspektivische offizielle Erweiterungen

- `POST /api/v1/documents/index`
- `POST /api/v1/retrieval/query`
- `POST /api/v1/validate`
- `GET /api/v1/schemas/{schema_name}/{version}`

Diese Erweiterungen sind nur dann offizielle API, wenn sie vertraglich stabilisiert und dokumentiert sind. Bis dahin bleiben sie interne Serviceverträge.

### Interne Dienste

Beispiele für interne Endpunkte bzw. interne Serviceverträge:

- Parsing
- OCR
- Mail-Ingest
- Dokumentquellen-Synchronisation
- Embeddings
- RAG Index / Query
- Schema-Validierung
- Rule-Validierung
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
- Validierung gegen vorhandene Schemas oder Regeln

### Asynchron

Für größere oder langsamere Jobs wird ein Job erzeugt und später abgefragt.

Geeignet für:

- PDFs
- Office-Dokumente
- E-Mails mit Anhängen
- Retrieval- oder Agentenketten
- komplexere Analysen
- Batch- oder Workflow-Verarbeitung
- Dokumentquellen-Synchronisationen

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
- Nextcloud-Dokumente
- Fileserver-Bestände
- hochgeladene Referenzdokumente
- strukturierte oder halbstrukturierte Fachunterlagen

### Typische Consumer

- Chat / Agenten
- interne Recherche
- Ticketsystem
- Automationen
- dokumentzentrierte Auskunfts- und Suchfunktionen
- analytische oder dokumentbezogene Assistenzfunktionen

### Erweiterung: Dokumentquellen

Der Wissensbestand kann aus externen Dokumentensystemen gespeist werden.

Typische Integration:

- SharePoint-Synchronisation
- Nextcloud-Connector
- Fileserver-Watch-Folder
- Mail-Ingest für dokumentlastige Postfächer

Diese Quellen werden nicht ersetzt, sondern ergänzt.

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

### 5. Dokumentintelligenz über bestehende DMS-Systeme

```text
SharePoint / Nextcloud / Fileserver -> Ingestion / Sync -> Parsing / OCR -> Klassifikation / Tagging -> RAG / Retrieval -> API / Chat / Workflow
```

Diese Abläufe nutzen dieselbe Plattformbasis, unterscheiden sich aber im Einstiegspunkt und in der Prozesslogik.

---

## Daten- und Ingestion-Modell

### Quellen

- Text
- Datei-Uploads
- E-Mail
- SharePoint-Exporte oder APIs
- Nextcloud-Quellen
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
- Version / Änderungsstand
- Indexierungsstatus

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
- task- und dokumentspezifische Fachschemas
- serverseitig erzwungene Validierung

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
- Zugriffskontext für dokumentbezogenes Retrieval

### Sicherheitsgrundsatz

Kein Consumer darf interne Systemdetails oder Modellserver direkt kennen müssen. Sicherheit und Austauschbarkeit hängen direkt zusammen.

---

## Backup, Restore und Wartung

FoodLab soll einfach zu sichern, reproduzierbar wiederherzustellen und mit geringer Betriebsvarianz wartbar sein.

### Sicherungsebenen

- VM- oder Host-Snapshots vor größeren Änderungen
- applikationskonsistente Sicherung von Postgres
- Redis-Konfiguration und Queue-relevante Betriebsparameter
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

### Grundsatz zur Wiederherstellung

Primärdokumente bleiben in führenden Quellsystemen. FoodLab muss daher seine eigenen Verarbeitungs-, Metadaten- und Indexbestände konsistent sichern und bei Bedarf reproduzierbar aus Primärsystemen neu aufbauen können.

---

## Compliance-Bewertung

FoodLab ist primär eine technische Plattform. Die konkrete rechtliche Bewertung hängt vom Einsatzkontext, den Datenkategorien und der Betreiberrolle ab. Für die technische Architektur sind folgende Aspekte maßgeblich.

### DSGVO

Relevante Architekturprinzipien:

- Datenminimierung durch Trennung von Primärsystem und sekundärem Wissensindex
- kontrollierte Speicherung von extrahiertem Text, Metadaten und Ergebnissen
- definierte Lösch- und Reingestion-Strategien
- Auditierbarkeit von Verarbeitungsschritten
- Zugriffsschutz auf API, interne Dienste und Retrieval-Bestand
- Trennung von Test-, Entwicklungs- und Produktionsdaten

Typische Anforderungen im Betrieb:

- Verzeichnis der Verarbeitungstätigkeiten
- Rollen- und Berechtigungskonzept
- Löschkonzept für Jobs, Resultate, Chunks und Caches
- Auftragsverarbeitungs- oder interne Verantwortungszuordnung
- Prüfbarkeit, welche Daten in den Index gelangt sind

### NIS2 / betriebliche Resilienz

Soweit FoodLab in regulierten oder kritischen Umfeldern betrieben wird, unterstützt die Zielarchitektur insbesondere:

- Netzsegmentierung
- definierte externe Eintrittspunkte
- Logging und Monitoring
- Backup- und Restore-Fähigkeit
- Betriebsdokumentation
- Härtung interner Servicekommunikation
- Wiederherstellbarkeit und Incident-Handling

### Produkthaftung / KI-gestützte Entscheidungen

FoodLab liefert strukturierte Entscheidungsgrundlagen, keine autonomen Entscheidungen.

Daraus folgen als technische Leitplanken:

- nachvollziehbare Datenherkunft
- strukturierte Ergebnisse statt freier Freitextantworten
- Regelvalidierung zusätzlich zu LLM-Ausgaben
- Kennzeichnung von Unsicherheiten und Grenzen
- Möglichkeit zur Quellenangabe und Explainability
- fachliche Endentscheidung bleibt beim aufsetzenden System oder Nutzer

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

Mehrere Einstiegspfade nutzen denselben Unterbau. Dadurch steigt die Zahl der Use Cases, ohne dass jede neue Lösung eigene Infrastruktur für Parsing, Wissen, Vertragsvalidierung und Modellzugriff aufbauen muss.

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

### DMS / Dokumentquellen

SharePoint, Nextcloud und Fileserver bleiben führende Dokumentquellen. FoodLab nutzt sie als Primärquellen für Analyse, Klassifikation, Extraktion und Wissensaufbau.

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
│   ├── sharepoint-connector/
│   ├── nextcloud-connector/
│   ├── embedding-service/
│   ├── rag-service/
│   ├── schema-registry/
│   ├── rule-engine/
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
- SharePoint / Nextcloud / Fileserver sauber anbinden

### 4. Shared Knowledge sauber operationalisieren

- Embedding-Service als Standard
- zentrale Chunk-/Metadatenregeln
- Primärsysteme vs. Retrieval-System klar trennen
- Indizierung aus mehreren Quellen sauber definieren
- Similar Documents und dokumentbezogene Retrieval-Features vertraglich stabilisieren

### 5. Betrieb produktionsreif machen

- Queue
- horizontale Worker-Skalierung
- Audit-Trail
- Observability
- Backup- und Restore-Prozeduren
- Rollen- und Sicherheitsmodell
- Compliance-nahe Betriebsdokumentation

---

## Statusbewertung

FoodLab ist nicht nur Infrastruktur und nicht nur ein einzelner Fachprozess. Es ist als gemeinsame Plattformbasis für mehrere Eingangskanäle und Use Cases erkennbar.

Der nächste Reifegrad besteht darin,

- die Mehrkanal-Architektur explizit durchzuziehen,
- die gemeinsamen Shared Services verbindlich zu machen,
- den Core-Vertrag zu härten,
- die zentrale Wissenshaltung auszubauen,
- Dokumentquellen systematisch anzubinden
- und den Betrieb auf Sicherheit, Wartbarkeit, Compliance und Skalierung zu standardisieren.

---

## Zielarchitektur in einem Satz

FoodLab ist eine joborientierte Core-Plattform für strukturierte Dokument-, Text-, Wissens- und AI-Verarbeitung, die mehrere Einstiegskanäle auf einer gemeinsamen sicheren und wartbaren Basis zusammenführt, führende Dokumentquellen um einen semantischen Knowledge Layer erweitert und ihre internen AI- und Retrieval-Dienste flexibel austauschbar betreibt.
