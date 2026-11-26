from fastapi import APIRouter, Query

from app.services import stats_service

router = APIRouter()


@router.get("/stats/daily-sales")
def daily_sales(days: int = Query(7, ge=1, le=90)):
    return stats_service.daily_sales(days=days)
