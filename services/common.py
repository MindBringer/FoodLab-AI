import hashlib
import math
import os
import re
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

def stable_hash_embedding(text: str, dim: int = 384) -> List[float]:
    vec = [0.0] * dim
    for token in re.findall(r"\w+", text.lower()):
        h = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        sign = -1.0 if ((h >> 8) & 1) else 1.0
        vec[idx] += sign
    norm = math.sqrt(sum(v*v for v in vec)) or 1.0
    return [v / norm for v in vec]
