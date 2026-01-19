
from typing import Optional, Tuple, List
from pydantic import BaseModel

class Detection(BaseModel):
    type: str = "vehicle"
    tracking_id: str
    class_name: Optional[str] = None
    bbox: Tuple[float, float, float, float]
    confidence: Optional[float] = None
    centroid: Optional[Tuple[float, float]] = None
    speed_kmph: Optional[float] = None  # if upstream provides

class Calibration(BaseModel):
    meters_per_pixel: Optional[float] = None
    homography: Optional[List[List[float]]] = None  # 3x3
    speed_unit: str = "kmph"

class Smoothing(BaseModel):
    ema_alpha: float = 0.35
    min_samples: int = 3

class SpeedConfig(BaseModel):
    speed_limit_kmph: Optional[float] = None
    min_confidence: float = 0.7
    smoothing: Smoothing = Smoothing()

class IngressFrame(BaseModel):
    event_id: Optional[str] = None
    camera_id: str
    ts_ms: Optional[int] = None
    fps: float = 5.0
    img_ref: Optional[str] = None
    detections: List[Detection]
    calibration: Optional[Calibration] = None
    speed_config: Optional[SpeedConfig] = None
