# FoodLab Roadmap zur Produktionsreife

## Status
### Erledigt

- Phase 0 komplett
- Sprint 1 größtenteils
- Sprint 4 größtenteils
- Sprint 5 größtenteils
- Sprint 6 größtenteils

### Teilweise erledigt

- Sprint 2
- Sprint 3
- Sprint 13
- Sprint 17
- Sprint 19

### Offen

- alles ab Sprint 7 außer den genannten Teilständen

## Ziel

Diese Roadmap beschreibt die schrittweise Entwicklung von FoodLab von einem funktionierenden technischen Stack hin zu einer produktionsreifen Plattform mit priorisierten Use Cases.

Prioritäten:

1. Power Automate Integration
2. Ticketsystem (Power App)
3. Dokumentquellen + Knowledge Layer
4. n8n (für Tests / Orchestrierung)
5. Frontend / Chat / Agenten (niedrigste Priorität)

---

# Phase 0 – Architektur-Fixierung

## Ziel

Klare Trennung zwischen Plattform, internen Services und Use Cases.

## Ergebnisse

* FoodLab Core als stabile Plattform definiert
* Externe vs. interne APIs festgelegt
* Einstiegskanäle priorisiert
* DMS-Abgrenzung festgeschrieben
* Queue, Schema-Verträge und Regelvalidierung als Kernbestandteile verankert

---

# Phase 1 – Core stabilisieren

## Sprint 1 – JSON-Vertrag & API

### Ziel

Stabile, versionierte API als Basis für alle Integrationen.

### Aufgaben

* JSON-Response-Envelope definieren
* Schema-Version einführen
* Pydantic-/Schema-Validierung integrieren
* Fehlerstruktur standardisieren
* OpenAPI bereinigen
* technische vs. fachliche Metadaten sauber trennen

### Definition of Done

* Alle Endpunkte liefern konsistentes JSON
* Fehler sind maschinenlesbar
* Response-Modelle sind dokumentiert und validiert

---

## Sprint 2 – Runtime-Entkopplung

### Ziel

Zentraler Zugriff auf LLMs über `llm-router`

### Aufgaben

* Worker vollständig auf `llm-router` umstellen
* direkte Modellzugriffe entfernen
* Retry/Timeout implementieren
* Modellkonfiguration externalisieren
* Provider-Fallbacks definieren
* Logging der Modellaufrufe standardisieren

### Definition of Done

* Modelle sind ohne Codeänderung austauschbar
* Providerwahl erfolgt zentral
* Worker kennt keine konkreten Modellserver mehr

---

## Sprint 3 – Ingestion & Parsing

### Ziel

Reproduzierbare Dokumentverarbeitung als belastbare Ingestion-Basis.

### Aufgaben

* Parser kapseln
* Dateitypen erweitern (`pdf`, `docx`, `xlsx`, `eml`, `msg`)
* OCR-Pfad verbindlich definieren
* Metadatenmodell einführen
* HTML-/Plaintext-Trennung für Mail-Inhalte umsetzen
* Header- und Attachment-Verarbeitung definieren
* Watch-Folder als technisches Ingestion-Muster implementieren

### Definition of Done

* Gleiche Inputs liefern gleiche Ergebnisse
* Mail- und Dateiverarbeitung ist reproduzierbar
* Dokumente liegen im normalisierten Zwischenformat vor

---

## Sprint 4 – Queue & Worker-Orchestrierung

### Ziel

Skalierbare, entkoppelte und fehlertolerante Verarbeitung über Queueing.

### Aufgaben

* `redis` als Standard-Queue integrieren
* Worker auf Queue-Consumer umbauen
* Retry-Mechanismen implementieren
* Leasing / Visibility Timeout definieren
* Fehlerfälle und Dead-Letter-Strategie vorbereiten
* Betriebsparameter für Queue und Worker externalisieren

### Definition of Done

* Jobs laufen nicht mehr direkt request-gekoppelt
* Worker können horizontal skaliert werden
* Fehlerhafte Jobs blockieren den Normalbetrieb nicht

---

## Sprint 5 – Schema Registry

### Ziel

Stabile, versionierte Datenverträge für strukturierte Ergebnisse.

### Aufgaben

* `schema-registry` als Service oder Modul definieren
* JSON-Schemas für Kern-Use-Cases modellieren
* Versionierungskonzept einführen
* Schema-Validierung in Worker bzw. Aggregation integrieren
* Fehlerbehandlung bei Schema-Verletzungen festlegen

### Definition of Done

* Ergebnisse werden gegen definierte Schemas validiert
* Schema-Versionen sind nachvollziehbar
* Use Cases können auf stabile Datenverträge bauen

---

## Sprint 6 – Rule Engine

### Ziel

Fachlogik und Validierung von LLM-Logik trennen.

### Aufgaben

