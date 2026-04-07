# Power Automate Flow – FoodLab Phase 1

Dieses Dokument beschreibt den kompletten Ziel-Flow für den aktuellen Phase-1-Stand:
- streng regelbasiert
- LLM nur zur Inhaltsinterpretation
- asynchrone Job-Verarbeitung
- saubere Traceability
- SharePoint als führendes Fachsystem

## Zielbild

```text
Trigger (Power App / SharePoint / Manuell)
  -> Variablen / Trace initialisieren
  -> FoodLab Submit (Text oder Datei)
  -> Job-ID übernehmen
  -> Do until: Poll Result
  -> Status auswerten
  -> Parse JSON
  -> SharePoint aktualisieren
  -> optional Rückgabe an Power App / weiteren Flow
```

---

## 1. Voraussetzungen

### Connector
Verwende die neue OpenAPI-Datei:
- `FoodLab-OpenAPI-v2-replace.yaml`

### Erforderliche Aktionen / Konnektoren
- Power Apps oder SharePoint Trigger
- Custom Connector: FoodLab
- SharePoint
- Data Operations: Compose, Parse JSON
- Variables
- Control: Condition, Do until, Delay, Scope

---

## 2. Benötigte Felder im Flow

### Eingabefelder
- `TicketId` oder SharePoint `ID`
- `Beschreibung` / zu analysierender Text
- optional: Dateianhang
- `schema_name`
- `schema_version`
- `rule_set`

### Empfohlene Standardwerte
- `schema_name = tasks/document_analysis`
- `schema_version = 1.0.0`
- `rule_set = document_analysis_v1`
- `entry_channel = power_automate`
- `source_system = sharepoint` oder `powerapp`

---

## 3. Flow A – Textanalyse

## Schritt 1: Trigger
Beispiel:
- `When an item is created`
- oder `Power Apps (V2)`

### Empfohlene Trigger-Felder
- Beschreibung
- Kategorie
- Anfrageart
- ID

---

## Schritt 2: Variablen initialisieren

### Variable `varCorrelationId` (String)
Wert:
```text
guid()
```

### Variable `varTraceId` (String)
Wert:
```text
guid()
```

### Variable `varJobId` (String)
Wert:
```text
''
```

### Variable `varJobStatus` (String)
Wert:
```text
queued
```

### Variable `varPollCount` (Integer)
Wert:
```text
0
```

### Variable `varMaxPollCount` (Integer)
Wert:
```text
20
```

### Variable `varPollDelaySeconds` (Integer)
Wert:
```text
15
```

---

## Schritt 3: Compose – Request Body aufbauen

Aktion: `Compose`  
Name: `Compose_FoodLab_Text_Request`

Inhalt:

```json
{
  "text": "@{triggerBody()?['Beschreibung']}",
  "schema_name": "tasks/document_analysis",
  "schema_version": "1.0.0",
  "rule_set": "document_analysis_v1",
  "entry_channel": "power_automate",
  "metadata": {
    "ticket_id": "@{triggerBody()?['ID']}",
    "kategorie": "@{triggerBody()?['Kategorie']}",
    "anfrageart": "@{triggerBody()?['Anfrageart']}"
  },
  "meta": {
    "correlation_id": "@{variables('varCorrelationId')}",
    "trace_id": "@{variables('varTraceId')}",
    "source_system": "sharepoint",
    "business_context": {
      "site": "IT-Support",
      "list": "IT-Support-Tickets"
    }
  }
}
```

Bei Power Apps statt `triggerBody()` entsprechend die Power-Apps-Parameter einsetzen.

---

## Schritt 4: FoodLab – Submit Text Job

Aktion: `Custom Connector -> SubmitTextJob`

Body:
```text
outputs('Compose_FoodLab_Text_Request')
```

Wichtig:
- Der Connector muss HTTP `202` akzeptieren.
- Auth über `x-api-key` im Connector.

---

## Schritt 5: Job-ID speichern

Aktion: `Set variable`  
Variable: `varJobId`

Wert:
```text
body('SubmitTextJob')?['job_id']
```

---

## Schritt 6: Initialer SharePoint-Status

Aktion: `Update item`

