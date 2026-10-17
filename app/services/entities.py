import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.action import Action
from app.models.decision import Decision
from app.models.engagement import Engagement
from app.models.finding import Finding
from app.models.initiative import Initiative
from app.models.meeting import Meeting

ENTITY_MODELS: dict[str, tuple[type, str]] = {
    "finding": (Finding, "title"),
    "initiative": (Initiative, "name"),
    "meeting": (Meeting, "title"),
    "decision": (Decision, "title"),
    "action": (Action, "title"),
}


def entity_label(entity_type: str) -> str:
    return entity_type.capitalize()


def resolve_entity(db: Session, engagement: Engagement, entity_type: str, entity_id: uuid.UUID) -> tuple[object, str]:
    """Devuelve (entidad, título). 422 si el tipo no se conoce o la entidad no es de este engagement."""
    if entity_type not in ENTITY_MODELS:
        raise HTTPException(status_code=422, detail=f"entity_type debe ser uno de: {', '.join(ENTITY_MODELS)}")
    model, title_attr = ENTITY_MODELS[entity_type]
    entity = db.get(model, entity_id)
    if entity is None or entity.engagement_id != engagement.id:
        raise HTTPException(status_code=422, detail="entity_id no pertenece a este engagement")
    return entity, getattr(entity, title_attr)
