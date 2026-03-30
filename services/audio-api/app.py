import os
import uuid
from pathlib import Path
from typing import List

import librosa
import numpy as np
import soundfile as sf
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from faster_whisper import WhisperModel
from qdrant_client import QdrantClient
from qdrant_client.http import models

app = FastAPI(title="FoodLab Audio API", version="3.0.0")

AUDIO_MODEL = os.getenv("AUDIO_MODEL", "small")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
COLLECTION = os.getenv("QDRANT_AUDIO_COLLECTION", "audio_speakers")
AUDIO_DIR = Path(os.getenv("AUDIO_DIR", "/srv/ai-gpu/audio"))
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

client = QdrantClient(url=QDRANT_URL)
model: WhisperModel | None = None

def get_model() -> WhisperModel:
    global model
    if model is None:
        model = WhisperModel(AUDIO_MODEL, device="auto", compute_type="int8")
    return model

def ensure_collection(dim: int = 32) -> None:
    try:
        client.get_collection(COLLECTION)
    except Exception:
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
        )

def audio_embedding(path: Path) -> List[float]:
    y, sr = librosa.load(str(path), sr=16000, mono=True)
    if y.size == 0:
        raise HTTPException(status_code=422, detail="empty audio")
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)
    delta = librosa.feature.delta(mfcc)
    feat = np.concatenate([mfcc.mean(axis=1), delta.mean(axis=1)])[:32]
    feat = feat.astype(np.float32)
    norm = np.linalg.norm(feat) or 1.0
    return (feat / norm).tolist()

@app.get("/health")
def health():
    return {"status": "ok", "service": "audio-api", "model": AUDIO_MODEL}

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...), language: str | None = Form(None)):
    target = AUDIO_DIR / f"{uuid.uuid4()}_{os.path.basename(file.filename or 'audio.wav')}"
    target.write_bytes(await file.read())
    segments, info = get_model().transcribe(str(target), language=language or None, vad_filter=True)
    text = " ".join(segment.text.strip() for segment in segments).strip()
    return {"status": "done", "text": text, "language": info.language, "duration": info.duration}

@app.post("/speakers/enroll")
async def enroll(speaker_name: str = Form(...), file: UploadFile = File(...)):
    target = AUDIO_DIR / f"{uuid.uuid4()}_{os.path.basename(file.filename or 'audio.wav')}"
    target.write_bytes(await file.read())
    vector = audio_embedding(target)
    ensure_collection(dim=len(vector))
    point_id = str(uuid.uuid4())
    client.upsert(
        collection_name=COLLECTION,
        points=[models.PointStruct(id=point_id, vector=vector, payload={"speaker_name": speaker_name, "path": str(target)})],
    )
    return {"status": "enrolled", "speaker_name": speaker_name, "point_id": point_id}

@app.post("/speakers/identify")
async def identify(file: UploadFile = File(...)):
    target = AUDIO_DIR / f"{uuid.uuid4()}_{os.path.basename(file.filename or 'audio.wav')}"
    target.write_bytes(await file.read())
    vector = audio_embedding(target)
    ensure_collection(dim=len(vector))
    hits = client.query_points(collection_name=COLLECTION, query=vector, limit=1).points
    if not hits:
        return {"status": "unknown"}
    hit = hits[0]
    return {"status": "identified", "speaker_name": hit.payload.get("speaker_name"), "score": hit.score}
