
from fastapi import APIRouter, Body, HTTPException
from typing import Dict, Any
from app.services.speed_detection_service import SpeedDetectionService

router = APIRouter(tags=["speed_detection"])
_service = SpeedDetectionService()

@router.get("/healthcheck")
async def healthcheck():
    return {"status": "ok", "service": "speed-detection", "version": "1.0.0"}

@router.post("/speed")
async def speed(event: Dict[str, Any] = Body(...)):
    """
    Test-mode: computes per-frame speeds using homography or meters_per_pixel,
    returns computed 'speed_sample' style objects (no publish).
    """
    try:
        samples = await _service.compute_speeds(event)  # returns list of {tracking_id, speed_kmph, ...}
        return {"status": "ok", "samples": samples}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/overspeeding")
async def overspeeding(event: Dict[str, Any] = Body(...)):
    """
    Test-mode: reuses the same compute path but filters to only overspeeding vehicles.
    Returns would-emit violation events (no publish).
    """
    try:
        violations = await _service.speed_detection_service.compute_violations(event)  # returns list of violation events
        return {"status": "ok", "violations": violations}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
