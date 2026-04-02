# FoodLab → Power Automate über On-Premises Data Gateway

## Zielbild

Power Automate ruft die interne FoodLab-API nicht direkt über das Internet auf, sondern über einen **Custom Connector**, der über ein **On-Premises Data Gateway** in das interne Netzwerk geleitet wird.

## Wichtige Festlegung

Die OpenAPI-Datei ist für **Power Automate / Power Apps** im Format **OpenAPI 2.0 (Swagger)** gehalten.

## 1. Gateway vorbereiten

### Platzierung

Installiere das Gateway **nicht** auf dem FoodLab-Container selbst, sondern auf einem stabilen Windows-Server im gleichen Netzsegment oder mit Routing auf den FoodLab-Host.

Beispiel:
- Gateway-Server: `M365-GW-01.internal.local`
- FoodLab-API: `foodlab-api.internal.local:8088`

### Anforderungen

- Windows Server, dauerhaft online
- Ausgehender Internetzugang für das Gateway zu Microsoft-Diensten
- Interner Zugriff vom Gateway-Server auf `foodlab-api.internal.local:8088`
- Fester DNS-Name statt `localhost`

### Wichtiger Punkt

Im Connector darfst du **nicht** `localhost:8088` verwenden, außer das Gateway läuft exakt auf demselben Host wie FoodLab. Normalerweise muss hier ein interner Hostname oder eine interne IP eingetragen werden.

## 2. Gateway installieren

1. Standard Gateway installieren, nicht Personal Mode.
2. Mit einem dedizierten M365-/Entra-Administratorkonto anmelden.
3. Gateway-Name eindeutig vergeben, z. B. `GW-FoodLab-Prod-01`.
4. Recovery Key dokumentieren und sicher ablegen.
5. Im Power Platform Admin Center prüfen, ob das Gateway sichtbar ist.

## 3. Gateway für Custom Connectors bereitstellen

Im Gateway muss der Zugriff für Power Apps / Power Automate freigegeben werden. Für **Custom Connectors** ist relevant, dass der Gateway-Besitzer bzw. die beteiligten Konten die nötigen Rechte haben. Für Custom Connectors ist die **Admin-Freigabe** auf dem Gateway entscheidend.

Empfehlung:
- technisches Besitzerkonto für Gateway
- separates Servicekonto für Connector/Flow
- dokumentierte Admin-Freigabe

## 4. Custom Connector anlegen

### In Solution arbeiten

Den Connector in einer **Solution** anlegen:

1. Power Automate oder Power Apps öffnen
2. **Solutions**
3. bestehende unmanaged Solution verwenden oder neue Solution `FoodLab Integration` anlegen
4. **New custom connector** → **Import an OpenAPI file**

### OpenAPI-Datei

Die Datei `foodlab-powerautomate-openapi.yaml` importieren.

## 5. Connector konfigurieren

### General

- **Scheme:** zunächst `http`, weil FoodLab intern nur intern auf Port 8088 läuft
- **Host:** `foodlab-api.internal.local:8088`
- **Base URL:** `/`

Wenn intern TLS via Reverse Proxy verfügbar ist, später auf `https` umstellen.

### Security

- Authentication type: **API Key**
- Parameter label: `x-api-key`
- Parameter name: `x-api-key`
- Parameter location: `Header`

### Definition

Es werden drei Actions importiert:
- `SubmitTextJob`
- `GetJobStatus`
- `GetJobResult`

## 6. Verbindung über Gateway herstellen

Nach dem Speichern des Connectors:

1. Neue Connection für den Custom Connector anlegen
2. API-Key hinterlegen
3. Gateway auswählen
4. Test mit `GetJobStatus` oder `SubmitTextJob`

## 7. Flow-Grundablauf

### Empfohlener Ablauf

1. Trigger aus SharePoint / Power Apps / manuell
2. Action `SubmitTextJob`
3. `job_id` aus Response lesen
4. `Do until`-Schleife auf `status = done` oder `status = error`
5. in Schleife `GetJobStatus` oder direkt `GetJobResult`
6. bei Erfolg `GetJobResult`
7. `Parse JSON`
8. Ergebnisfelder in SharePoint schreiben

### Zu speichernde Felder in SharePoint

- FoodLab Job ID
- Status
- Sample Type
- Product Name
- Matrix
- Assessment
- Validation Valid
- Rules Ok
- JSON Raw Result
- Fehlertext
- Zeitpunkt Anfrage / Antwort

## 8. Empfehlung für den ersten produktiven Schnitt

Für Phase 1 reicht die bestehende API aus. Zusätzliche FoodLab-Endpunkte sind erst dann sinnvoll, wenn du:
- synchrones Direkt-Result statt Polling willst
- ein speziell abgeflachtes M365-Responsemodell willst
- Batch-Verarbeitung brauchst

## 9. Technische Hinweise

### Hostname

Der OpenAPI-Host muss aus Sicht des **Gateway-Servers** erreichbar sein.

### HTTP intern

Für den internen Erstbetrieb ist HTTP technisch machbar. Für produktiv mittelfristig besser:
- interner Reverse Proxy
- internes TLS-Zertifikat
- dann Connector auf HTTPS umstellen

### Timeout / Polling

Nicht endlos pollen. Empfehlung:
- 5 bis 10 Schleifen
- jeweils 10 bis 20 Sekunden warten
- danach Fehlerstatus setzen

### API-Key

`change-me` nicht produktiv verwenden. Eigenen Schlüssel setzen und dokumentiert rotieren.

## 10. Nächster technischer Schritt

1. Gateway installieren
2. internen DNS-Namen für FoodLab festziehen
3. OpenAPI importieren
4. Connector testen
5. danach Flow aufbauen
