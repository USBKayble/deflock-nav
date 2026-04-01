from contextlib import asynccontextmanager

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from src.api.routes import routing, cameras


from src.api.database import engine
from src.api.models import Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="DeFlock Nav API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routing.router)
app.include_router(cameras.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


# Serve static files from the Vue build directory
# Use a static path relative to the app working directory or root
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "src", "frontend", "dist")

# If the static directory doesn't exist (e.g., during development), we don't mount the static files
# Docker build will ensure this directory exists in production
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    if full_path.startswith("api/"):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not Found")

    if not os.path.exists(STATIC_DIR):
        return {"message": "Frontend not built yet. Run `npm run build` in src/frontend."}

    static_dir_real = os.path.realpath(STATIC_DIR)
    file_path = os.path.join(STATIC_DIR, full_path)
    file_path_real = os.path.realpath(file_path)

    if os.path.commonpath([static_dir_real, file_path_real]) != static_dir_real:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Forbidden")

    if os.path.exists(file_path_real) and os.path.isfile(file_path_real):
        return FileResponse(file_path_real)

    return FileResponse(os.path.join(static_dir_real, "index.html"))
