from __future__ import annotations
from typing import Optional
import io
from PIL import Image
import imagehash
import numpy as np
from s3_client import get_bytes, upload_bytes
from face import get_embedding_from_image_bytes
from db import pool
from uuid import uuid4

THUMB_MAX_PX = 512


def process_image(s3_key: str) -> Optional[str]:
    image_bytes = get_bytes(s3_key)
    embedding = get_embedding_from_image_bytes(image_bytes)
    phash_value = _compute_phash(image_bytes)
    thumb_bytes, thumb_key = _make_and_store_thumbnail(image_bytes, source_key=s3_key)

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO faces (s3_key_original, s3_key_thumb, embedding, phash)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (s3_key, thumb_key, np.array(embedding, dtype=np.float32), int(phash_value)),
            )
            inserted_id = cur.fetchone()[0]
    return str(inserted_id)


def _compute_phash(image_bytes: bytes) -> int:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return int(str(imagehash.phash(img)), 16)


def _make_and_store_thumbnail(image_bytes: bytes, source_key: str) -> tuple[bytes, str]:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    w, h = img.size
    scale = min(1.0, THUMB_MAX_PX / max(w, h))
    new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
    thumb = img.resize(new_size)
    buf = io.BytesIO()
    thumb.save(buf, format="JPEG", quality=85)
    data = buf.getvalue()
    key = source_key.replace("uploads/", "thumbnails/")
    if key == source_key:
        key = f"thumbnails/{uuid4()}.jpg"
    upload_bytes(key, data, "image/jpeg")
    return data, key


