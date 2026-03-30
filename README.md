# FoodLab

Modulare AI- und Dokumentverarbeitungsplattform für lokale oder hybride Deployments. FoodLab nimmt Texte und Dateien entgegen, extrahiert Inhalte, verarbeitet sie regelbasiert und per LLM, normalisiert die Ergebnisse in strukturierte JSON-Antworten und stellt sie über eine stabile API für Prozesssysteme wie Power Automate bereit.

---

## Zielsetzung

FoodLab soll einen belastbaren Kern für dokumenten- und textgetriebene Fachprozesse bereitstellen. Der Fokus liegt nicht auf einem generischen Chat-System, sondern auf einem reproduzierbaren Verarbeitungsweg für operative Integrationen.

Ziele:

- standardisierte API für externe Systeme
- Entkopplung von Fachlogik und AI-Runtime
- saubere Trennung von Service-Node und GPU-Node
- normierte JSON-Ergebnisse statt freier Modellantworten
- synchrone und asynchrone Verarbeitung großer Eingaben
- Erweiterbarkeit für RAG, Audio, OCR und Workflow-Automatisierung
- lokaler oder hybrider Betrieb ohne Cloud-Zwang

---

## Aktueller Stand

Der aktuelle Stand besteht aus zwei sich ergänzenden Ebenen:

1. **Betriebs- und Runtime-Ebene**
   - `setup-stack-v3-apps.sh` trennt den Stack in `svc`- und `gpu`-Rolle.
   - Der GPU-Teil betreibt `llm-router`, `vllm`, `ollama` und `audio-api`.
   - Zwischen Service- und GPU-Seite existiert das gemeinsame Netz `foodlab-svc-bridge`.

2. **FoodLab-Core als Referenzimplementierung**
   - `foodlab_install.sh` beschreibt einen modularen lokalen Stack mit `foodlab-api`, `foodlab-worker`, `foodlab-postgres`, `foodlab-tika` und `foodlab-ollama` als Core.
   - Erweiterungen sind `foodlab-qdrant`, `foodlab-rag`, `foodlab-audio`, `foodlab-n8n` und `foodlab-frontend`.
   - Zusätzlich wird eine OpenAPI für die Core-API erzeugt.

Diese Kombination definiert heute sowohl das Zielbild als auch eine bereits lauffähige Referenz für den Kern.

---

## Architektur

### 1. Gesamtbild

```text
Power Automate / On-Prem Gateway / andere Clients
                    |
                    v
              foodlab-api
                    |
        +-----------+-----------+
        |                       |
        v                       v
  Postgres / Jobstatus     foodlab-worker
                                |
          +---------------------+----------------------+
          |                     |                      |
          v                     v                      v
        Tika            Regex / Fachlogik        LLM-Aufruf
                                                      |
                                                      v
                                                llm-router
                                                      |
                              +-----------------------+----------------------+
                              |                                              |
                              v                                              v
                            vLLM                                           Ollama
                          (NVIDIA)                                    (CPU/AMD/Fallback)
```

### 2. Rollenmodell

#### Service Node (`svc`)

Der Service-Node enthält die produktnahe Verarbeitungslogik:

- `foodlab-api`
- `foodlab-worker`
- `postgres`
- `tika`
- optional `qdrant`
- optional `rag`
- optional `n8n`
- optional `frontend`
- Datenverzeichnisse für Inbox, Rohdaten, Ergebnisse und OCR

#### GPU Node (`gpu`)

Der GPU-Node kapselt AI-Runtime und spezialisierte Beschleunigung:

- `llm-router`
- `vllm` für NVIDIA
- `ollama` für CPU/AMD/Fallback
- `audio-api`
- Modellcache und Audio-Datenablage

### 3. Trennlinie Core vs. Extensions

#### Core

Alles, was für den FoodLab-Kern zwingend benötigt wird:

- `foodlab-api`
- `foodlab-worker`
- `postgres`
- `tika`
- Zugriff auf LLM-Runtime über `llm-router`

#### Extensions

Optionale oder interne Erweiterungen:

- `qdrant`
- `rag`
- `audio`
- `n8n`
- `frontend`

Diese Trennung ist fachlich wichtig: Externe Prozesssysteme sollen nur den Core sehen, nicht die internen Hilfsdienste.

---

## FoodLab-Kern

Der FoodLab-Kern ist eine joborientierte Dokument- und Texteingangsplattform.

### Aufgaben des Kerns

- Annahme von Texten und Dateien
- persistente Ablage der Eingänge
- Erstellung und Verwaltung von Jobs
- Extraktion von Textinhalten aus Dateien
- fachliche Vorverarbeitung per Regex / Regeln
- Prompt-Aufbau für die AI-Verarbeitung
- Aufruf der LLM-Runtime
- Normalisierung und Aggregation der Ergebnisse
- Bereitstellung eines stabilen JSON-Ergebnisses
- Nachvollziehbarkeit über Jobstatus, Resultate und Fehler

