import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.engagement import Engagement


def require_in_engagement(db: Session, model, entity_id: uuid.UUID | None, engagement: Engagement, field: str):
    """Carga la entidad referenciada y exige que sea del mismo engagement.

    Devuelve None si entity_id es None. Responde 422 (nunca 404) cuando la entidad no existe o es de otro
    engagement, para no revelar la existencia de datos ajenos.
    """
    if entity_id is None:
        return None
    entity = db.get(model, entity_id)
    if entity is None or entity.engagement_id != engagement.id:
        raise HTTPException(status_code=422, detail=f"{field} no pertenece a este engagement")
    return entity