Felder:
- `FoodLabJobId = @{variables('varJobId')}`
- `FoodLabStatus = queued`
- `FoodLabCorrelationId = @{variables('varCorrelationId')}`
- `FoodLabTraceId = @{variables('varTraceId')}`

Empfehlung:
- Speichere Correlation- und Trace-ID direkt im Ticket.
- Das spart dir später Debug-Zeit.

---

## Schritt 7: Do Until – auf Ergebnis pollen

Aktion: `Do until`

Abbruchbedingung:
```text
or(
  equals(variables('varJobStatus'),'done'),
  equals(variables('varJobStatus'),'failed'),
  greaterOrEquals(variables('varPollCount'),variables('varMaxPollCount'))
)
```

### Inhalt der Schleife

#### 7.1 Delay
Aktion: `Delay`

Wert:
```text
PT15S
```

oder dynamisch:
```text
concat('PT', string(variables('varPollDelaySeconds')), 'S')
```

#### 7.2 Get Job Result
Aktion: `Custom Connector -> GetJobResult`

Parameter:
- `job_id = @{variables('varJobId')}`

#### 7.3 Status setzen
Aktion: `Set variable`  
Variable: `varJobStatus`

Wert:
```text
body('GetJobResult')?['status']
```

#### 7.4 Poll-Zähler erhöhen
Aktion: `Increment variable`
- `varPollCount += 1`

#### 7.5 Optional: Zwischenstatus nach SharePoint
Aktion: `Update item`

Nur wenn du Live-Status willst:
- `FoodLabStatus = @{variables('varJobStatus')}`

---

## Schritt 8: Status nach Polling auswerten

Aktion: `Condition`

### Bedingung 1: `done`
```text
equals(variables('varJobStatus'),'done')
```

#### Dann-Zweig

##### 8.1 Parse JSON – Result Envelope
Content:
```text
body('GetJobResult')
```

Schema:
Verwende das Schema aus `FoodLab-Job-Envelope-Schema-v1.json`.

##### 8.2 SharePoint aktualisieren
Beispielmapping:

- `FoodLabStatus = done`
- `FoodLabSuccess = @{body('GetJobResult')?['success']}`
- `FoodLabSchemaVersion = @{body('GetJobResult')?['schema_version']}`
- `FoodLabResultJson = @{string(body('GetJobResult')?['data']?['result'])}`
- `FoodLabValidationJson = @{string(body('GetJobResult')?['data']?['validation'])}`
- `FoodLabRulesJson = @{string(body('GetJobResult')?['data']?['rules'])}`
- `FoodLabRequestId = @{body('GetJobResult')?['meta']?['trace']?['request_id']}`
- `FoodLabProcessingMs = @{body('GetJobResult')?['meta']?['runtime']?['processing_ms']}`

##### 8.3 Optional Rückgabe an Power App
Mit `Respond to a PowerApp or flow`:
- `status`
- `job_id`
- `result_json`
- `validation_json`
- `rules_json`

---

### Bedingung 2: `failed`
```text
equals(variables('varJobStatus'),'failed')
```

#### Dann-Zweig
`Update item`:

- `FoodLabStatus = failed`
- `FoodLabErrorCode = @{first(body('GetJobResult')?['errors'])?['code']}`
- `FoodLabErrorMessage = @{first(body('GetJobResult')?['errors'])?['message']}`
- `FoodLabErrorDetails = @{string(first(body('GetJobResult')?['errors'])?['details'])}`

Optional:
- Teams Nachricht
- Planner Eskalation
- manueller Review

---

### Sonst-Zweig: Polling-Timeout
Wenn weder `done` noch `failed`, aber `varMaxPollCount` erreicht wurde:

`Update item`:
- `FoodLabStatus = timeout`
- `FoodLabErrorMessage = Polling timeout in Power Automate`

Empfehlung:
- Diese Fälle nicht verwerfen.
- Später erneut pollbar machen oder separaten Follow-up-Flow anstoßen.

---

## 4. Flow B – Datei-Upload

Nutze denselben Flow-Grundaufbau, aber mit Datei-Submit.

## Schritt 1 bis 2
Gleich wie im Text-Flow.

## Schritt 3: Datei besorgen
Mögliche Quellen:
- SharePoint `Get file content`
- Power Apps Datei-Input
- OneDrive / Filesystem / Mail Attachment

