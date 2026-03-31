# FoodLab Roadmap zur Produktionsreife

## Ziel

Diese Roadmap beschreibt die schrittweise Entwicklung von FoodLab von einem funktionierenden technischen Stack hin zu einer produktionsreifen Plattform mit priorisierten Use Cases.

Prioritäten:

1. Power Automate Integration
2. Ticketsystem (Power App)
3. n8n (für Tests / Orchestrierung)
4. Frontend / Chat / Agenten (niedrigste Priorität)

---

# Phase 0 – Architektur-Fixierung

## Ziel

Klare Trennung zwischen Plattform, internen Services und Use Cases.

## Ergebnisse

* FoodLab Core als stabile Plattform definiert
* Externe vs. interne APIs festgelegt
* Einstiegskanäle priorisiert

---

# Phase 1 – Core stabilisieren

## Sprint 1 – JSON-Vertrag & API

### Ziel

Stabile, versionierte API als Basis für alle Integrationen.

### Aufgaben

* JSON-Response-Envelope definieren
* Schema-Version einführen
* Pydantic-/Schema-Validierung
* Fehlerstruktur standardisieren
* OpenAPI bereinigen

### Definition of Done

* Alle Endpunkte liefern konsistentes JSON
* Fehler sind maschinenlesbar

---

## Sprint 2 – Runtime-Entkopplung

### Ziel

Zentraler Zugriff auf LLMs über llm-router

### Aufgaben

* Worker → llm-router umstellen
* direkte Modellzugriffe entfernen
* Retry/Timeout implementieren
* Modellkonfiguration externalisieren

### Definition of Done

* Modelle austauschbar ohne Codeänderung

---

## Sprint 3 – Ingestion & Parsing

### Ziel

Reproduzierbare Dokumentverarbeitung

### Aufgaben

* Parser kapseln
* Dateitypen erweitern (PDF, DOCX, XLSX)
* Metadatenmodell einführen
* Regelengine modularisieren

### Definition of Done

* Gleiche Inputs liefern gleiche Ergebnisse

---

# Phase 2 – Power Automate Integration (Priorität A)

## Sprint 4 – Power Automate MVP

### Ziel

Erster produktiver Einstiegskanal

### Aufgaben

* API-Endpunkte finalisieren
* OpenAPI für Connector optimieren
* Beispiel-Flows erstellen
* Fehlerhandling definieren

### Definition of Done

* End-to-End Flow funktioniert stabil

---

# Phase 3 – Ticketsystem (Power App)

## Sprint 5 – Datenmodell & Integration

### Ziel

Ticketsystem nutzt FoodLab als Backend

### Aufgaben

* SharePoint-Struktur definieren
* Ticketklassifikation integrieren
* FoodLab nur bei technischen Fällen nutzen

### Definition of Done

* Ticket kann FoodLab-Ergebnis referenzieren

---

## Sprint 6 – Power App MVP

### Ziel

Erste nutzbare Oberfläche

### Aufgaben

* Formular mit Pflichtfeldern
* Validierung
* Flow-Anbindung
* Ergebnisanzeige

### Definition of Done

* Tickets können vollständig bearbeitet werden

---

## Sprint 7 – Wissensaufbau

### Ziel

Tickets erzeugen strukturierte Wissensbasis

### Aufgaben

* Dokumentation speichern
* Similar Cases implementieren
* RAG-Anbindung vorbereiten

### Definition of Done

* Wissensbasis wächst automatisch

---

# Phase 4 – n8n (optional früh, wenn sinnvoll)

## Sprint 8 – n8n Integration

### Ziel

Schnelle Tests und Orchestrierung

### Aufgaben

* Referenz-Workflows
* Webhooks
* Debug-Flows

### Definition of Done

* n8n kann FoodLab vollständig nutzen

---

# Phase 5 – RAG & Wissen

## Sprint 9 – RAG produktiv

### Ziel

Zentrale Wissensbasis

### Aufgaben

* embedding-service einführen
* Chunking standardisieren
* Qdrant strukturieren

### Definition of Done

* Retrieval ist reproduzierbar

---

# Phase 5b – Document Intelligence

## Ziel

FoodLab als semantische Wissensschicht über Dokumentbeständen etablieren.

---

## Sprint 9.1 – Klassifikation & Tagging

### Aufgaben

- Dokumenttyp-Klassifikation (LLM + Regeln)
- Tagging-System definieren
- JSON-Schema für Dokumentmetadaten
- Validierung der Ergebnisse

### Definition of Done

- Dokumente sind strukturiert klassifiziert
- Tags sind reproduzierbar

---

## Sprint 9.2 – Retrieval UX

### Aufgaben

- Similar Documents
- Treffer mit Quellenangabe (Zitate / Chunk)
- Filter nach Metadaten

### Definition of Done

- Retrieval liefert nachvollziehbare Ergebnisse

---

## Sprint 9.3 – Security & Zugriff

### Aufgaben

- ACL-Konzept vorbereiten
- Bereichsfilter (z. B. Abteilung)
- keine unberechtigten Treffer

### Definition of Done

- Suchergebnisse entsprechen Zugriffskontext

---

# Phase 6 – Security & Betrieb

## Sprint 10 – Security

### Ziel

System absichern

### Aufgaben

* Reverse Proxy
* interne Dienste abschotten
* Secrets sichern

### Definition of Done

* Nur definierte APIs sind extern erreichbar

---

## Sprint 11 – Observability

### Ziel

System betreibbar machen

### Aufgaben

* Logging
* Metrics
* Healthchecks

### Definition of Done

* Fehler sind nachvollziehbar

---

## Sprint 12 – Skalierung

### Ziel

Lastfähigkeit

### Aufgaben

* Queue einführen
* Worker skalieren

### Definition of Done

* System ist horizontal skalierbar

---

## Sprint 13 – Backup & Restore

### Ziel

Produktionsreife

### Aufgaben

* Backups implementieren
* Restore testen
* Deployment standardisieren

### Definition of Done

* Wiederherstellung funktioniert sicher

---

# Phase 7 – Frontend / Chat (niedrige Priorität)

## Sprint 14 – Test-Frontend

### Ziel

Debug- und Test-UI

### Aufgaben

* Health
* Job-Submit
* RAG-Abfrage

### Definition of Done

* Plattform kann visuell getestet werden

---

## Sprint 15 – Chat / Agenten

### Ziel

Erweiterte Nutzung

### Aufgaben

* Chat-Endpunkt
* Retrieval-Integration
* Agentenlogik

### Definition of Done

* Chat nutzt denselben Core wie alle anderen Systeme

---

# Produktionsreife erreicht wenn:

* JSON-Vertrag stabil
* Power Automate produktiv
* Ticketsystem produktiv
* Wissensbasis aktiv genutzt
* Security umgesetzt
* Monitoring vorhanden
* Backup getestet

---

# Hinweis zur Umsetzung

Die Umsetzung erfolgt strikt entlang der Abhängigkeiten:

Core → Integration → Use Case → Betrieb

Frontend und Chat werden bewusst zuletzt umgesetzt, außer sie dienen als Testwerkzeug.
