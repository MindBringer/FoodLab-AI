import os
from typing import Any, Dict, List, Optional

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="FoodLab LLM Router", version="3.0.0")

DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "auto")
GPU_BACKEND = os.getenv("GPU_BACKEND", "auto")
VLLM_URL = os.getenv("VLLM_URL", "http://vllm:8000")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "qwen2.5:7b-instruct")
VLLM_MODEL = os.getenv("VLLM_MODEL", "Qwen/Qwen2.5-7B-Instruct")

class ChatRequest(BaseModel):
    prompt: str
    system: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.2
    max_tokens: int = 1024

def choose_provider(requested: Optional[str]) -> str:
    provider = (requested or DEFAULT_PROVIDER or "auto").lower()
    if provider != "auto":
        return provider
    if GPU_BACKEND == "nvidia":
        return "vllm"
    return "ollama"

def call_vllm(req: ChatRequest, model: str) -> Dict[str, Any]:
    messages = []
    if req.system:
        messages.append({"role": "system", "content": req.system})
    messages.append({"role": "user", "content": req.prompt})
    resp = requests.post(
        f"{VLLM_URL.rstrip('/')}/v1/chat/completions",
        json={
            "model": model,
            "messages": messages,
            "temperature": req.temperature,
            "max_tokens": req.max_tokens,
        },
        timeout=300,
    )
    if resp.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"vllm call failed: {resp.text[:400]}")
    data = resp.json()
    text = data["choices"][0]["message"]["content"]
    return {"provider": "vllm", "model": model, "text": text, "raw": data}

def call_ollama(req: ChatRequest, model: str) -> Dict[str, Any]:
    prompt = req.prompt if not req.system else f"{req.system}\n\n{req.prompt}"
    resp = requests.post(
        f"{OLLAMA_URL.rstrip('/')}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": req.temperature},
        },
        timeout=300,
    )
    if resp.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"ollama call failed: {resp.text[:400]}")
    data = resp.json()
    text = data.get("response", "")
    return {"provider": "ollama", "model": model, "text": text, "raw": data}

@app.get("/health")
def health():
    return {"status": "ok", "service": "llm-router", "gpu_backend": GPU_BACKEND, "default_provider": DEFAULT_PROVIDER}

@app.post("/chat")
def chat(req: ChatRequest):
    provider = choose_provider(req.provider)
    if provider == "vllm":
        return call_vllm(req, req.model or VLLM_MODEL)
    if provider == "ollama":
        return call_ollama(req, req.model or OLLAMA_CHAT_MODEL)
    raise HTTPException(status_code=400, detail=f"unsupported provider: {provider}")
