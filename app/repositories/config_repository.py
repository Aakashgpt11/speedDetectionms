
import json
from typing import Optional, Dict, Any
from app.infrastructure.redis_client import get_redis

class ConfigRepository:
    async def get_calibration(self, camera_id: str) -> Optional[Dict[str, Any]]:
        r = await get_redis()
        data = await r.get(f"cfg:calib:{camera_id}")
        return json.loads(data) if data else None
