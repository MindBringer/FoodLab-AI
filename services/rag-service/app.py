import os
import re
import uuid
from typing import Any, Dict, List, Optional

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient
from qdrant_client.http import models

app = FastAPI(title="FoodLab RAG Service", version="3.0.0")

QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "docs_chunks")
EMBEDDING_URL = os.getenv("EMBEDDING_URL", "http://embedding-service:8094")
LLM_ROUTER_URL = os.getenv("LLM_ROUTER_URL", "http://llm-router:8091")

client = QdrantClient(url=QDRANT_URL)

class IngestRequest(BaseModel):
    document_name: str
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    chunk_size: int = 1200
    chunk_overlap: int = 120

class QueryRequest(BaseModel):
    query: str
    limit: int = 5
    generate_answer: bool = True
    filter: Optional[Dict[str, Any]] = None

def ensure_collection(dim: int = 384) -> None:
    try:
        client.get_collection(QDRANT_COLLECTION)
    except Exception:
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
        )

def chunk_text(text: str, chunk_size: int = 1200, chunk_overlap: int = 120) -> List[str]:
    parts = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    chunks: List[str] = []
    current = ""
    for part in parts:
        if len(current) + len(part) + 2 <= chunk_size:
            current = f"{current}\n\n{part}".strip()
        else:
            if current:
                chunks.append(current)
            current = part
    if current:
        chunks.append(current)
    if not chunks and text.strip():
        chunks = [text[:chunk_size]]
    return chunks

def embed_texts(texts: List[str]) -> List[List[float]]:
    resp = requests.post(f"{EMBEDDING_URL.rstrip('/')}/embed/texts", json={"texts": texts}, timeout=300)
    if resp.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"embedding service failed: {resp.text[:400]}")
    data = resp.json()
    return data["vectors"]

@app.get("/health")
def health():
    return {"status": "ok", "service": "rag-service", "collection": QDRANT_COLLECTION}

@app.post("/collections/init")
def init_collection():
    sample = embed_texts(["health probe"])
    ensure_collection(dim=len(sample[0]))
    return {"status": "ok", "collection": QDRANT_COLLECTION, "dim": len(sample[0])}

@app.post("/ingest/document")
def ingest_document(req: IngestRequest):
    vectors = embed_texts(["health probe"])
    ensure_collection(dim=len(vectors[0]))

    chunks = chunk_text(req.text, req.chunk_size, req.chunk_overlap)
    if not chunks:
        raise HTTPException(status_code=422, detail="no text to ingest")

    vectors = embed_texts(chunks)
    doc_id = str(uuid.uuid4())
    points = []
    for idx, (chunk, vector) in enumerate(zip(chunks, vectors), start=1):
        points.append(
            models.PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "doc_id": doc_id,
                    "chunk_id": idx,
                    "document_name": req.document_name,
                    "text": chunk,
                    **req.metadata,
                },
            )
        )
    client.upsert(collection_name=QDRANT_COLLECTION, points=points)
    return {"status": "indexed", "doc_id": doc_id, "chunks": len(points)}

@app.post("/query")
def query(req: QueryRequest):
    vectors = embed_texts([req.query])
    ensure_collection(dim=len(vectors[0]))
    hits = client.query_points(
        collection_name=QDRANT_COLLECTION,
        query=vectors[0],
        limit=max(1, min(req.limit, 20)),
    ).points
    items = [{"score": h.score, "payload": h.payload} for h in hits]
    result: Dict[str, Any] = {"items": items}
    if req.generate_answer and items:
        context = "\n\n".join(item["payload"].get("text", "") for item in items)
        llm = requests.post(
            f"{LLM_ROUTER_URL.rstrip('/')}/chat",
            json={
                "system": "Du beantwortest Fragen nur auf Basis des gelieferten Kontexts. Wenn Informationen fehlen, sag das klar.",
                "prompt": f"Kontext:\n{context}\n\nFrage:\n{req.query}",
                "temperature": 0.1,
            },
            timeout=300,
        )
        if llm.status_code < 400:
            result["answer"] = llm.json().get("text")
    return result
