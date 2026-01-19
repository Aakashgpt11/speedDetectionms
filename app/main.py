
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.controllers.speed_detection_controller import router as speed_detection_router

app = FastAPI(title="AGV-VA Speed Detection Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# One router for all speed_detection endpoints
app.include_router(speed_detection_router, prefix="/api/speed_detection")
