import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://deflock:localdev@localhost:5432/deflock_nav")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    VALHALLA_URL: str = os.getenv("VALHALLA_URL", "http://localhost:8002")
    OVERPASS_URL: str = os.getenv("OVERPASS_URL", "https://overpass-api.de/api/interpreter")
    OSRM_URL: str = os.getenv("OSRM_URL", "https://router.project-osrm.org")

settings = Settings()
