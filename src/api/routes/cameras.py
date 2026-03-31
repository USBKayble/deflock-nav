from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/v1")


@router.get("/cameras")
async def get_cameras(
    bbox: str = Query(..., description="min_lon,min_lat,max_lon,max_lat"),
    type: str | None = Query(None),
    operator: str | None = Query(None),
    limit: int = Query(500, le=5000),
):
    pass


@router.get("/cameras/{osm_id}")
async def get_camera(osm_id: int):
    pass


@router.get("/stats")
async def get_stats(bbox: str = Query(...)):
    pass
