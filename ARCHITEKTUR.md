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

### 5.1 Document Intelligence Layer (DMS Integration)

Verantwortung:

- Integration externer Dokumentquellen (SharePoint, Nextcloud, Fileserver)
- Synchronisation und Ingestion von Dokumenten
- Normalisierung von Dokument- und Metadaten
- Übergabe an Parsing-, Embedding- und RAG-Schicht
- KI-gestützte Klassifikation und Tagging
- Verknüpfung zwischen Primärsystem und Retrieval-Index

Grundprinzip:

FoodLab ist kein führendes Dokumentenmanagementsystem.  
Primärsysteme bleiben verantwortlich für:

- Ablage
- Versionierung
- Berechtigungen
- Revision / Audit

FoodLab erzeugt einen sekundären, semantischen Arbeits- und Suchindex.

---

### Datenfluss

Primärsystem → Ingestion → Parsing → Chunking → Embedding → Qdrant → Retrieval

---

### Unterstützte Quellen

- SharePoint (bevorzugt)
- Nextcloud (WebDAV / API)
- Fileserver (Watch-Folder / Batch)
- E-Mail / Exporte (optional)

---

### Metadatenmodell (Mindeststandard)

- source_system (sharepoint / nextcloud / filer)
- source_id
- source_path / source_url
- document_name
- version
- last_modified
- checksum
- classification (AI)
- tags (AI)
- sensitivity (optional)
- department / context

---

### Trennung von Verantwortung

Primärsystem:
- Wahrheit der Daten
- Berechtigungen
- Lebenszyklus

FoodLab:
- Analyse
- Suche
- Wissensaufbau
- Klassifikation

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

Ergänzung DMS:
SharePoint / Nextcloud / Fileserver
                |
                v
        Ingestion / Sync Layer
                |
                v
          Parsing / OCR
                |
                v
      Chunking / Embedding
                |
                v
            Qdrant (RAG)
                |
                v
      Retrieval / Tagging / LLM
