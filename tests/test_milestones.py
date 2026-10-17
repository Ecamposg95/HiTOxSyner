from datetime import date, timedelta

from tests.factories import login

MILESTONE = {"name": "Diagnóstico consolidado", "phase": "Diagnose", "due_date": "2026-11-15", "owner": "Equipo Syner", "deliverable": "Informe de diagnóstico"}


def _admin_and_initiative(client, world):
    admin = login(client, "admin@syner.example")
    initiative = client.post(f"/api/engagements/{world.eng_a.id}/initiatives", headers=admin, json={"name": "Automatización"}).json()
    return admin, initiative


def test_syner_creates_milestone_with_defaults_and_logs_activity(client, world):
    admin = login(client, "admin@syner.example")
    response = client.post(f"/api/engagements/{world.eng_a.id}/milestones", headers=admin, json=MILESTONE)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "Planned"
    assert body["phase"] == "Diagnose"
    assert body["initiative_id"] is None
    assert body["engagement_id"] == str(world.eng_a.id)
    activity = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=admin).json()["items"][0]
    assert activity["summary"] == 'Syner Admin created Milestone "Diagnóstico consolidado"'


def test_client_roles_cannot_write_milestones(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/milestones", headers=admin, json=MILESTONE).json()
    for email in ("exec@a.example", "collab@a.example"):
        headers = login(client, email)
        assert client.post(f"/api/engagements/{world.eng_a.id}/milestones", headers=headers, json=MILESTONE).status_code == 403
        assert client.patch(f"/api/milestones/{created['id']}", headers=headers, json={"status": "Done"}).status_code == 403
        assert client.get(f"/api/engagements/{world.eng_a.id}/milestones", headers=headers).json()["total"] == 1


def test_milestones_isolated_by_organization(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/milestones", headers=admin, json=MILESTONE).json()
    client.post(f"/api/engagements/{world.eng_b.id}/milestones", headers=admin, json={**MILESTONE, "name": "De B"})
    listing = client.get(f"/api/engagements/{world.eng_a.id}/milestones", headers=login(client, "exec@a.example")).json()
    assert listing["total"] == 1 and listing["items"][0]["name"] == MILESTONE["name"]
    assert client.get(f"/api/milestones/{created['id']}", headers=login(client, "exec@b.example")).status_code == 404
    assert client.get(f"/api/engagements/{world.eng_a.id}/milestones", headers=login(client, "collab@b.example")).status_code == 404


def test_initiative_must_belong_to_engagement(client, world):
    admin = login(client, "admin@syner.example")
    other = client.post(f"/api/engagements/{world.eng_b.id}/initiatives", headers=admin, json={"name": "De B"}).json()
    base = f"/api/engagements/{world.eng_a.id}/milestones"
    assert client.post(base, headers=admin, json={**MILESTONE, "initiative_id": other["id"]}).status_code == 422
    created = client.post(base, headers=admin, json=MILESTONE).json()
    assert client.patch(f"/api/milestones/{created['id']}", headers=admin, json={"initiative_id": other["id"]}).status_code == 422
    assert client.get(f"/api/milestones/{created['id']}", headers=admin).json()["initiative_id"] is None


def test_status_change_logs_before_and_after_and_null_rules(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/milestones", headers=admin, json=MILESTONE).json()
    response = client.patch(f"/api/milestones/{created['id']}", headers=admin, json={"status": "In Progress"})
    assert response.status_code == 200 and response.json()["status"] == "In Progress"
    activity = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=admin).json()["items"][0]
    assert activity["action"] == "status_changed"
    assert activity["summary"] == 'Syner Admin updated Milestone "Diagnóstico consolidado" from Planned to In Progress'
    assert client.patch(f"/api/milestones/{created['id']}", headers=admin, json={"name": None}).status_code == 422
    cleared = client.patch(f"/api/milestones/{created['id']}", headers=admin, json={"due_date": None})
    assert cleared.status_code == 200 and cleared.json()["due_date"] is None


def test_list_filters_by_phase_status_and_initiative(client, world):
    admin, initiative = _admin_and_initiative(client, world)
    base = f"/api/engagements/{world.eng_a.id}/milestones"
    client.post(base, headers=admin, json=MILESTONE)
    client.post(base, headers=admin, json={**MILESTONE, "name": "Piloto", "phase": "Execute", "status": "Done", "initiative_id": initiative["id"]})
    assert client.get(base, headers=admin, params={"phase": "Execute"}).json()["total"] == 1
    assert client.get(base, headers=admin, params={"status": "Planned"}).json()["items"][0]["name"] == MILESTONE["name"]
    assert client.get(base, headers=admin, params={"initiative_id": initiative["id"]}).json()["items"][0]["name"] == "Piloto"


def test_dashboard_roadmap_groups_by_phase_and_next_milestones_skip_done(client, world):
    admin = login(client, "admin@syner.example")
    base = f"/api/engagements/{world.eng_a.id}/milestones"
    today = date.today()
    client.post(base, headers=admin, json={"name": "Lejano", "phase": "Execute", "due_date": (today + timedelta(days=40)).isoformat()})
    client.post(base, headers=admin, json={"name": "Cercano", "phase": "Diagnose", "due_date": (today + timedelta(days=5)).isoformat()})
    client.post(base, headers=admin, json={"name": "Hecho", "phase": "Discover", "due_date": (today - timedelta(days=5)).isoformat(), "status": "Done"})
    client.post(base, headers=admin, json={"name": "Sin fecha", "phase": "Measure"})
    body = client.get(f"/api/engagements/{world.eng_a.id}/dashboard", headers=login(client, "exec@a.example")).json()
    phases = {p["phase"]: [m["name"] for m in p["milestones"]] for p in body["roadmap"]}
    assert list(phases) == ["Discover", "Diagnose", "Design", "Prioritize", "Execute", "Measure"]
    assert phases["Discover"] == ["Hecho"] and phases["Diagnose"] == ["Cercano"] and phases["Measure"] == ["Sin fecha"]
    assert [m["name"] for m in body["next_milestones"]] == ["Cercano", "Lejano"]


def test_initiative_detail_includes_milestones(client, world):
    admin, initiative = _admin_and_initiative(client, world)
    client.post(f"/api/engagements/{world.eng_a.id}/milestones", headers=admin, json={**MILESTONE, "initiative_id": initiative["id"]})
    client.post(f"/api/engagements/{world.eng_a.id}/milestones", headers=admin, json={**MILESTONE, "name": "Suelto"})
    detail = client.get(f"/api/initiatives/{initiative['id']}/detail", headers=login(client, "collab@a.example")).json()
    assert [m["name"] for m in detail["milestones"]] == [MILESTONE["name"]]
