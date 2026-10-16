from datetime import date

from tests.factories import login

DECISION = {"title": "Adoptar plataforma única de conciliación", "context": "Hoy hay tres herramientas.", "alternatives": "A) Mantener. B) Consolidar.", "syner_recommendation": "Consolidar en 90 días.", "owner_name": "Dirección de Operaciones", "impact": "Alto en costo operativo"}
MEETING = {"title": "Comité #2", "held_on": "2026-10-21T16:00:00Z"}


def test_syner_creates_decision_with_defaults_and_logs_activity(client, world):
    admin = login(client, "admin@syner.example")
    response = client.post(f"/api/engagements/{world.eng_a.id}/decisions", headers=admin, json=DECISION)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "Proposed"
    assert body["decided_on"] is None
    assert body["final_decision"] == ""
    assert body["initiative_id"] is None and body["meeting_id"] is None
    activity = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=admin).json()["items"][0]
    assert activity["summary"] == 'Syner Admin created Decision "Adoptar plataforma única de conciliación"'


def test_client_roles_cannot_create_decisions(client, world):
    for email in ("exec@a.example", "collab@a.example"):
        assert client.post(f"/api/engagements/{world.eng_a.id}/decisions", headers=login(client, email), json=DECISION).status_code == 403


def test_executive_approves_and_decided_on_is_set(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/decisions", headers=admin, json=DECISION).json()
    exec_a = login(client, "exec@a.example")
    response = client.patch(f"/api/decisions/{created['id']}", headers=exec_a, json={"status": "Approved"})
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "Approved"
    assert response.json()["decided_on"] == date.today().isoformat()
    activity = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=exec_a).json()["items"][0]
    assert activity["action"] == "status_changed"
    assert activity["summary"] == 'Exec A updated Decision "Adoptar plataforma única de conciliación" from Proposed to Approved'
    deferred = client.patch(f"/api/decisions/{created['id']}", headers=exec_a, json={"status": "Deferred"})
    assert deferred.status_code == 200 and deferred.json()["decided_on"] == date.today().isoformat()