### Warum Job-basiert

Das Jobmodell ist bewusst gewählt, weil es für Integrationen robuster ist als reine Request/Response-LLM-Endpunkte:

- große Dateien können asynchron verarbeitet werden
- Power Automate kann pollen statt auf lange HTTP-Requests zu warten
- Fehler und Teilresultate bleiben nachvollziehbar
- mehrstufige Verarbeitung wird möglich

---

## API-Konzept

Die Core-API ist die einzige externe Integrationsfläche für Prozesssysteme.

### Leitprinzipien

- keine direkte Anbindung externer Systeme an `llm-router`
- keine direkte Exponierung von RAG, Audio oder Frontend
- Authentifizierung über API-Key
- JSON-first
- OpenAPI als stabiler Vertragsbestandteil

### Vorgesehene Kern-Endpunkte

- `GET /health`
- `POST /api/v1/jobs/text`
- `POST /api/v1/jobs/submit`
- `GET /api/v1/jobs/{job_id}`
- `GET /api/v1/jobs/{job_id}/result`

### Sync- und Async-Modus

#### Synchron

Für kleine Inputs kann `wait=true` genutzt werden. Die API wartet dann bis zum Abschluss oder Timeout und gibt direkt das Ergebnis zurück.

#### Asynchron

Für größere Dateien oder längere LLM-Laufzeiten wird ein Job erzeugt. Der Client erhält `job_id` und pollt anschließend den Status oder das Resultat.

---

## Verarbeitungsfluss

### 1. Text- oder Dateiannahme

Ein Client übergibt:

- Prompt
- Text oder Datei(en)
- optionale Korrelation-ID
- optionales Warten auf Abschluss

### 2. Persistenz und Jobanlage

Die API:

- erzeugt eine `job_id`
- speichert Uploads in die Inbox
- legt Job und Job-Dateien in Postgres an

### 3. Claiming durch Worker

Der Worker:

- claimt die nächste offene Datei
- verwendet Leasing / Reaper gegen hängengebliebene Verarbeitung
- setzt Jobstatus und Fortschritt

### 4. Extraktion

- Textdateien werden direkt gelesen
- andere Formate werden über Tika in Plaintext überführt

### 5. Vorverarbeitung

- Regex- und Regelvorprüfung
- erste strukturierte Extraktion
- Warnungen und Vorbefunde

### 6. LLM-Verarbeitung

- Aufbau eines fachlichen Prompts
- LLM-Aufruf über `llm-router`
- bevorzugte Rückgabe als JSON

### 7. Normalisierung

- Zusammenführung von Regex-Vorprüfung und LLM-Ergebnis
- Ableitung eines normierten flachen Resultats
- Ablage in DB und Result-Datei

### 8. Abschluss

- Aggregation über alle Dateien eines Jobs
- finaler Jobstatus `done` oder `error`
- Ergebnisabholung per API

---

## Daten- und Dateitypen

### Bereits sinnvoll abgedeckt

- `txt`
- `csv`
- `md`
- allgemeine Dokumentformate über Tika
- viele Office-Dokumente einschließlich `xlsx`, sofern Extraktion über Tika ausreicht

### Noch als Fachlogik zu ergänzen

- spezialisierte E-Mail-Verarbeitung für `eml` / `msg`
- HTML-Body / Plaintext-Body-Trennung
- Header-Extraktion
- Attachment-spezifische Behandlung
- domänenspezifische Parser für strukturierte Labordokumente

---

## Power-Automate-Integration

Power Automate spricht nicht direkt mit dem Modell, sondern mit der Core-API.

### Zielpfad

```text
Power Automate -> On-Premises Data Gateway -> foodlab-api
```

### Übergabemodell

Power Automate übergibt:

- Text oder Datei
- Prompt
- optionale Metadaten
- optional `correlation_id`

Die Antwort ist kein Freitext, sondern ein kontrolliertes JSON-Enveloping.

### Vorteile dieses Modells

- klare Abgrenzung zwischen Fach-API und Modellbetrieb
- bessere Fehlerdiagnose
- stabilere Connector-Definition
- geringere Kopplung an konkrete Modelle

---

## Normiertes JSON

Der Zielzustand ist ein serverseitig validiertes, versioniertes Ergebnisformat.

### Zielprinzipien

