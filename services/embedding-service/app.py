import hashlib
import math
import os
import re
from typing import List, Optional

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="FoodLab Embedding Service", version="3.0.0")

EMBED_PROVIDER = os.getenv("EMBED_PROVIDER", "ollama")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", os.getenv("EMBED_MODEL", "nomic-embed-text"))
FALLBACK_DIM = int(os.getenv("EMBED_FALLBACK_DIM", "384"))

class EmbedRequest(BaseModel):
    texts: List[str]
    provider: Optional[str] = None
    model: Optional[str] = None

def stable_hash_embedding(text: str, dim: int = 384) -> List[float]:
    vec = [0.0] * dim
    for token in re.findall(r"\w+", text.lower()):
        h = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        sign = -1.0 if ((h >> 8) & 1) else 1.0
        vec[idx] += sign
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]

@app.get("/health")
def health():
    return {"status": "ok", "service": "embedding-service", "provider": EMBED_PROVIDER}

@app.post("/embed/texts")
def embed_texts(req: EmbedRequest):
    provider = (req.provider or EMBED_PROVIDER).lower()
    model = req.model or OLLAMA_EMBED_MODEL
    vectors = []
    if provider == "ollama":
        for text in req.texts:
            resp = requests.post(
                f"{OLLAMA_URL.rstrip('/')}/api/embeddings",
                json={"model": model, "prompt": text},
                timeout=180,
            )
            if resp.status_code >= 400:
                raise HTTPException(status_code=502, detail=f"ollama embedding failed: {resp.text[:400]}")
            data = resp.json()
            vec = data.get("embedding")
            if not isinstance(vec, list):
                raise HTTPException(status_code=502, detail="ollama returned invalid embedding")
            vectors.append(vec)
    elif provider == "hash":
        vectors = [stable_hash_embedding(text, dim=FALLBACK_DIM) for text in req.texts]
    else:
        raise HTTPException(status_code=400, detail=f"unsupported embedding provider: {provider}")
    return {"provider": provider, "model": model, "vectors": vectors}
