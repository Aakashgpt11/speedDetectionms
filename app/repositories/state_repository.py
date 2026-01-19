
import json, os
from typing import Optional, Dict, Any
from app.infrastructure.redis_client import get_redis

STATE_TTL = int(os.getenv("STATE_TTL_SEC", "3600"))
DEDUP_TTL = int(os.getenv("DEDUP_TTL_SEC", "60"))

class StateRepository:
    def k_tracks(self, camera_id: str) -> str:
        return f"spd:tracks:{camera_id}"
    def k_last_viol(self, camera_id: str) -> str:
        return f"spd:last_viol:{camera_id}"

    async def get_track(self, camera_id: str, track_id: str) -> Optional[Dict[str, Any]]:
        r = await get_redis()
        v = await r.hget(self.k_tracks(camera_id), track_id)
        return json.loads(v) if v else None

    async def set_track(self, camera_id: str, track_id: str, data: Dict[str, Any]):
        r = await get_redis()
        await r.hset(self.k_tracks(camera_id), track_id, json.dumps(data))
        await r.expire(self.k_tracks(camera_id), STATE_TTL)

    async def should_emit(self, dedupe_key: str) -> bool:
        r = await get_redis()
        ok = await r.setnx(f"dedupe:{dedupe_key}", "1")
        if ok:
            await r.expire(f"dedupe:{dedupe_key}", DEDUP_TTL)
            return True
        return False

    async def get_last_violation_ts(self, camera_id: str, track_id: str) -> Optional[int]:
        r = await get_redis()
        v = await r.hget(self.k_last_viol(camera_id), track_id)
        return int(v) if v else None

    async def set_last_violation_ts(self, camera_id: str, track_id: str, ts_s: int):
        r = await get_redis()
        await r.hset(self.k_last_viol(camera_id), track_id, ts_s)
