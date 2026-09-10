import os
import redis
import time
import logging

logger = logging.getLogger(__name__)

redis_client = None

def get_redis_client():
    global redis_client
    if redis_client is None:
        host = os.getenv("REDIS_HOST", "localhost")
        port = int(os.getenv("REDIS_PORT", 6379))

        # Try multiple times before giving up
        for i in range(10):  # 10 retries
            try:
                client = redis.Redis(
                    host=host,
                    port=port,
                    db=0,
                    decode_responses=True
                )
                client.ping()  # test connection
                redis_client = client
                logger.info(f"✅ Connected to Redis at {host}:{port}")
                break
            except redis.exceptions.ConnectionError as e:
                logger.warning(f"⏳ Redis not ready ({i+1}/10). Retrying in 2s...")
                time.sleep(2)
        else:
            logger.error(f"❌ Could not connect to Redis at {host}:{port} after retries")
            redis_client = None

    return redis_client
