from tests.factories import login

ACTION = {"title": "Levantar inventario de hojas de cálculo", "organization_side": "CLIENT", "priority": "High", "due_date": "2026-10-30"}


def _initiative(client, world):
    admin = login(client, "admin@syner.example")
    return admin, client.post(f"/api/engagements/{world.eng_a.id}/initiatives", headers=admin, json={"name": "Automatización"}).json()


def test_syner_creates_action_linked_to_initiative_and_owner(client, world):
    admin, initiative = _initiative(client, world)
    payload = {**ACTION, "initiative_id": initiative["id"], "owner_user_id": str(world.collab_a.id)}
    response = client.post(f"/api/engagements/{world.eng_a.id}/actions", headers=admin, json=payload)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "Open"
    assert body["owner_name"] == "Collab A"
    assert body["initiative_id"] == initiative["id"]


def test_client_roles_cannot_create_actions(client, world):
    for email in ("exec@a.example", "collab@a.example"):
        assert client.post(f"/api/engagements/{world.eng_a.id}/actions", headers=login(client, email), json=ACTION).status_code == 403


def test_collaborator_updates_only_own_actions_and_only_status_evidence(client, world):
    admin = login(client, "admin@syner.example")
    mine = client.post(f"/api/engagements/{world.eng_a.id}/actions", headers=admin, json={**ACTION, "owner_user_id": str(world.collab_a.id)}).json()
    other = client.post(f"/api/engagements/{world.eng_a.id}/actions", headers=admin, json={**ACTION, "title": "Otra"}).json()
    collab = login(client, "collab@a.example")
    response = client.patch(f"/api/actions/{mine['id']}", headers=collab, json={"status": "In Progress", "evidence": "Inventario iniciado", "title": "Hackeado"})
    assert response.status_code == 200
    assert response.json()["status"] == "In Progress"
    assert response.json()["evidence"] == "Inventario iniciado"
    assert response.json()["title"] == ACTION["title"]
    assert client.patch(f"/api/actions/{other['id']}", headers=collab, json={"status": "Completed"}).status_code == 403
    assert client.patch(f"/api/actions/{mine['id']}", headers=login(client, "exec@a.example"), json={"status": "Completed"}).status_code == 403


def test_my_actions_filter(client, world):
    admin = login(client, "admin@syner.example")
    client.post(f"/api/engagements/{world.eng_a.id}/actions", headers=admin, json={**ACTION, "owner_user_id": str(world.collab_a.id)})
    client.post(f"/api/engagements/{world.eng_a.id}/actions", headers=admin, json={**ACTION, "title": "Otra"})
    collab = login(client, "collab@a.example")
    assert client.get(f"/api/engagements/{world.eng_a.id}/actions", headers=collab).json()["total"] == 2
    mine = client.get(f"/api/engagements/{world.eng_a.id}/actions", headers=collab, params={"mine": "true"}).json()
    assert mine["total"] == 1 and mine["items"][0]["owner_user_id"] == str(world.collab_a.id)


def test_actions_isolated_by_organization(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/actions", headers=admin, json=ACTION).json()
    assert client.patch(f"/api/actions/{created['id']}", headers=login(client, "collab@b.example"), json={"status": "Completed"}).status_code == 404
    assert client.get(f"/api/engagements/{world.eng_a.id}/actions", headers=login(client, "exec@b.example")).status_code == 404


def test_explicit_null_rules_on_update(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/actions", headers=admin, json=ACTION).json()
    assert client.patch(f"/api/actions/{created['id']}", headers=admin, json={"status": None}).status_code == 422
    cleared = client.patch(f"/api/actions/{created['id']}", headers=admin, json={"due_date": None})
    assert cleared.status_code == 200 and cleared.json()["due_date"] is None


def test_status_change_logs_activity(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/actions", headers=admin, json=ACTION).json()
    client.patch(f"/api/actions/{created['id']}", headers=admin, json={"status": "Blocked"})
    activity = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=admin).json()["items"][0]
    assert activity["summary"] == f'Syner Admin updated Action "{ACTION["title"]}" from Open to Blocked'


def test_initiative_detail_aggregates_related_entities(client, world):
    admin, initiative = _initiative(client, world)
    finding = client.post(f"/api/engagements/{world.eng_a.id}/findings", headers=admin, json={"title": "Hallazgo origen"}).json()
    converted = client.post(f"/api/findings/{finding['id']}/convert", headers=admin).json()
    client.post(f"/api/engagements/{world.eng_a.id}/actions", headers=admin, json={**ACTION, "initiative_id": converted["id"]})
    detail = client.get(f"/api/initiatives/{converted['id']}/detail", headers=login(client, "exec@a.example"))
    assert detail.status_code == 200
    body = detail.json()
    assert body["initiative"]["id"] == converted["id"]
    assert [f["id"] for f in body["findings"]] == [finding["id"]]
    assert len(body["actions"]) == 1
    assert any(a["entity_id"] == converted["id"] or a["entity_id"] == finding["id"] for a in body["activity"])
    assert client.get(f"/api/initiatives/{initiative['id']}/detail", headers=login(client, "exec@b.example")).status_code == 404


def test_links_must_belong_to_engagement(client, world):
    admin = login(client, "admin@syner.example")
    other_initiative = client.post(f"/api/engagements/{world.eng_b.id}/initiatives", headers=admin, json={"name": "De B"}).json()
    base = f"/api/engagements/{world.eng_a.id}/actions"
    assert client.post(base, headers=admin, json={**ACTION, "initiative_id": other_initiative["id"]}).status_code == 422
    assert client.post(base, headers=admin, json={**ACTION, "owner_user_id": str(world.collab_b.id)}).status_code == 422
    syner_owned = client.post(base, headers=admin, json={**ACTION, "owner_user_id": str(world.admin.id)})
    assert syner_owned.status_code == 201 and syner_owned.json()["owner_name"] == "Syner Admin"
    created = client.post(base, headers=admin, json=ACTION).json()
    assert client.patch(f"/api/actions/{created['id']}", headers=admin, json={"initiative_id": other_initiative["id"]}).status_code == 422
    assert client.patch(f"/api/actions/{created['id']}", headers=admin, json={"owner_user_id": str(world.exec_b.id)}).status_code == 422
