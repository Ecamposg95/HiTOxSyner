from datetime import datetime, timezone

from tests.factories import login

MEETING = {"title": "Comité de transformación #1", "held_on": "2026-10-20T16:00:00Z", "participants": "Dirección, Syner", "objective": "Validar diagnóstico", "summary": "Se validó el diagnóstico.", "discussion": "Se discutieron prioridades.", "next_steps": "Preparar roadmap."}


def test_syner_creates_and_updates_meeting(client, world):
    admin = login(client, "admin@syner.example")
    response = client.post(f"/api/engagements/{world.eng_a.id}/meetings", headers=admin, json=MEETING)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["title"] == MEETING["title"]
    # Postgres devuelve la hora en la zona de la sesión (puede no ser UTC): comparar instantes, no texto.
    assert datetime.fromisoformat(body["held_on"]) == datetime(2026, 10, 20, 16, 0, tzinfo=timezone.utc)
    activity = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=admin).json()["items"][0]
    assert activity["summary"] == 'Syner Admin created Meeting "Comité de transformación #1"'
    updated = client.patch(f"/api/meetings/{body['id']}", headers=admin, json={"next_steps": "Roadmap listo."})
    assert updated.status_code == 200 and updated.json()["next_steps"] == "Roadmap listo."
    assert client.patch(f"/api/meetings/{body['id']}", headers=admin, json={"held_on": None}).status_code == 422


def test_held_on_is_required(client, world):
    admin = login(client, "admin@syner.example")
    assert client.post(f"/api/engagements/{world.eng_a.id}/meetings", headers=admin, json={"title": "Sin fecha"}).status_code == 422


def test_list_orders_by_held_on_desc(client, world):
    admin = login(client, "admin@syner.example")
    base = f"/api/engagements/{world.eng_a.id}/meetings"
    client.post(base, headers=admin, json={**MEETING, "title": "Vieja", "held_on": "2026-09-01T10:00:00Z"})
    client.post(base, headers=admin, json={**MEETING, "title": "Nueva", "held_on": "2026-10-01T10:00:00Z"})
    listing = client.get(base, headers=login(client, "collab@a.example")).json()
    assert [m["title"] for m in listing["items"]] == ["Nueva", "Vieja"]


def test_client_roles_cannot_write_meetings(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/meetings", headers=admin, json=MEETING).json()
    for email in ("exec@a.example", "collab@a.example"):
        headers = login(client, email)
        assert client.post(f"/api/engagements/{world.eng_a.id}/meetings", headers=headers, json=MEETING).status_code == 403
        assert client.patch(f"/api/meetings/{created['id']}", headers=headers, json={"summary": "x"}).status_code == 403
        assert client.post(f"/api/meetings/{created['id']}/actions", headers=headers, json={"title": "x"}).status_code == 403
        assert client.get(f"/api/meetings/{created['id']}", headers=headers).status_code == 200


def test_meetings_isolated_by_organization(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/meetings", headers=admin, json=MEETING).json()
    client.post(f"/api/engagements/{world.eng_b.id}/meetings", headers=admin, json={**MEETING, "title": "De B"})
    assert client.get(f"/api/engagements/{world.eng_a.id}/meetings", headers=login(client, "exec@a.example")).json()["total"] == 1
    assert client.get(f"/api/meetings/{created['id']}", headers=login(client, "exec@b.example")).status_code == 404
    assert client.get(f"/api/engagements/{world.eng_a.id}/meetings", headers=login(client, "collab@b.example")).status_code == 404


def test_action_created_from_meeting_carries_meeting_id_and_activity_mentions_meeting(client, world):
    admin = login(client, "admin@syner.example")
    meeting = client.post(f"/api/engagements/{world.eng_a.id}/meetings", headers=admin, json=MEETING).json()
    response = client.post(f"/api/meetings/{meeting['id']}/actions", headers=admin, json={"title": "Enviar roadmap", "owner_user_id": str(world.collab_a.id), "due_date": "2026-10-27"})
    assert response.status_code == 201, response.text
    action = response.json()
    assert action["meeting_id"] == meeting["id"]
    assert action["owner_name"] == "Collab A"
    activity = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=admin).json()["items"][0]
    assert activity["summary"] == 'Syner Admin created Action "Enviar roadmap" from Meeting "Comité de transformación #1"'
    listing = client.get(f"/api/engagements/{world.eng_a.id}/actions", headers=admin, params={"meeting_id": meeting["id"]}).json()
    assert listing["total"] == 1 and listing["items"][0]["id"] == action["id"]


def test_action_meeting_id_must_belong_to_engagement(client, world):
    admin = login(client, "admin@syner.example")
    other = client.post(f"/api/engagements/{world.eng_b.id}/meetings", headers=admin, json=MEETING).json()
    base = f"/api/engagements/{world.eng_a.id}/actions"
    assert client.post(base, headers=admin, json={"title": "x", "meeting_id": other["id"]}).status_code == 422
    created = client.post(base, headers=admin, json={"title": "x"}).json()
    assert client.patch(f"/api/actions/{created['id']}", headers=admin, json={"meeting_id": other["id"]}).status_code == 422
