from sqlalchemy import func, select

from app.models.action import Action
from app.models.comment import Comment
from app.models.decision import Decision
from app.models.document import Document, DocumentLink
from app.models.finding import Finding
from app.models.initiative import Initiative
from app.models.meeting import Meeting
from app.models.milestone import Milestone
from app.models.user import User
from app.seed import seed


def _count(db, model):
    return db.scalar(select(func.count()).select_from(model))


def test_seed_is_idempotent_and_creates_demo_data(db, client):
    seed(db)
    seed(db)
    assert _count(db, User) == 3
    assert _count(db, Finding) == 5
    assert _count(db, Initiative) == 4
    assert _count(db, Action) == 8
    assert _count(db, Milestone) == 6
    assert _count(db, Meeting) == 3
    assert _count(db, Decision) == 3
    assert _count(db, Document) == 5
    assert _count(db, DocumentLink) == 3
    assert _count(db, Comment) == 2
    titles = list(db.scalars(select(Finding.title))) + list(db.scalars(select(Milestone.name))) + list(db.scalars(select(Document.name)))
    assert all(t.startswith("[Demo]") for t in titles)
    assert db.scalar(select(func.count()).select_from(Document).where(Document.internal_only.is_(True))) == 1
    response = client.post("/api/auth/login", json={"email": "admin@syner.demo", "password": "syner-demo"})
    assert response.status_code == 200
