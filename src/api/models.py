from sqlalchemy import Column, Integer, String, BigInteger, DateTime, func
from geoalchemy2 import Geometry
from src.api.database import Base

class Camera(Base):
    __tablename__ = "cameras"

    osm_id = Column(BigInteger, primary_key=True, index=True)
    location = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)
    surveillance_type = Column(String(50))
    camera_direction = Column(Integer)
    camera_type = Column(String(50))
    operator = Column(String(255))
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
