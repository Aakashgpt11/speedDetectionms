
import json, os, time, uuid
from typing import Dict, Any
from app.infrastructure.redis_client import get_redis

EGRESS_STREAM = os.getenv("EGRESS_STREAM", "stream:logic:events")

class PublisherRepository:
    async def publish_violation(self, camera_id: str, source_event_id: str | None, payload: Dict[str, Any], dedupe_key: str):
        r = await get_redis()
        event = {
            "logic_event_id": str(uuid.uuid4()),
            "source_event_id": source_event_id,
            "type": "speed_violation",
            "model_id": "AGV-VA-SPED",
            "camera_id": camera_id,
            "ts_ms": int(time.time()*1000),
            "payload": payload,
            "severity": "high",
            "dedupe_key": dedupe_key,
            "version": "1.0.0",
            "ttl_sec": 604800
        }
        await r.xadd(EGRESS_STREAM, {"payload": json.dumps(event)})

    async def build_violation_event(self, camera_id: str, source_event_id: str | None, payload: Dict[str, Any], dedupe_key: str) -> Dict[str, Any]:
        return {
            "logic_event_id": str(uuid.uuid4()),
            "source_event_id": source_event_id,
            "type": "speed_violation",
            "model_id": "AGV-VA-SPED",
            "camera_id": camera_id,
            "ts_ms": int(time.time()*1000),
            "payload": payload,
            "severity": "high",
            "dedupe_key": dedupe_key,
            "version": "1.0.0",
            "ttl_sec": 604800
        }
