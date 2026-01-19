
# Optional background worker (run as separate process/container)
import asyncio, json, os
from typing import Dict, Any
from app.infrastructure.redis_client import get_redis
from app.services.speed_service import SpeedService

INGRESS_STREAM = os.getenv('INGRESS_STREAM','stream:det:yolo')
CONSUMER_GROUP = os.getenv('CONSUMER_GROUP','cg:logic:speed')
CONSUMER_NAME = os.getenv('CONSUMER_NAME','speed-local')
DLQ_STREAM = os.getenv('DLQ_STREAM','stream:deadletter:logic')

speed_service = SpeedService()

async def ensure_group(r):
    try:
        await r.xgroup_create(INGRESS_STREAM, CONSUMER_GROUP, id='$', mkstream=True)
    except Exception:
        pass

async def consume_loop():
    r = await get_redis()
    await ensure_group(r)
    while True:
        try:
            resp = await r.xreadgroup(groupname=CONSUMER_GROUP, consumername=CONSUMER_NAME,
                                      streams={INGRESS_STREAM: '>'}, count=64, block=2000)
            if not resp:
                continue
            for stream, messages in resp:
                for msg_id, fields in messages:
                    payload_str = fields.get('payload') or fields.get('data') or ''
                    try:
                        frame: Dict[str, Any] = json.loads(payload_str)
                        await speed_service.process_frame(frame)  # normal mode (publishes to egress)
                        await r.xack(INGRESS_STREAM, CONSUMER_GROUP, msg_id)
                    except Exception as e:
                        await r.xadd(DLQ_STREAM, {"payload": json.dumps({"error": str(e), "data": payload_str})})
                        await r.xack(INGRESS_STREAM, CONSUMER_GROUP, msg_id)
        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(0.5)
