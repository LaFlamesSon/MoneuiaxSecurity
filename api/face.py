from __future__ import annotations
import threading
from typing import List, Optional
import numpy as np
import cv2
from insightface.app import FaceAnalysis
from config import settings

_model_lock = threading.Lock()
_face_app: Optional[FaceAnalysis] = None

def _get_face_app() -> FaceAnalysis:
    global _face_app
    if _face_app is None:
        with _model_lock:
            if _face_app is None:
                face_app = FaceAnalysis(name="buffalo_l", providers=[settings.insightface_provider])
                face_app.prepare(ctx_id=0)
                _face_app = face_app
    return _face_app

def get_embedding_from_image_bytes(image_bytes: bytes) -> List[float]:
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Failed to decode image")
    app = _get_face_app()
    faces = app.get(image)
    if not faces:
        raise ValueError("No face detected")
    faces.sort(key=lambda f: (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]), reverse=True)
    embedding = faces[0].normed_embedding.astype(np.float32)
    return embedding.tolist()
