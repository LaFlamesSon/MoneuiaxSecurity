from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from typing import List
import numpy as np
from db import pool
from face import get_embedding_from_image_bytes
from s3_client import presign_url
from fastapi.responses import RedirectResponse
from uuid import UUID
from pathlib import Path
from uuid import uuid4
from s3_client import upload_bytes
from queue_client import queue
import httpx

app = FastAPI(title="MVP Visual Search API")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    ext = Path(file.filename or "").suffix
    key = f"uploads/{uuid4()}{ext}"
    content_type = file.content_type or "application/octet-stream"
    upload_bytes(key, data, content_type)
    job = queue.enqueue("worker.process_image", key)
    return {"s3_key": key, "job_id": job.id}

@app.post("/ingest-url")
async def ingest_url(url: str):
    async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
        resp = await client.get(url)
        if resp.status_code != 200 or not resp.content:
            raise HTTPException(status_code=400, detail="Failed to fetch URL")
        content_type = resp.headers.get("content-type", "application/octet-stream")
        ext = ".jpg" if "jpeg" in content_type or "jpg" in content_type else ".png"
        key = f"uploads/{uuid4()}{ext}"
        upload_bytes(key, resp.content, content_type)
        job = queue.enqueue("worker.process_image", key)
        return {"s3_key": key, "job_id": job.id}

@app.post("/search")
async def search(file: UploadFile = File(...), k: int = 5):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    embedding = get_embedding_from_image_bytes(data)
    query_vec = np.array(embedding, dtype=np.float32)
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, s3_key_original, s3_key_thumb, 1 - (embedding <=> %s) AS score
                FROM faces
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> %s
                LIMIT %s
                """,
                (query_vec, query_vec, k),
            )
            rows = cur.fetchall()
    results: List[dict] = []
    for row in rows:
        face_id, s3_key_original, s3_key_thumb, score = row
        results.append({
            "id": str(face_id),
            "score": float(score),
            "original_url": presign_url(s3_key_original) if s3_key_original else None,
            "thumb_url": presign_url(s3_key_thumb) if s3_key_thumb else None,
        })
    return {"results": results}

@app.get("/thumbnail/{face_id}")
def thumbnail(face_id: UUID):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT s3_key_thumb FROM faces WHERE id = %s", (str(face_id),))
            row = cur.fetchone()
            if not row or not row[0]:
                raise HTTPException(status_code=404, detail="Thumbnail not found")
            url = presign_url(row[0])
    return RedirectResponse(url)
