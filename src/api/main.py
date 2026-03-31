from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import routing, cameras


@asynccontextmanager
async def lifespan(app: FastAPI):
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