* `rule-engine` definieren
* Regeldefinitionen in JSON / YAML festlegen
* Grenzwert-, Plausibilitäts- und Compliance-Prüfungen integrieren
* Worker-Anbindung umsetzen
* Ergebnisstruktur für Warnungen, Verstöße und Hinweise vereinheitlichen

---

## Sprint 6.1 - Context Builder

- Nicht komplex – einfach sauber kapseln
- Umsetzung in FoodLab, zentrale Funktion:
{
  "task": "...",
  "ticket_data": {...},
  "similar_cases": [...],
  "system_context": {...}
}

## Sprint 6.2 - Strukturierte LLM Outputs

- mehr Struktur in Outputs:
{
  "analysis": "...",
  "root_cause": "...",
  "solution": "...",
  "confidence": 0.0-1.0
}

## Sprint 6.3 Logging und Trace-ID

- jede Anfrage bekommt:

  - request_id
  - input
  - output
  - timestamp

### Definition of Done

* Regeln werden reproduzierbar angewendet
* Fachliche Validierung ist nicht mehr implizit im Worker versteckt
* LLM-Ergebnisse können regelbasiert abgesichert werden
* Context, Outputs und Logging stabil

---

# Phase 2 – Power Automate Integration (Priorität A)

## Sprint 7 – Power Automate MVP

### Ziel

Erster produktiver Einstiegskanal mit stabilem Connector-Vertrag.

### Aufgaben

* API-Endpunkte finalisieren
* OpenAPI für Custom Connector optimieren
* Beispiel-Flows erstellen
* Fehlerhandling definieren
* Sync- vs. Async-Nutzung für Flows festlegen
* Referenz-Responses dokumentieren

### Definition of Done

* End-to-End Flow funktioniert stabil
* Flows können strukturierte FoodLab-Ergebnisse direkt weiterverarbeiten
* Connector-Vertrag ist wiederholbar einsetzbar

---

## Sprint 7.1 - Qualität und Kontrolle

1. Evaluation Layer (leicht)
if confidence < 0.6:
    mark_as_low_quality

oder:

Pflichtfelder prüfen
Antwortlänge
Struktur validieren
2. Similar Case Ranking verbessern

Ziel:

Ranking + Relevanz
ggf. Embeddings (optional später)
3. Feedback-Loop vorbereiten
Nutzer kann markieren:
👍 Lösung korrekt
👎 Lösung falsch

👉 wichtig für spätere Agenten

---

# Phase 3 – Ticketsystem (Power App)

## Sprint 8 – Datenmodell & Integration

### Ziel

Ticketsystem nutzt FoodLab als Analyse-Backend ohne Architekturbruch.

### Aufgaben

* SharePoint-Struktur definieren
* Ticketklassifikation integrieren
* FoodLab nur bei technischen Fällen bzw. klar definierten Szenarien nutzen
* technische Ergebnisrückgabe im Ticketkontext abbilden
* Übergabe von Kontextfeldern an FoodLab definieren

### Definition of Done

* Ticket kann FoodLab-Ergebnis referenzieren
* Ticketprozess bleibt führend im Fachsystem
* Analyse ist sauber vom UI und Workflow getrennt

---

## Sprint 9 – Power App MVP

### Ziel

Erste nutzbare Oberfläche für den priorisierten Supportprozess.

### Aufgaben

* Formular mit Pflichtfeldern
* Validierung
* Flow-Anbindung
* Ergebnisanzeige
* Similar-Cases-Vorbereitung
* Fehler- und Statusrückmeldungen in der Oberfläche

### Definition of Done

* Tickets können vollständig bearbeitet werden
* Ergebnisanzeige ist strukturiert nutzbar
* Nutzer müssen keine technischen Details der Plattform kennen

---

## Sprint 10 – Wissensaufbau aus Tickets

### Ziel

Tickets erzeugen eine nutzbare und strukturierte Wissensbasis.

### Aufgaben

* Dokumentation speichern
* Similar Cases implementieren
* Übergabe in RAG vorbereiten
* Ticket-Ergebnis und Wissensobjekt sauber trennen
* Klassifikation und Tags aus Ticketfällen ableiten

### Definition of Done

* Wissensbasis wächst automatisch
* ähnliche Fälle sind auffindbar
* Ticketsystem und Wissenslayer bleiben logisch getrennt

---

# Phase 4 – Dokumentquellen & Knowledge Layer

## Ziel

FoodLab als semantische Wissensschicht über externen Dokumentquellen etablieren, ohne führende DMS- oder Dateisysteme zu ersetzen.

---

## Sprint 11 – SharePoint-Ingestion

### Ziel

SharePoint als primäre Dokumentquelle stabil anbinden.

### Aufgaben

