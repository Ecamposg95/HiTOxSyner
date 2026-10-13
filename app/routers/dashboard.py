from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_engagement
from app.models.engagement import Engagement
from app.schemas.dashboard import DashboardRead
from app.services.dashboard import build_dashboard

router = APIRouter(tags=["dashboard"])


@router.get("/engagements/{engagement_id}/dashboard", response_model=DashboardRead)
def dashboard(engagement: Engagement = Depends(get_engagement), db: Session = Depends(get_db)):
    return build_dashboard(db, engagement)
