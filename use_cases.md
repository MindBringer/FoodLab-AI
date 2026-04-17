# Use Cases – FoodLab AI Plattform

## Ziel

Diese Dokumentation definiert alle relevanten Use Cases der Plattform auf einheitlicher Ebene.  
Die Plattform basiert auf einem zentralen Prinzip:

> **Mehrere Eingänge → einheitliche Verarbeitung → strukturierte AI-Ausgabe → Wissenspersistenz**

---

# 1. Struktur

## Domänen

- FoodLab (Core Business, AI-first)
- IT Support
- Wissensmanagement (cross-domain)
- Accounting / Finance
- HR
- Geschäftsführung / Management
- Plattform (technisch)

## Kategorien

- Core
- Business
- Support
- Knowledge
- Alerting
- System

---

# 2. Priorisierung

## P0 – Core Pipeline (MVP)

### UC-100 – Laborwerte per Mail verarbeiten

**Ziel**  
Automatische Verarbeitung von Laborwerten aus E-Mails inkl. AI-Auswertung und Speicherung.

**Trigger**  
E-Mail-Eingang

**Ablauf**
1. Mail kommt an
2. Power Automate triggert
3. Inhalt wird extrahiert
4. Übergabe an FoodLab-AI
5. Analyse + Embedding
6. Rückgabe an Power Automate
7. Speicherung in SharePoint

**Ergebnis**
- strukturierter Datensatz
- AI-Auswertung
- Wissenseintrag

---

### UC-101 – Input Normalisierung

**Ziel**  
Alle Eingänge in ein einheitliches Schema überführen

---

### UC-102 – AI Verarbeitung

**Ziel**  
Analyse, Interpretation und Strukturierung

---

### UC-103 – Embedding

**Ziel**  
Semantische Indizierung für spätere Nutzung

---

### UC-104 – Persistenz

**Ziel**  
Speicherung in SharePoint als Wissensbasis

---

# 3. FoodLab (Business Core)

## UC-110 – Rezeptentwicklung

AI-gestützte Entwicklung neuer Rezepte

## UC-111 – Rezeptoptimierung

Verbesserung bestehender Rezepte

## UC-112 – Fehleranalyse

Analyse von Problemen (z. B. Konsistenz)

## UC-113 – Skalierung

Anpassung auf Produktionsmengen

## UC-114 – Varianten generieren

Alternative Zutaten / Methoden

---

# 4. Erweiterte Eingänge

## UC-120 – Filesystem Input

Ordnerüberwachung, neue Dateien triggern Pipeline

## UC-121 – Frontend Input

User gibt strukturierte Daten ein (Power App)

## UC-122 – Alerts (System / DB)

Automatisch generierte Events

## UC-123 – Interne Folge-Cases

Cases erzeugen neue Cases

---

# 5. IT Support

## UC-200 – Ticket erstellen

User erstellt Supportfall

## UC-201 – Klassifikation

Support / Standard / Hybrid

## UC-202 – Technischer Support

Analyse + Lösung + Dokumentation

## UC-203 – Standardprozess

Organisatorische Anfrage

## UC-204 – Hybrid Case

Mischform

---

# 6. Wissensmanagement

## UC-300 – Dokumentation speichern

Problem, Ursache, Lösung

## UC-301 – Ähnliche Fälle finden

Semantische Suche

## UC-302 – Wissensaggregation

Zusammenführung von Erkenntnissen

## UC-303 – Vergleich / Trends

Analyse über mehrere Fälle

---

# 6.1 DMS / Dokumentenmanagement

## UC-350 – Dokument manuell ablegen

User speichert Dokument in SharePoint.

---

## UC-351 – Strukturierte Ablage

### Ordnerstruktur

/DMS
  /IT
    /Arbeitsanweisungen
    /Anleitungen
    /NIS2
  /QS
    /HACCP
    /Prüfprotokolle
  /Allgemein
    /Richtlinien
    /Vorlagen
  /HR
  /Finance

---

## UC-352 – Dokumenttemplate

Jedes Dokument enthält:

Titel:
Bereich:
Dokumentart:
Version:
Datum:
Autor:
Freigabe:
Gültig ab:
Beschreibung:

---

## UC-353 – Dokumentänderung erkennen (optional)

---

## UC-354 – RAG-Ingestion (später)

---

## UC-357 – Fallback

Dokumente bleiben über SharePoint zugreifbar.

---

# 7. Accounting / Finance

## UC-400 – Rechnungseingang

Erfassung und Prüfung

## UC-401 – Freigabeprozess

Genehmigungsworkflow

## UC-402 – Reisekosten

Erfassung und Prüfung

## UC-403 – Budgetanfragen

Genehmigung und Tracking

---

# 8. HR

## UC-500 – Onboarding

Neuer Mitarbeiter

## UC-501 – Offboarding

Austritt

## UC-502 – Vertragsänderung

Anpassungen

## UC-503 – HR-Anfragen

Standardprozesse

---

# 9. Geschäftsführung / Management

## UC-600 – Entscheidungsanfragen

Investitionen / Maßnahmen

## UC-601 – KPI Reporting

Zusammenfassungen und Analysen

## UC-602 – Risiko-Tracking

Erfassung kritischer Themen

---

# 10. Alerting

## UC-700 – Benachrichtigung

Events an User

## UC-701 – Reminder / SLA

Zeitbasierte Trigger

## UC-702 – Anomalie Alerts

Erkennung auffälliger Werte

---

# 11. Plattform (System)

## UC-900 – Datenpersistenz

SharePoint als zentrale Ablage

## UC-901 – Workflow Orchestrierung

Power Automate

## UC-902 – UI / UX

Power Apps / Frontend

## UC-903 – Berechtigungen

Zugriffskontrolle

## UC-904 – Audit / DSGVO

Nachvollziehbarkeit

---

## UC-905 – Datenmodell

- input
- normalized_input
- ai_output
- metadata
- status

---

## UC-906 – API Contract

- Request Schema
- Response Schema
- Fehlerstruktur

---

## UC-907 – Statusmodell

- new
- processing
- done
- error
- review

---

## UC-908 – Fehlerhandling

- Parsing Fehler
- AI Fehler
- Persistenz Fehler

---
