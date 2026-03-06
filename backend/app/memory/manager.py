import redis
import json
from loguru import logger
from typing import Dict, Any, Optional

class MemoryManager:
    def __init__(self, host='localhost', port=6379, db=0):
        try:
            self.redis_client = redis.StrictRedis(host=host, port=port, db=db, decode_responses=True)
            self.redis_client.ping()
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None

    def get_session(self, session_id: str) -> Dict[str, Any]:
        if not self.redis_client:
            return {}
        data = self.redis_client.get(f"session:{session_id}")
        return json.loads(data) if data else {}

    def update_session(self, session_id: str, data: Dict[str, Any], ttl: int = 3600):
        if not self.redis_client:
            return
        current_data = self.get_session(session_id)
        current_data.update(data)
        self.redis_client.setex(f"session:{session_id}", ttl, json.dumps(current_data))

    def clear_session(self, session_id: str):
        if self.redis_client:
            self.redis_client.delete(f"session:{session_id}")

    def get_patient_context(self, phone: str) -> Dict[str, Any]:
        # This could retrieve from persistent DB or a dedicated Redis hash
        if not self.redis_client:
            return {}
        data = self.redis_client.get(f"patient_pref:{phone}")
        return json.loads(data) if data else {}

    def update_patient_pref(self, phone: str, prefs: Dict[str, Any]):
        if not self.redis_client:
            return
        self.redis_client.set(f"patient_pref:{phone}", json.dumps(prefs))
