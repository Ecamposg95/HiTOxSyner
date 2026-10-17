from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.models.engagement import Engagement
from app.models.enums import ActivityAction
from app.models.user import User
from app.schemas.comment import CommentCreate
from app.services.activity import log_activity
from app.services.entities import entity_label, resolve_entity


def create_comment(db: Session, *, user: User, engagement: Engagement, data: CommentCreate) -> Comment:
    _, title = resolve_entity(db, engagement, data.entity_type, data.entity_id)
    comment = Comment(
        organization_id=engagement.organization_id, engagement_id=engagement.id, created_by=user.id,
        entity_type=data.entity_type, entity_id=data.entity_id, author_id=user.id, author_name=user.full_name, body=data.body,
    )
    db.add(comment)
    db.flush()
    log_activity(
        db, user=user, engagement=engagement, action=ActivityAction.COMMENTED, entity_type=data.entity_type,
        entity_id=data.entity_id, summary=f'{user.full_name} commented on {entity_label(data.entity_type)} "{title}"',
    )
    db.commit()
    db.refresh(comment)
    return comment