## Schritt 4: FoodLab – Submit File Job

Aktion:
`Custom Connector -> SubmitFileJob`

Parameter:
- `schema_name = tasks/document_analysis`
- `schema_version = 1.0.0`
- `rule_set = document_analysis_v1`
- `entry_channel = power_automate`
- `correlation_id = @{variables('varCorrelationId')}`
- `trace_id = @{variables('varTraceId')}`
- `source_system = sharepoint`

Dateifeld:
- `file = File Content`

Danach identisch weiter:
- `varJobId`
- Polling
- SharePoint Update

---

## 5. Empfohlene SharePoint-Spalten

Für Phase 1 sinnvoll:

### Technische Felder
- `FoodLabJobId` (Text)
- `FoodLabStatus` (Choice/Text)
- `FoodLabCorrelationId` (Text)
- `FoodLabTraceId` (Text)
- `FoodLabRequestId` (Text)
- `FoodLabSchemaVersion` (Text)
- `FoodLabProcessingMs` (Number)

### Ergebnisfelder
- `FoodLabResultJson` (Mehrzeiliger Text)
- `FoodLabValidationJson` (Mehrzeiliger Text)
- `FoodLabRulesJson` (Mehrzeiliger Text)

### Fehlerfelder
- `FoodLabErrorCode` (Text)
- `FoodLabErrorMessage` (Mehrzeiliger Text)
- `FoodLabErrorDetails` (Mehrzeiliger Text)

---

## 6. Flow-Struktur mit Scopes

Für sauberes Fehlerhandling:

### Scope `Prepare`
- Trigger lesen
- Variablen
- Compose Body

### Scope `Submit`
- SubmitTextJob / SubmitFileJob
- Job-ID speichern

### Scope `Poll`
- Do Until
- GetJobResult

### Scope `Persist`
- SharePoint Update
- Antwort an Aufrufer

### Scope `Fail`
Catch-Scope mit `Configure run after`

---

## 7. Empfohlene Fehlerbehandlung

### Technische Fehler
- Connector nicht erreichbar
- Gateway down
- Timeout
- 401 / API-Key falsch

### Fachliche Fehler
- Schema-Verletzung
- Regelverletzung
- unbrauchbare Analyse

### Maßnahmen
- Ticketstatus sauber setzen
- Fehler roh speichern
- keine stillen Fehler
- keine impliziten Retries in Power Automate ohne Log

---

## 8. Wichtige Regeln für Phase 1

- Kein Agent-Verhalten im Flow
- Keine fachliche Entscheidungslogik in Power Automate verstecken
- Flow bleibt Orchestrierung, nicht Intelligenzschicht
- Fachliches Ergebnis immer aus `data`
- Trace/Runtime immer aus `meta`
- Statussteuerung immer über `status`

---

## 9. Minimales Testset

### Test 1
Normale Textanalyse mit gültigem Text

Erwartung:
- Submit = 202
- Result = done
- SharePoint aktualisiert

### Test 2
Leerer oder fehlerhafter Input

Erwartung:
- sauberer Fehler oder validierungsfähiger Fail

### Test 3
API-Key falsch

Erwartung:
- 401
- Fail-Scope läuft

### Test 4
Worker langsam / Ergebnis spät

Erwartung:
- mehrere Poll-Runden
- kein Flow-Abbruch vor MaxPollCount

### Test 5
Worker liefert failed

Erwartung:
- Fehlerdetails in SharePoint

---

## 10. Klare Umbau-Reihenfolge

1. Custom Connector mit neuer OpenAPI ersetzen
2. SharePoint-Spalten ergänzen
3. bestehenden Submit-Flow auf Trace-Variablen erweitern
4. Polling auf `/result` mit Status im Envelope umbauen
5. Parse JSON nur auf finalem Ergebnis
6. Fehlerfelder mitpersistieren
7. Datei-Variante ergänzen

---

## 11. Was noch nicht in Phase 1 gehört

- Multi-Step Planning
- autonome Toolwahl
- ReAct / Agent Loops
- komplexe State Machines
- selbstständige Eskalationsentscheidungen des LLM

Das kommt frühestens später. Für jetzt zählt:
- stabil
- nachvollziehbar
- wiederholbar
