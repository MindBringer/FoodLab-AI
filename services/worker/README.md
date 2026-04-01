# Worker Quality v2

Diese Version verbessert zwei Punkte:

1. präziserer Prompt für contracts / invoices / lab reports
2. Warning-Sanitizing gegen generische LLM-Sätze wie:
   - "Keine relevante Analysefunde ..."
   - "Keine Informationen gefunden"

## Ersetzt
- `services/worker/app/worker.py`

## Rollout

```bash
cp /mnt/data/worker_llm_quality_v2.py /opt/FoodLab-AI/services/worker/app/worker.py
cd /opt/FoodLab-AI
bash setup-stack.sh svc
```

## Erwartung

Bei Vertragstexten:
- `document_type=contract`
- `findings=[]`
- keine generischen Analyse-Warnings
- weiterhin:
  - `llm_provider=...`
  - `llm_model=...`