- feste Top-Level-Struktur
- Schema-Version im Response
- fachliche Findings in standardisierter Liste
- technische Metadaten getrennt von Fachdaten
- Fehler als strukturierte Liste

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
    "findings": [
      {
        "parameter": "Gesamtkeimzahl",
        "normalized_key": "gesamtkeimzahl",
        "operator": "<=",
        "value": 1000,
        "unit": "KBE/g",
        "category": "microbiology",
        "status": "ok",
        "raw_text": "..."
      }
    ],
    "warnings": []
  },
  "meta": {
    "provider": "vllm",
    "model": "Qwen/Qwen2.5-7B-Instruct"
  },
  "errors": []
}
```

Der aktuelle Referenzstand liefert bereits strukturierte JSON-Ergebnisse und ein flaches Resultat, aber das fachliche API-Schema muss noch explizit versioniert und serverseitig hart validiert werden.

---

## Betriebsmodell

### Deployment-Linien

#### 1. Referenz- / Dev-Deployment

`foodlab_install.sh` erzeugt einen lokalen Podman-Stack als modulare Referenzimplementierung.

Geeignet für:

- lokale Entwicklung
- funktionale Validierung
- Demo / Debugging
- frühe Fachtests

#### 2. Ziel-Deployment

`setup-stack-v3-apps.sh` bildet das spätere Betriebsmodell mit getrenntem Service- und GPU-Node ab.

Geeignet für:

- produktionsnahe Deployments
- Hardware-Trennung
- GPU-Skalierung
- klare Verantwortlichkeit zwischen Fachlogik und Inferenz

### Konsolidierungsrichtung

Die in `foodlab_install.sh` definierte Fachlogik wird als Referenz verstanden und schrittweise in die svc/gpu-Zielarchitektur überführt. Dauerhaft sollen nicht zwei konkurrierende Stacks gepflegt werden.

---

## Geplanter Endausbau

### 1. Core-Härtung

- versioniertes API-Schema
- Pydantic-/JSON-Schema-Validierung
- Retry bei ungültigem Modell-JSON
- bessere Fehlercodes
- Healthchecks und Readiness-Probes
- API-Rate-Limits und Request-Size-Limits

### 2. LLM-Orchestrierung

- Worker ruft nicht mehr direkt Ollama auf
- stattdessen ausschließlich `llm-router`
- Provider-Auswahl nach Last, Modell, Verfügbarkeit und Use Case
- Fallback-Ketten

### 3. Dokumentdomäne

- spezialisierte Parser für E-Mail, XLSX und Laborberichte
- regelbasierte Vorprüfung pro Dokumenttyp
- Dokumentklassifikation
- Schema-Auswahl pro Task

### 4. Queue und Skalierung

- Redis-gestützte Queue optional
- mehrere Worker-Instanzen
- horizontale Skalierung auf Dateiebene
- Lastverteilung über mehrere GPU-Nodes

### 5. Retrieval und Wissensbasis

- RAG als interne Erweiterung
- dokumentbezogene Wissensindizierung
- zitierfähige Retrieval-Antworten für interne Oberflächen

### 6. Audio-Pipeline

- Ersatz der Stub-Implementierung
- Whisper / ASR
- Speaker-Diarization
- Audio-Metadaten und Speaker-Enrolment produktionsreif

### 7. Workflow und UI

- n8n für Prozessketten und Trigger
- Frontend als internes Operations- und Debugging-UI
- kein Zwang für Kernnutzung

### 8. Observability und Betrieb

- zentrales Logging
- Metriken / Tracing
- Audit-Trail
- Backup- und Restore-Konzept

---

## Designentscheidungen

### Externe Systeme sprechen nur mit dem Core

Das reduziert Kopplung und schützt die interne Architektur vor ständigen Vertragsänderungen.

### LLM-Runtime bleibt austauschbar

Der Produktkern darf nicht von einem einzelnen Modellserver abhängen.

### Regelvorprüfung bleibt wichtig

LLMs ergänzen die Fachlogik, ersetzen sie aber nicht. Vorvalidierung und Normalisierung bleiben Pflicht.

### JSON ist Produktvertrag, nicht Modell-Laune

Das Ziel ist kein „möglichst gutes“ JSON aus dem Modell, sondern eine API, die serverseitig ein belastbares Ergebnis garantiert.

---

## Repository-Struktur (Sollbild)

```text
.
├── README.md
├── docs/
│   ├── ARCHITEKTUR.md
│   ├── POWER-AUTOMATE-INTEGRATION.md
│   └── ROADMAP.md
├── compose/
│   ├── docker-compose.svc.yml
│   └── docker-compose.ai.yml
├── services/
│   ├── foodlab-api/
│   ├── foodlab-worker/
│   ├── llm-router/
│   ├── audio-api/
│   └── ...
└── scripts/
    ├── setup-stack-v3-apps.sh
    └── foodlab_install.sh
```

---

## Statusbewertung

FoodLab ist nicht mehr nur Infrastruktur, sondern bereits als Referenzkern erkennbar. Der nächste Reifegrad besteht darin, die vorhandene Core-Logik sauber in die svc/gpu-Zielarchitektur zu überführen, die LLM-Anbindung auf `llm-router` zu standardisieren und das Ergebnisformat als versioniertes API-Schema zu härten.

