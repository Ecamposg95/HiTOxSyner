from tests.factories import login


def test_syner_lists_all_engagements(client, world):
    headers = login(client, "admin@syner.example")
    response = client.get("/api/engagements", headers=headers)
    assert response.status_code == 200
    assert {e["name"] for e in response.json()} == {"Programa A", "Programa B"}


def test_client_user_lists_only_own_engagements(client, world):
    headers = login(client, "exec@a.example")
    names = {e["name"] for e in client.get("/api/engagements", headers=headers).json()}
    assert names == {"Programa A"}


def test_client_user_cannot_read_other_org_engagement(client, world):
    headers = login(client, "exec@b.example")
    assert client.get(f"/api/engagements/{world.eng_a.id}", headers=headers).status_code == 404


def test_syner_updates_summary_health_and_progress(client, world):
    headers = login(client, "admin@syner.example")
    response = client.patch(
        f"/api/engagements/{world.eng_a.id}",
        headers=headers,
        json={"executive_summary": "Situación actual: arranque.", "health": "Attention", "progress_pct": 15},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["health"] == "Attention"
    assert body["progress_pct"] == 15
    assert body["executive_summary"] == "Situación actual: arranque."


def test_executive_patch_own_engagement_is_403(client, world):
    headers = login(client, "exec@a.example")
    response = client.patch(f"/api/engagements/{world.eng_a.id}", headers=headers, json={"progress_pct": 50})
    assert response.status_code == 403


def test_progress_out_of_range_is_422(client, world):
    headers = login(client, "admin@syner.example")
    assert client.patch(f"/api/engagements/{world.eng_a.id}", headers=headers, json={"progress_pct": 101}).status_code == 422
    assert client.patch(f"/api/engagements/{world.eng_a.id}", headers=headers, json={"executive_summary": "x" * 2001}).status_code == 422


def test_syner_creates_client_user(client, world):
    headers = login(client, "admin@syner.example")
    payload = {"email": "Nuevo@A.example", "full_name": "Nuevo", "password": "password123", "role": "HITO_COLLABORATOR"}
    response = client.post(f"/api/engagements/{world.eng_a.id}/users", headers=headers, json=payload)
    assert response.status_code == 201
    assert response.json()["email"] == "nuevo@a.example"
    assert response.json()["organization_id"] == str(world.org_a.id)
    assert client.post(f"/api/engagements/{world.eng_a.id}/users", headers=headers, json=payload).status_code == 409
    assert login(client, "nuevo@a.example", "password123")


def test_cannot_create_syner_admin_inside_client_engagement(client, world):
    headers = login(client, "admin@syner.example")
    payload = {"email": "x@a.example", "full_name": "X", "password": "password123", "role": "SYNER_ADMIN"}
    assert client.post(f"/api/engagements/{world.eng_a.id}/users", headers=headers, json=payload).status_code == 422


def test_executive_cannot_manage_users(client, world):
    headers = login(client, "exec@a.example")
    assert client.get(f"/api/engagements/{world.eng_a.id}/users", headers=headers).status_code == 403


def test_syner_deactivates_user(client, world):
    headers = login(client, "admin@syner.example")
    response = client.patch(
        f"/api/engagements/{world.eng_a.id}/users/{world.collab_a.id}", headers=headers, json={"is_active": False}
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert client.patch(
        f"/api/engagements/{world.eng_a.id}/users/{world.exec_b.id}", headers=headers, json={"is_active": False}
    ).status_code == 404


def test_explicit_null_in_patch_is_422_unless_nullable(client, world):
    headers = login(client, "admin@syner.example")
    assert client.patch(f"/api/engagements/{world.eng_a.id}", headers=headers, json={"name": None}).status_code == 422
    cleared = client.patch(f"/api/engagements/{world.eng_a.id}", headers=headers, json={"subtitle": None})
    assert cleared.status_code == 200 and cleared.json()["subtitle"] is None
    user_url = f"/api/engagements/{world.eng_a.id}/users/{world.collab_a.id}"
    assert client.patch(user_url, headers=headers, json={"password": None}).status_code == 422
    assert client.patch(user_url, headers=headers, json={"role": None}).status_code == 422
