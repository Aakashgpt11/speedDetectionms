
from typing import Optional, List
from pydantic import BaseModel, Field

class ConfigReloadRequest(BaseModel):
    camera_ids: Optional[List[str]] = Field(default=None)

class ConfigReloadResponse(BaseModel):
    status: str = "ok"
    reloaded: List[str] = []

class ControlRequest(BaseModel):
    camera_id: str

class ControlResponse(BaseModel):
    status: str = "ok"
    action: str
    camera_id: str
