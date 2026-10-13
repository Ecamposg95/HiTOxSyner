from tests.factories import login

INITIATIVE = {"name": "Automatización de conciliación", "objective": "Eliminar el cierre manual", "area": "Operaciones", "priority": "High"}
FINDING = {"title": "Conciliación manual diaria", "description": "Depende de Excel.", "area": "Operaciones", "impact": "High", "recommendation": "Automatizar."}


def test_syner_creates_and_updates_initiative(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/initiatives", headers=admin, json=INITIATIVE)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["status"] == "Discovery"
    assert body["progress_pct"] == 0
    updated = client.patch(f"/api/initiatives/{body['id']}", headers=admin, json={"status": "Design", "progress_pct": 20})
    assert updated.status_code == 200
    assert updated.json()["status"] == "Design"
    activity = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=admin).json()["items"][0]
    assert activity["summary"] == 'Syner Admin updated Initiative "Automatización de conciliación" from Discovery to Design'


def test_client_roles_cannot_write_initiatives(client, world):
    for email in ("exec@a.example", "collab@a.example"):
        assert client.post(f"/api/engagements/{world.eng_a.id}/initiatives", headers=login(client, email), json=INITIATIVE).status_code == 403


def test_initiatives_isolated_by_organization(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/initiatives", headers=admin, json=INITIATIVE).json()
    assert client.get(f"/api/initiatives/{created['id']}", headers=login(client, "exec@b.example")).status_code == 404
    listing = client.get(f"/api/engagements/{world.eng_a.id}/initiatives", headers=login(client, "exec@a.example")).json()
    assert listing["total"] == 1


def test_progress_out_of_range_is_422(client, world):
    admin = login(client, "admin@syner.example")
    assert client.post(f"/api/engagements/{world.eng_a.id}/initiatives", headers=admin, json={**INITIATIVE, "progress_pct": 120}).status_code == 422


def test_explicit_null_rules_on_update(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/initiatives", headers=admin, json={**INITIATIVE, "target_date": "2026-12-01"}).json()
    assert client.patch(f"/api/initiatives/{created['id']}", headers=admin, json={"name": None}).status_code == 422
    cleared = client.patch(f"/api/initiatives/{created['id']}", headers=admin, json={"target_date": None})
    assert cleared.status_code == 200 and cleared.json()["target_date"] is None


def test_convert_finding_creates_initiative_once(client, world):
    admin = login(client, "admin@syner.example")
    finding = client.post(f"/api/engagements/{world.eng_a.id}/findings", headers=admin, json=FINDING).json()
    response = client.post(f"/api/findings/{finding['id']}/convert", headers=admin)
    assert response.status_code == 201, response.text
    initiative = response.json()
    assert initiative["name"] == "Conciliación manual diaria"
    assert initiative["objective"] == "Automatizar."
    assert initiative["area"] == "Operaciones"
    assert initiative["priority"] == "High"
    assert initiative["status"] == "Discovery"
    refreshed = client.get(f"/api/findings/{finding['id']}", headers=admin).json()
    assert refreshed["status"] == "Converted to Initiative"
    assert refreshed["initiative_id"] == initiative["id"]
    assert client.post(f"/api/findings/{finding['id']}/convert", headers=admin).status_code == 409
    activity = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=admin).json()["items"][0]
    assert activity["action"] == "converted"
    assert activity["summary"] == 'Syner Admin converted Finding "Conciliación manual diaria" into Initiative "Conciliación manual diaria"'


def test_only_syner_can_convert(client, world):
    admin = login(client, "admin@syner.example")
    finding = client.post(f"/api/engagements/{world.eng_a.id}/findings", headers=admin, json=FINDING).json()
    assert client.post(f"/api/findings/{finding['id']}/convert", headers=login(client, "exec@a.example")).status_code == 403