* SharePoint-Connector definieren
* Änderungs- und Reingestion-Logik festlegen
* Dokumentreferenzmodell einführen
* Metadaten aus SharePoint normalisieren
* Berechtigungsrelevante Kontextfelder übernehmen
* Lösch- bzw. Deindexierungslogik vorbereiten

### Definition of Done

* SharePoint-Dokumente werden stabil referenziert und indiziert
* Änderungen werden erkannt
* Primärsystem und sekundärer Index sind sauber getrennt

---

## Sprint 12 – Nextcloud- und Fileserver-Ingestion

### Ziel

Weitere Dokumentquellen standardisiert anbinden.

### Aufgaben

* Nextcloud-Connector definieren
* Fileserver-Watch-Folder produktiv nutzbar machen
* Normalisierung unterschiedlicher Metadatenmodelle
* Reingestion bei Dateiänderung
* Fehlerfälle bei Netzwerk- oder Pfadproblemen abfangen

### Definition of Done

* Nextcloud- und Fileserver-Quellen werden kontrolliert ingestiert
* Metadatenmodell bleibt konsistent
* Quellsysteme bleiben fachlich führend

---

## Sprint 13 – RAG produktiv

### Ziel

Zentrale Wissensbasis mit reproduzierbarem Retrieval.

### Aufgaben

* `embedding-service` verbindlich einführen
* Chunking standardisieren
* Qdrant-Struktur und Collections definieren
* Metadatenmodell für externe Dokumente finalisieren
* Versionserkennung / Änderungslogik abschließen
* Reindexing-Strategie festlegen

### Definition of Done

* Retrieval ist reproduzierbar
* Dokumente aus externen Quellen werden stabil indiziert
* Änderungen werden erkannt und aktualisiert

---

## Sprint 14 – Klassifikation & Tagging

### Ziel

Dokumentquellen semantisch anreichern und systematisch nutzbar machen.

### Aufgaben

* Dokumenttyp-Klassifikation (LLM + Regeln)
* Tagging-System definieren
* JSON-Schema für Dokumentmetadaten
* Validierung der Ergebnisse
* Similar Documents vorbereiten
* Klassifikations- und Tagging-Qualität messbar machen

### Definition of Done

* Dokumente sind strukturiert klassifiziert
* Tags sind reproduzierbar
* Klassifikation ist als eigener Plattformbaustein nutzbar

---

## Sprint 15 – Retrieval UX & API

### Ziel

Retrieval als belastbare Funktion für API, Frontend und Workflows bereitstellen.

### Aufgaben

* Similar Documents
* Treffer mit Quellenangabe (Zitat / Chunk / Referenz)
* Filter nach Metadaten
* Query-API stabilisieren
* Antwortformate für dokumentbezogene Fragen definieren

### Definition of Done

* Retrieval liefert nachvollziehbare Ergebnisse
* Quellenbezug ist sichtbar
* Dokumentabfragen sind für mehrere Consumer wiederverwendbar

---

## Sprint 16 – Security & Zugriffskontext im Retrieval

### Ziel

Der Wissenslayer muss den Zugriffskontext respektieren.

### Aufgaben

* ACL-Konzept vorbereiten
* Bereichsfilter, z. B. Abteilung oder Quelle
* keine unberechtigten Treffer
* Sicherheitslabel im Metadatenmodell verankern
* Zugriffskontext in Query-Verarbeitung berücksichtigen

### Definition of Done

* Suchergebnisse entsprechen Zugriffskontext
* sensitive Dokumente werden nicht unzulässig sichtbar
* Retrieval ist nicht nur funktional, sondern kontrolliert nutzbar

---

# Phase 5 – n8n und technische Orchestrierung

## Sprint 17 – n8n Integration

### Ziel

Schnelle Tests, technische Orchestrierung und Referenz-Workflows.

### Aufgaben

* Referenz-Workflows
* Webhooks
* Debug-Flows
* Dokumentquellen-Workflows testbar machen
* API- und Retrieval-Funktionen über n8n nutzbar machen

### Definition of Done

* n8n kann FoodLab vollständig nutzen
* technische Orchestrierungen sind reproduzierbar
* n8n ist Hilfsschicht, nicht Produktkern

---

# Phase 6 – Security, Compliance und Betrieb

## Sprint 18 – Security

### Ziel

System absichern und externe Exposition kontrollieren.

### Aufgaben

* Reverse Proxy
* interne Dienste abschotten
* Secrets sichern
* TLS-Zielbild vorbereiten
* Rollen- und Token-Modell konkretisieren

### Definition of Done

* Nur definierte APIs sind extern erreichbar
* interne Dienste sind nicht direkt exponiert
* Sicherheitsgrenzen sind dokumentiert

---

## Sprint 19 – Observability

### Ziel

System betreibbar und nachvollziehbar machen.

### Aufgaben

* Logging
* Metrics
* Healthchecks
* Readiness-Probes
* Audit-Trail vorbereiten
* Betriebs-Dashboards definieren

