from sqlalchemy import delete, func, select

from app.models.action import Action
from app.models.comment import Comment
from app.models.decision import Decision
from app.models.document import Document, DocumentLink
from app.models.enums import DocumentCategory
from app.models.finding import Finding
from app.models.initiative import Initiative
from app.models.lab import ActionContract, ActionContractCta, Cta, LabSession, Participant, Pod
from app.models.meeting import Meeting
from app.models.milestone import Milestone
from app.models.user import User
from app.seed import ORION_DOCUMENTS, seed


def _count(db, model):
    return db.scalar(select(func.count()).select_from(model))


def _login(client, email, password):
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


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
    assert _count(db, Document) == 5 + len(ORION_DOCUMENTS)
    assert _count(db, DocumentLink) == 3
    assert _count(db, Comment) == 2
    assert _count(db, LabSession) == 4
    assert _count(db, Pod) == 4
    assert _count(db, Participant) == 20
    assert _count(db, Cta) == 8
    assert _count(db, ActionContract) == 2
    assert _count(db, ActionContractCta) == 3
    titles = (
        list(db.scalars(select(Finding.title))) + list(db.scalars(select(Milestone.name)))
        + list(db.scalars(select(Participant.full_name))) + list(db.scalars(select(Pod.name)))
    )
    assert all(t.startswith("[Demo]") for t in titles)
    names = list(db.scalars(select(Document.name)))
    assert sum(1 for n in names if n.startswith("[Demo]")) == 5
    orion = list(db.scalars(select(Document).where(Document.category == DocumentCategory.DELIVERABLES, Document.internal_only.is_(True))))
    assert {d.name for d in orion} == {name for name, _, _ in ORION_DOCUMENTS}
    assert all("orion" in d.tags and d.url == "" for d in orion)
    assert db.scalar(select(func.count()).select_from(Document).where(Document.internal_only.is_(True))) == 1 + len(ORION_DOCUMENTS)
    admin = _login(client, "admin@syner.demo", "syner-demo")
    engagement_id = client.get("/api/engagements", headers=admin).json()[0]["id"]
    assert client.get(f"/api/engagements/{engagement_id}/documents", headers=admin).json()["total"] == 5 + len(ORION_DOCUMENTS)
    exec_headers = _login(client, "exec@hito.demo", "exec-demo")
    assert client.get(f"/api/engagements/{engagement_id}/documents", headers=exec_headers).json()["total"] == 4
    summary = client.get(f"/api/engagements/{engagement_id}/lab/summary", headers=exec_headers).json()
    assert summary["cta_totals"]["total"] == 8 and summary["sessions_done"] == 2 and summary["active_contracts"] == 1


def test_seed_skips_demo_modules_when_engagement_has_real_initiatives(db, client):
    seed(db)
    real = db.scalar(select(Initiative).order_by(Initiative.created_at))
    real.name = "Iniciativa real del cliente"
    for model in (ActionContractCta, ActionContract, Cta, Participant, Pod, LabSession, Milestone):
        db.execute(delete(model))
    db.commit()
    seed(db)
    assert _count(db, Milestone) == 0
    assert _count(db, LabSession) == 0
    assert _count(db, Participant) == 0
    assert _count(db, Meeting) == 3
    assert _count(db, Document) == 5 + len(ORION_DOCUMENTS)
