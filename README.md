
# AGV-VA Speed Detection Logic Service (MVC)

Industry-style layered layout using FastAPI + Redis Streams.

**Layers**
- controllers/ — HTTP endpoints (health, models, config, speed testing)
- services/ — business logic (speed compute, config ops)
- repositories/ — data access (Redis state, publisher, config cache)
- domain/ — entities & model catalog
- infrastructure/ — Redis client, worker/consumer
- dto/ — request/response DTOs for controllers

Run locally:
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# or docker compose up --build
```

Use the Postman collection under `postman/`.
