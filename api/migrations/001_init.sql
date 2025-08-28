CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS faces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    s3_key_original TEXT NOT NULL,
    s3_key_thumb TEXT,
    embedding VECTOR(512),
    phash BIGINT,
    canonical_face_id UUID REFERENCES faces(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS faces_embedding_idx ON faces USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
