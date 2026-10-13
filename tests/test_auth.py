from app.core.security import create_access_token
from tests.factories import PASSWORD, login, make_user
from app.models.enums import Role


def test_login_returns_token_and_sets_cookie(client, world):
    response = client.post("/api/auth/login", json={"email": "admin@syner.example", "password": PASSWORD})
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "admin@syner.example"
    assert body["user"]["role"] == "SYNER_ADMIN"
    assert body["user"]["organization_name"] == "Syner"
    assert "access_token" in response.cookies


def test_login_is_case_insensitive_on_email(client, world):
    response = client.post("/api/auth/login", json={"email": "ADMIN@Syner.example", "password": PASSWORD})
    assert response.status_code == 200


def test_login_rejects_wrong_password(client, world):
    response = client.post("/api/auth/login", json={"email": "admin@syner.example", "password": "nope"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Credenciales inválidas"}


def test_login_rejects_inactive_user(client, db, world):
    make_user(db, world.org_a, "off@a.example", Role.HITO_COLLABORATOR, is_active=False)
    db.commit()
    response = client.post("/api/auth/login", json={"email": "off@a.example", "password": PASSWORD})
    assert response.status_code == 401


def test_me_with_bearer(client, world):
    headers = login(client, "exec@a.example")
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["role"] == "HITO_EXECUTIVE"


def test_me_with_cookie_only(client, world):
    client.post("/api/auth/login", json={"email": "exec@a.example", "password": PASSWORD})
    response = client.get("/api/auth/me")
    assert response.status_code == 200


def test_me_without_credentials_is_401(client, world):
    assert client.get("/api/auth/me").status_code == 401


def test_me_with_expired_token_is_401(client, world):
    token = create_access_token(user_id=str(world.admin.id), organization_id=str(world.syner.id), role="SYNER_ADMIN", expires_hours=-1)
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or expired token"}


def test_me_for_deactivated_user_is_401(client, db, world):
    headers = login(client, "collab@a.example")
    world.collab_a.is_active = False
    db.commit()
    assert client.get("/api/auth/me", headers=headers).status_code == 401


def test_logout_clears_cookie(client, world):
    client.post("/api/auth/login", json={"email": "exec@a.example", "password": PASSWORD})
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").status_code == 401
