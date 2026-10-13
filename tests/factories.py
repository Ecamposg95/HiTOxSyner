from types import SimpleNamespace

from app.core.security import hash_password
from app.models.engagement import Engagement
from app.models.enums import OrganizationKind, Role
from app.models.organization import Organization
from app.models.user import User

PASSWORD = "pass1234"


def make_org(db, name, slug, kind=OrganizationKind.CLIENT):
    org = Organization(name=name, slug=slug, kind=kind)
    db.add(org)
    db.flush()
    return org


def make_engagement(db, org, name="Programa de transformación"):
    engagement = Engagement(organization_id=org.id, name=name)
    db.add(engagement)
    db.flush()
    return engagement


def make_user(db, org, email, role, full_name=None, password=PASSWORD, is_active=True):
    user = User(
        organization_id=org.id,
        email=email,
        full_name=full_name or email.split("@")[0],
        password_hash=hash_password(password),
        role=role,
        is_active=is_active,
    )
    db.add(user)
    db.flush()
    return user


def build_world(db):
    syner = make_org(db, "Syner", "syner", OrganizationKind.CONSULTANCY)
    admin = make_user(db, syner, "admin@syner.example", Role.SYNER_ADMIN, "Syner Admin")
    org_a = make_org(db, "Cliente A", "cliente-a")
    org_b = make_org(db, "Cliente B", "cliente-b")
    eng_a = make_engagement(db, org_a, "Programa A")
    eng_b = make_engagement(db, org_b, "Programa B")
    exec_a = make_user(db, org_a, "exec@a.example", Role.HITO_EXECUTIVE, "Exec A")
    collab_a = make_user(db, org_a, "collab@a.example", Role.HITO_COLLABORATOR, "Collab A")
    exec_b = make_user(db, org_b, "exec@b.example", Role.HITO_EXECUTIVE, "Exec B")
    collab_b = make_user(db, org_b, "collab@b.example", Role.HITO_COLLABORATOR, "Collab B")
    db.commit()
    for obj in (syner, admin, org_a, org_b, eng_a, eng_b, exec_a, collab_a, exec_b, collab_b):
        db.refresh(obj)
    return SimpleNamespace(
        syner=syner, admin=admin, org_a=org_a, org_b=org_b, eng_a=eng_a, eng_b=eng_b,
        exec_a=exec_a, collab_a=collab_a, exec_b=exec_b, collab_b=collab_b,
    )


def login(client, email, password=PASSWORD):
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
