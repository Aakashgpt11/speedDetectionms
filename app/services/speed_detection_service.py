
import os, time
from typing import Dict, Any, List, Tuple
import numpy as np

from app.domain.speed import IngressFrame
from app.repositories.state_repository import StateRepository
from app.repositories.publisher_repository import PublisherRepository

class SpeedDetectionService:
    def __init__(self):
        self.state = StateRepository()
        self.publisher = PublisherRepository()

    @staticmethod
    def _centroid_from_bbox(b: Tuple[float, float, float, float]) -> Tuple[float, float]:
        x,y,w,h = b
        return (x + w/2.0, y + h/2.0)

    @staticmethod
    def _apply_homography(pt: Tuple[float,float], H):
        M = np.array(H, dtype=float)
        v = np.array([pt[0], pt[1], 1.0], dtype=float)
        out = M @ v
        if out[2] == 0:
            return (pt[0], pt[1])
        return (float(out[0]/out[2]), float(out[1]/out[2]))

    @staticmethod
    def _distance_meters(p1, p2) -> float:
        return float(np.hypot(p1[0]-p2[0], p1[1]-p2[1]))

    async def _compute(self, frame: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Internal helper: computes EMA speed per detection; returns list of dicts per track."""
        model = IngressFrame(**frame)
        camera_id = model.camera_id
        fps = model.fps or 5.0
        dt = 1.0/max(fps, 0.1)

        calib = model.calibration
        H = calib.homography if (calib and calib.homography) else None
        mpp = calib.meters_per_pixel if calib else None

        min_conf = (model.speed_config.min_confidence if model.speed_config else 0.7)
        ema_alpha = (model.speed_config.smoothing.ema_alpha if model.speed_config and model.speed_config.smoothing else 0.35)
        min_samples = (model.speed_config.smoothing.min_samples if model.speed_config and model.speed_config.smoothing else 3)

        results: List[Dict[str, Any]] = []

        for det in model.detections:
            if det.confidence is not None and det.confidence < min_conf:
                continue

            tid = det.tracking_id
            cx, cy = det.centroid or self._centroid_from_bbox(det.bbox)

            last = await self.state.get_track(camera_id, tid)
            if last:
                if H:
                    p_prev = self._apply_homography((last['cx'], last['cy']), H)
                    p_curr = self._apply_homography((cx, cy), H)
                    dist_m = self._distance_meters(p_curr, p_prev)
                else:
                    dist_px = float(np.hypot(cx-last['cx'], cy-last['cy']))
                    dist_m = dist_px * mpp if mpp else dist_px  # px fallback

                v_mps = dist_m / dt
                v_kmph = v_mps * 3.6
                samples = last.get('samples', 0) + 1
                v_ema = ema_alpha * v_kmph + (1-ema_alpha) * last.get('v_ema', v_kmph)

                # Update state
                await self.state.set_track(camera_id, tid, {"cx": cx, "cy": cy, "v_ema": v_ema, "samples": samples})

                # Append sample (only after min_samples)
                results.append({
                    "camera_id": camera_id,
                    "tracking_id": tid,
                    "class_name": det.class_name,
                    "bbox": det.bbox,
                    "samples": samples,
                    "speed_kmph_raw": v_kmph,
                    "speed_kmph": v_ema if samples >= min_samples else None,
                    "ts_ms": model.ts_ms
                })

            else:
                # Init state for the track
                await self.state.set_track(camera_id, tid, {"cx": cx, "cy": cy, "v_ema": 0.0, "samples": 0})
                results.append({
                    "camera_id": camera_id,
                    "tracking_id": tid,
                    "class_name": det.class_name,
                    "bbox": det.bbox,
                    "samples": 0,
                    "speed_kmph_raw": None,
                    "speed_kmph": None,
                    "ts_ms": model.ts_ms
                })

        return results

    async def compute_speeds(self, frame: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Used by POST /api/speed_detection/speed
        Returns a list of speed samples (test mode, no publish).
        """
        return await self._compute(frame)

    async def compute_violations(self, frame: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Used by POST /api/speed_detection/overspeeding
        Reuses _compute() but filters to overspeed and returns would-emit violation events.
        """
        results = await self._compute(frame)
        model = IngressFrame(**frame)
        camera_id = model.camera_id
        speed_limit = (model.speed_config.speed_limit_kmph
                       if model.speed_config and model.speed_config.speed_limit_kmph is not None else None)

        if speed_limit is None:
            return []  # no limit, no violations

        violations: List[Dict[str, Any]] = []
        debounce_sec = int(os.getenv('VIOLATION_DEBOUNCE_SEC', '10'))

        for r in results:
            if r["speed_kmph"] is None:
                continue
            if r["speed_kmph"] > speed_limit:
                over_pct = (r["speed_kmph"] - speed_limit) * 100.0 / max(speed_limit, 1e-6)
                bucket = int((r["ts_ms"] or int(time.time()*1000)) / 1000)
                dedupe_key = f"{camera_id}:{r['tracking_id']}:{bucket}:speed"

                # Debounce (but do not publish in test mode)
                last_ts = await self.state.get_last_violation_ts(camera_id, r["tracking_id"])
                now_s = int(time.time())
                ok_debounce = True if last_ts is None else (now_s - last_ts) >= debounce_sec

                if ok_debounce:
                    evt = await self.publisher.build_violation_event(
                        camera_id, model.event_id,
                        {
                            "tracking_id": r["tracking_id"],
                            "class_name": r["class_name"],
                            "speed_kmph": float(r["speed_kmph"]),
                            "speed_limit_kmph": float(speed_limit),
                            "over_speed_percentage": float(over_pct),
                            "bbox": r["bbox"],
                            "evidence_img": model.img_ref,
                            "attributes": None
                        },
                        dedupe_key
                    )
                    violations.append(evt)
                    # Record last violation time so repeated calls behave realistically
                    await self.state.set_last_violation_ts(camera_id, r["tracking_id"], now_s)

        return violations
