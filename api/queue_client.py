import redis
from rq import Queue
from config import settings

redis_client = redis.from_url(settings.redis_url)
queue = Queue("default", connection=redis_client, default_timeout=600)
