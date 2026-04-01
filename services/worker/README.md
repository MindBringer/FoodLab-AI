# Worker-Umbau auf echten LLM-Pfad

## Ersetzt
- `services/worker/app/worker.py`

## Zusätzliche Env-Variablen

```env
WORKER_ENABLE_LLM=1
WORKER_LLM_TIMEOUT=90
WORKER_LLM_MAX_CHARS=12000
WORKER_LLM_FALLBACK_HEURISTIC=1
```

## Verhalten

- Parser/Text wird wie bisher verarbeitet
- Worker baut einen Prompt
- Aufruf an `LLM_ROUTER_URL + /chat`
- Antwort muss JSON enthalten
- JSON wird in das Schema `tasks/document_analysis` normalisiert
- danach wie bisher:
  - schema-registry
  - rule-engine
  - Persistenz

## Rollout

1. Datei austauschen
2. Env ergänzen
3. `bash setup-stack.sh svc`
4. Testjob absetzen