### Definition of Done

* Fehler sind nachvollziehbar
* Dienste sind beobachtbar
* betriebsrelevante Zustände sind messbar

---

## Sprint 20 – Skalierung

### Ziel

Lastfähigkeit und horizontale Erweiterbarkeit.

### Aufgaben

* Queue finalisieren
* Worker skalieren
* Lastverhalten dokumentieren
* Engpässe zwischen svc- und gpu-Knoten identifizieren
* RAG- und Runtime-Skalierung getrennt betrachten

### Definition of Done

* System ist horizontal skalierbar
* Queue und Worker verhalten sich unter Last stabil
* Skalierungsgrenzen sind bekannt

---

## Sprint 21 – Backup & Restore

### Ziel

Wiederherstellbarkeit und Betriebsreife.

### Aufgaben

* Backups implementieren
* Restore testen
* Deployment standardisieren
* DB-Dumps und Qdrant-Snapshots dokumentieren
* Wiederaufbau aus Primärquellen für Dokumentquellen definieren

### Definition of Done

* Wiederherstellung funktioniert sicher
* Plattformdaten sind konsistent sicherbar
* Rebuild des Wissensbestands ist nachvollziehbar beschrieben

---

## Sprint 22 – Compliance

### Ziel

Technische Plattform auf rechtliche und regulatorische Anforderungen vorbereiten.

### Aufgaben

* DSGVO-Maßnahmen konkretisieren
* Löschkonzepte definieren
* Audit Logging ausbauen
* Zugriffskontrolle dokumentieren
* Trennung von Test- und Produktionsdaten verbindlich machen
* NIS2-nahe Resilienz- und Betriebsaspekte dokumentieren
* Umgang mit KI-bedingten Risiken und Grenzen dokumentieren

### Definition of Done

* Compliance-relevante Maßnahmen sind dokumentiert und technisch verankert
* Plattform unterstützt datenschutz- und betriebssicheren Einsatz
* KI-Ergebnisse sind nachvollziehbar und nicht als autonome Fachentscheidung missverständlich

---

# Phase 7 – Frontend / Chat / Agenten

## Sprint 23 – Test-Frontend

### Ziel

Debug- und Test-UI für Plattformfunktionen.

### Aufgaben

* Health
* Job-Submit
* RAG-Abfrage
* Dokumentabfragen mit Quellenbezug
* Anzeige strukturierter Ergebnisse

### Definition of Done

* Plattform kann visuell getestet werden
* API- und Retrieval-Funktionen sind über UI prüfbar
* Frontend bleibt technischer Consumer, nicht fachlicher Primärprozess

---

## Sprint 24 – Chat / Agenten

### Ziel

Erweiterte Nutzung auf Basis desselben Core und Wissenslayers.

### Aufgaben

* Chat-Endpunkt
* Retrieval-Integration
* Agentenlogik
* Quellenbezug in Antworten
* Begrenzung auf kontrollierte, nachvollziehbare Toolnutzung

### Definition of Done

* Chat nutzt denselben Core wie alle anderen Systeme
* Antworten können Retrieval-Kontext einbeziehen
* agentische Funktionen verletzen nicht die Plattformgrenzen

---

# Produktionsreife erreicht wenn:

* JSON-Vertrag stabil
* Queue und Worker entkoppelt produktiv laufen
* Power Automate produktiv
* Ticketsystem produktiv
* Wissensbasis aktiv genutzt
* Dokumentquellen stabil angebunden sind
* Security umgesetzt
* Monitoring vorhanden
* Backup getestet
* Compliance-Maßnahmen dokumentiert und technisch gestützt sind

---

# Hinweis zur Umsetzung

Die Umsetzung erfolgt strikt entlang der Abhängigkeiten:

Core → Verträge / Queue / Validierung → Integration → Dokumentquellen / Wissen → Use Case → Betrieb

Frontend und Chat werden bewusst zuletzt umgesetzt, außer sie dienen als Testwerkzeug.

---

# OPTIONAL: Erweiterung Agentensystem
Phase x – Selektive Agentifizierung (nur für bestimmte Use-Cases)

👉 NICHT global einführen

Nur für:

hybride Fälle
komplexe Tickets
1. Mini-Planner (kein Full Agent!)
if unclear_case:
    steps = [
        analyze,
        retrieve_context,
        generate_solution
    ]

👉 noch kein echtes ReAct / Chain-of-Thought nötig

2. Tool Selection (leicht)
if standard_request:
    skip_llm
elif complex_issue:
    use_llm

👉 kannst du sogar erstmal regelbasiert lassen

🔵 Phase y – echte Agent-Architektur (später, optional)

Nur wenn:

mehrere Systeme aktiv gesteuert werden
komplexe Prozesse entstehen

Dann:

Orchestrator raus
Agent rein
