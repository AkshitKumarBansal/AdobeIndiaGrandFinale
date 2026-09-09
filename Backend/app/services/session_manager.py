# Backend/session_manager.py

import json
import uuid
import logging
from typing import List, Dict, Any, Optional

from app.services.redis_client import get_redis_client
from app.core.auth import verify_password

# --- Constants for Redis Keys ---
SESSION_META_PREFIX = "session:meta:"
SESSION_HISTORY_PREFIX = "session:history:"
SESSION_ANALYSIS_PREFIX = "session:analysis:"
SESSION_FILES_PREFIX = "session:files:"
USER_PREFIX = "user:"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- User Management Functions ---

def create_user(email: str, hashed_password: str, name: str):
    redis = get_redis_client()
    if not redis:
        logger.error("❌ Redis client is not available. Failed to create user.")
        return None

    user_key = f"{USER_PREFIX}{email}"
    redis.hset(user_key, mapping={
        "email": email,
        "hashed_password": hashed_password,
        "name": name
    })


def get_user(email: str) -> Optional[Dict[str, Any]]:
    redis = get_redis_client()
    if not redis:
        return None
    user_key = f"{USER_PREFIX}{email}"
    user_data = redis.hgetall(user_key)
    return user_data if user_data else None


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    user = get_user(email)
    if not user:
        return None
    if not verify_password(password, user['hashed_password']):
        return None
    return user


# --- Session Management ---

def create_session(analysis_result: Dict[str, Any], user_id: str) -> Optional[str]:
    redis = get_redis_client()
    if not redis:
        logger.error("❌ Redis client is not available. Failed to create session.")
        return None

    session_id = str(uuid.uuid4())
    metadata = analysis_result.get("metadata", {})
    user_id_from_meta = metadata.get('user_id', user_id)

    with redis.pipeline() as pipe:
        # Session metadata
        meta_key = f"{SESSION_META_PREFIX}{session_id}"
        pipe.hset(meta_key, mapping={
            "persona": metadata.get("persona", ""),
            "job_to_be_done": metadata.get("job_to_be_done", ""),
            "processing_timestamp": metadata.get("processing_timestamp", ""),
            "language": metadata.get("language", "en"),
            "doc_count": len(metadata.get("input_documents", [])),
            "user_id": user_id_from_meta
        })

        # Analysis result
        analysis_key = f"{SESSION_ANALYSIS_PREFIX}{session_id}"
        pipe.set(analysis_key, json.dumps(analysis_result))

        # Files
        files_key = f"{SESSION_FILES_PREFIX}{session_id}"
        file_path_map = metadata.get("file_path_map", {})
        if file_path_map:
            pipe.rpush(files_key, *file_path_map.values())

        # Initialize chat history with a starting message
        history_key = f"{SESSION_HISTORY_PREFIX}{session_id}"
        pipe.delete(history_key)
        pipe.rpush(history_key, json.dumps({"role": "bot", "content": "Analysis complete! Here are the key insights."}))


        # Add session to user session set
        user_sessions_key = f"user:{user_id_from_meta}:sessions"
        pipe.sadd(user_sessions_key, session_id)

        pipe.execute()

    logger.info(f"✅ New session created for user {user_id_from_meta}. ID: {session_id}")
    return session_id


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    redis = get_redis_client()
    if not redis:
        return None

    analysis_key = f"{SESSION_ANALYSIS_PREFIX}{session_id}"
    history_key = f"{SESSION_HISTORY_PREFIX}{session_id}"
    files_key = f"{SESSION_FILES_PREFIX}{session_id}"

    analysis_data_json = redis.get(analysis_key)
    if not analysis_data_json:
        return None

    chat_history_raw = redis.lrange(history_key, 0, -1)
    chat_history = [json.loads(msg) for msg in chat_history_raw]

    file_paths = redis.lrange(files_key, 0, -1)

    return {
        "analysis": json.loads(analysis_data_json),
        "chat_history": chat_history,
        "file_paths": file_paths
    }


def add_message_to_history(session_id: str, message: Dict[str, str]):
    redis = get_redis_client()
    if not redis:
        return
    history_key = f"{SESSION_HISTORY_PREFIX}{session_id}"
    redis.rpush(history_key, json.dumps(message))


def get_all_sessions_metadata_for_user(user_id: str) -> List[Dict[str, Any]]:
    redis = get_redis_client()
    if not redis:
        return []

    user_sessions_key = f"user:{user_id}:sessions"
    session_ids = redis.smembers(user_sessions_key)

    sessions_metadata = []
    for session_id in session_ids:
        meta_key = f"{SESSION_META_PREFIX}{session_id}"
        metadata = redis.hgetall(meta_key)
        if metadata:
            sessions_metadata.append({
                "id": session_id,
                "persona": metadata.get('persona', ''),
                "job": metadata.get('job_to_be_done', ''),
                "timestamp": metadata.get('processing_timestamp', ''),
                "doc_count": int(metadata.get('doc_count', 0))
            })

    # FIX: Provide a default timestamp for sorting to prevent errors
    sessions_metadata.sort(
        key=lambda x: x.get('timestamp') or '1970-01-01T00:00:00Z',
        reverse=True
    )

    return sessions_metadata


def update_session(session_id: str, analysis_result: Dict[str, Any]):
    redis = get_redis_client()
    if not redis:
        logger.error("❌ Redis client is not available. Failed to update session.")
        return

    meta_key = f"{SESSION_META_PREFIX}{session_id}"
    metadata = analysis_result.get("metadata", {})
    user_id = metadata.get("user_id") or redis.hget(meta_key, "user_id")

    with redis.pipeline() as pipe:
        # Update metadata
        pipe.hset(meta_key, mapping={
            "persona": metadata.get("persona", ""),
            "job_to_be_done": metadata.get("job_to_be_done", ""),
            "processing_timestamp": metadata.get("processing_timestamp", ""),
            "language": metadata.get("language", "en"),
            "doc_count": len(metadata.get("input_documents", [])),
            "user_id": user_id
        })

        # Update analysis result
        analysis_key = f"{SESSION_ANALYSIS_PREFIX}{session_id}"
        pipe.set(analysis_key, json.dumps(analysis_result))

        # ✅ Do NOT delete chat history
        pipe.execute()

    logger.info(f"✅ Session updated with new analysis. ID: {session_id}")