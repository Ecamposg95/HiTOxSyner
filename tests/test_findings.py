from tests.factories import login

PAYLOAD = {
    "title": "Conciliación manual diaria",
    "description": "El cierre diario depende de hojas de cálculo.",
    "type": "Quick Win",
    "area": "Operaciones",
    "impact": "High",
    "severity": "Medium",
    "recommendation": "Automatizar la conciliación.",
}


def test_syner_creates_finding_and_logs_activity(client, world):
    headers = login(client, "admin@syner.example")
    response = client.post(f"/api/engagements/{world.eng_a.id}/findings", headers=headers, json=PAYLOAD)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "New"
    assert body["type"] == "Quick Win"
    assert body["engagement_id"] == str(world.eng_a.id)
    assert body["initiative_id"] is None
    activity = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=headers).json()
    assert activity["items"][0]["summary"] == 'Syner Admin created Finding "Conciliación manual diaria"'


def test_client_roles_cannot_create_findings(client, world):
    for email in ("exec@a.example", "collab@a.example"):
        response = client.post(f"/api/engagements/{world.eng_a.id}/findings", headers=login(client, email), json=PAYLOAD)
        assert response.status_code == 403


def test_findings_are_isolated_by_organization(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/findings", headers=admin, json=PAYLOAD).json()
    client.post(f"/api/engagements/{world.eng_b.id}/findings", headers=admin, json={**PAYLOAD, "title": "De B"})
    listing = client.get(f"/api/engagements/{world.eng_a.id}/findings", headers=login(client, "collab@a.example")).json()
    assert listing["total"] == 1
    assert listing["items"][0]["title"] == "Conciliación manual diaria"
    assert client.get(f"/api/findings/{created['id']}", headers=login(client, "exec@b.example")).status_code == 404
    assert client.get(f"/api/engagements/{world.eng_b.id}/findings", headers=login(client, "exec@a.example")).status_code == 404


def test_status_change_logs_before_and_after(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/findings", headers=admin, json=PAYLOAD).json()
    response = client.patch(f"/api/findings/{created['id']}", headers=admin, json={"status": "Validated"})
    assert response.status_code == 200
    assert response.json()["status"] == "Validated"
    activity = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=admin).json()["items"][0]
    assert activity["action"] == "status_changed"
    assert activity["summary"] == 'Syner Admin updated Finding "Conciliación manual diaria" from New to Validated'
    assert activity["changes"] == [{"field": "status", "before": "New", "after": "Validated"}]


def test_list_filters_by_status_and_type(client, world):
    admin = login(client, "admin@syner.example")
    client.post(f"/api/engagements/{world.eng_a.id}/findings", headers=admin, json=PAYLOAD)
    client.post(f"/api/engagements/{world.eng_a.id}/findings", headers=admin, json={**PAYLOAD, "title": "Otro", "type": "Gap"})
    by_type = client.get(f"/api/engagements/{world.eng_a.id}/findings", headers=admin, params={"type": "Gap"}).json()
    assert by_type["total"] == 1 and by_type["items"][0]["title"] == "Otro"
    by_status = client.get(f"/api/engagements/{world.eng_a.id}/findings", headers=admin, params={"status": "Closed"}).json()
    assert by_status["total"] == 0


def test_title_is_required_and_limited(client, world):
    admin = login(client, "admin@syner.example")
    assert client.post(f"/api/engagements/{world.eng_a.id}/findings", headers=admin, json={}).status_code == 422
    assert client.post(f"/api/engagements/{world.eng_a.id}/findings", headers=admin, json={"title": "x" * 201}).status_code == 422


def test_explicit_null_on_required_field_is_422_but_nullable_is_allowed(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/findings", headers=admin, json=PAYLOAD).json()
    assert client.patch(f"/api/findings/{created['id']}", headers=admin, json={"title": None}).status_code == 422
    assert client.patch(f"/api/findings/{created['id']}", headers=admin, json={"syner_owner_id": None}).status_code == 200


def test_syner_owner_must_be_syner_user(client, world):
    headers = login(client, "admin@syner.example")
    url = f"/api/engagements/{world.eng_a.id}/findings"
    bad = client.post(url, headers=headers, json={**PAYLOAD, "syner_owner_id": str(world.exec_a.id)})
    assert bad.status_code == 422
    ok = client.post(url, headers=headers, json={**PAYLOAD, "syner_owner_id": str(world.admin.id)})
    assert ok.status_code == 201, ok.text
