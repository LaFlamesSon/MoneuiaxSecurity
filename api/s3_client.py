import boto3
from config import settings

s3 = boto3.client("s3", region_name=settings.aws_region)

def upload_bytes(key: str, data: bytes, content_type: str) -> None:
    s3.put_object(Bucket=settings.s3_bucket, Key=key, Body=data, ContentType=content_type)

def get_bytes(key: str) -> bytes:
    obj = s3.get_object(Bucket=settings.s3_bucket, Key=key)
    return obj["Body"].read()

def presign_url(key: str, expires_in: int = 3600) -> str:
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket, "Key": key},
        ExpiresIn=expires_in,
    )
