import uuid

from app.models.engagement import Engagement
from app.models.enums import Health, OrganizationKind, Role
from app.models.organization import Organization
from app.models.user import User


def test_models_persist_with_defaults(db):
    org = Organization(name="Cliente Demo", slug="cliente-demo", kind=OrganizationKind.CLIENT)
    db.add(org)
    db.flush()
    engagement = Engagement(organization_id=org.id, name="Programa")
    user = User(organization_id=org.id, email="a@b.com", full_name="A", password_hash="x", role=Role.HITO_EXECUTIVE)
    db.add_all([engagement, user])
    db.commit()
    db.refresh(engagement)
    assert isinstance(engagement.id, uuid.UUID)
    assert engagement.health == Health.ON_TRACK
    assert engagement.progress_pct == 0
    assert engagement.executive_summary == ""
    assert user.is_active is True
    assert user.organization.slug == "cliente-demo"