def test_executive_can_only_resolve_status_and_nothing_else(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/decisions", headers=admin, json=DECISION).json()
    exec_a = login(client, "exec@a.example")
    assert client.patch(f"/api/decisions/{created['id']}", headers=exec_a, json={"status": "Approved", "title": "Otro"}).status_code == 403
    assert client.patch(f"/api/decisions/{created['id']}", headers=exec_a, json={"status": "Under Review"}).status_code == 403
    assert client.patch(f"/api/decisions/{created['id']}", headers=exec_a, json={"final_decision": "x"}).status_code == 403
    assert client.patch(f"/api/decisions/{created['id']}", headers=exec_a, json={}).status_code == 403
    unchanged = client.get(f"/api/decisions/{created['id']}", headers=exec_a).json()
    assert unchanged["status"] == "Proposed" and unchanged["title"] == DECISION["title"]
    assert client.patch(f"/api/decisions/{created['id']}", headers=login(client, "collab@a.example"), json={"status": "Approved"}).status_code == 403


def test_syner_sets_decided_on_explicitly_and_it_is_not_overwritten(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/decisions", headers=admin, json=DECISION).json()
    response = client.patch(f"/api/decisions/{created['id']}", headers=admin, json={"status": "Rejected", "decided_on": "2026-10-01", "final_decision": "No por ahora."})
    assert response.status_code == 200
    assert response.json()["decided_on"] == "2026-10-01"
    assert response.json()["final_decision"] == "No por ahora."
    assert client.patch(f"/api/decisions/{created['id']}", headers=admin, json={"title": None}).status_code == 422
    cleared = client.patch(f"/api/decisions/{created['id']}", headers=admin, json={"decided_on": None})
    assert cleared.status_code == 200 and cleared.json()["decided_on"] is None


def test_decisions_isolated_by_organization(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/decisions", headers=admin, json=DECISION).json()
    client.post(f"/api/engagements/{world.eng_b.id}/decisions", headers=admin, json={**DECISION, "title": "De B"})
    assert client.get(f"/api/engagements/{world.eng_a.id}/decisions", headers=login(client, "collab@a.example")).json()["total"] == 1
    assert client.get(f"/api/decisions/{created['id']}", headers=login(client, "exec@b.example")).status_code == 404
    assert client.patch(f"/api/decisions/{created['id']}", headers=login(client, "exec@b.example"), json={"status": "Approved"}).status_code == 404
    assert client.get(f"/api/engagements/{world.eng_a.id}/decisions", headers=login(client, "exec@b.example")).status_code == 404


def test_links_must_belong_to_engagement(client, world):
    admin = login(client, "admin@syner.example")
    other_initiative = client.post(f"/api/engagements/{world.eng_b.id}/initiatives", headers=admin, json={"name": "De B"}).json()
    other_meeting = client.post(f"/api/engagements/{world.eng_b.id}/meetings", headers=admin, json=MEETING).json()
    base = f"/api/engagements/{world.eng_a.id}/decisions"
    assert client.post(base, headers=admin, json={**DECISION, "initiative_id": other_initiative["id"]}).status_code == 422
    assert client.post(base, headers=admin, json={**DECISION, "meeting_id": other_meeting["id"]}).status_code == 422
    created = client.post(base, headers=admin, json=DECISION).json()
    assert client.patch(f"/api/decisions/{created['id']}", headers=admin, json={"initiative_id": other_initiative["id"]}).status_code == 422


def test_dashboard_counts_and_lists_decisions_required(client, world):
    admin = login(client, "admin@syner.example")
    base = f"/api/engagements/{world.eng_a.id}/decisions"
    client.post(base, headers=admin, json={**DECISION, "title": "Propuesta"})
    client.post(base, headers=admin, json={**DECISION, "title": "En revisión", "status": "Under Review"})
    client.post(base, headers=admin, json={**DECISION, "title": "Aprobada", "status": "Approved"})
    body = client.get(f"/api/engagements/{world.eng_a.id}/dashboard", headers=login(client, "exec@a.example")).json()
    assert body["tiles"]["decisions_required"] == 2
    assert {d["title"] for d in body["decisions_required"]} == {"Propuesta", "En revisión"}
    assert client.get(base, headers=admin, params={"status": "Approved"}).json()["total"] == 1


def test_meeting_detail_aggregates_decisions_and_actions(client, world):
    admin = login(client, "admin@syner.example")
    meeting = client.post(f"/api/engagements/{world.eng_a.id}/meetings", headers=admin, json=MEETING).json()
    decision = client.post(f"/api/meetings/{meeting['id']}/decisions", headers=admin, json=DECISION)
    assert decision.status_code == 201, decision.text
    assert decision.json()["meeting_id"] == meeting["id"]
    activity = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=admin).json()["items"][0]
    assert activity["summary"] == 'Syner Admin created Decision "Adoptar plataforma única de conciliación" from Meeting "Comité #2"'
    client.post(f"/api/meetings/{meeting['id']}/actions", headers=admin, json={"title": "Acción de reunión"})
    client.post(f"/api/engagements/{world.eng_a.id}/decisions", headers=admin, json={**DECISION, "title": "Suelta"})
    detail = client.get(f"/api/meetings/{meeting['id']}/detail", headers=login(client, "collab@a.example"))
    assert detail.status_code == 200
    body = detail.json()
    assert body["meeting"]["id"] == meeting["id"]
    assert [d["title"] for d in body["decisions"]] == [DECISION["title"]]
    assert [a["title"] for a in body["actions"]] == ["Acción de reunión"]
    assert client.get(f"/api/meetings/{meeting['id']}/detail", headers=login(client, "exec@b.example")).status_code == 404
    assert client.post(f"/api/meetings/{meeting['id']}/decisions", headers=login(client, "exec@a.example"), json=DECISION).status_code == 403


def test_initiative_detail_includes_decisions(client, world):
    admin = login(client, "admin@syner.example")
    initiative = client.post(f"/api/engagements/{world.eng_a.id}/initiatives", headers=admin, json={"name": "Automatización"}).json()
    client.post(f"/api/engagements/{world.eng_a.id}/decisions", headers=admin, json={**DECISION, "initiative_id": initiative["id"]})
    client.post(f"/api/engagements/{world.eng_a.id}/decisions", headers=admin, json={**DECISION, "title": "Suelta"})
    detail = client.get(f"/api/initiatives/{initiative['id']}/detail", headers=login(client, "exec@a.example")).json()
    assert [d["title"] for d in detail["decisions"]] == [DECISION["title"]]
