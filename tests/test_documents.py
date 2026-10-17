import uuid

from tests.factories import login

DOCUMENT = {"name": "Diagnóstico operativo v1", "category": "Assessment", "version": "1.0", "url": "https://drive.example.com/d/abc", "doc_date": "2026-10-10", "tags": ["diagnóstico", "operaciones"]}


def _admin_and_initiative(client, world):
    admin = login(client, "admin@syner.example")
    return admin, client.post(f"/api/engagements/{world.eng_a.id}/initiatives", headers=admin, json={"name": "Automatización"}).json()


def test_syner_creates_document_with_uploader_tags_and_activity(client, world):
    admin = login(client, "admin@syner.example")
    response = client.post(f"/api/engagements/{world.eng_a.id}/documents", headers=admin, json=DOCUMENT)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["uploader_id"] == str(world.admin.id)
    assert body["tags"] == ["diagnóstico", "operaciones"]
    assert body["internal_only"] is False
    assert body["links"] == []
    activity = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=admin).json()["items"][0]
    assert activity["summary"] == 'Syner Admin created Document "Diagnóstico operativo v1"'
    updated = client.patch(f"/api/documents/{body['id']}", headers=admin, json={"version": "1.1", "tags": []})
    assert updated.status_code == 200 and updated.json()["version"] == "1.1" and updated.json()["tags"] == []
    assert client.patch(f"/api/documents/{body['id']}", headers=admin, json={"name": None}).status_code == 422
    assert client.post(f"/api/engagements/{world.eng_a.id}/documents", headers=admin, json={**DOCUMENT, "tags": ["x"] * 21}).status_code == 422


def test_client_roles_cannot_write_documents(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(f"/api/engagements/{world.eng_a.id}/documents", headers=admin, json=DOCUMENT).json()
    for email in ("exec@a.example", "collab@a.example"):
        headers = login(client, email)
        assert client.post(f"/api/engagements/{world.eng_a.id}/documents", headers=headers, json=DOCUMENT).status_code == 403
        assert client.patch(f"/api/documents/{created['id']}", headers=headers, json={"version": "2"}).status_code == 403
        assert client.post(f"/api/documents/{created['id']}/links", headers=headers, json={"entity_type": "initiative", "entity_id": str(uuid.uuid4())}).status_code == 403


def test_internal_only_documents_are_visible_only_to_syner(client, world):
    admin, initiative = _admin_and_initiative(client, world)
    base = f"/api/engagements/{world.eng_a.id}/documents"
    public = client.post(base, headers=admin, json=DOCUMENT).json()
    internal = client.post(base, headers=admin, json={**DOCUMENT, "name": "Notas internas Syner", "internal_only": True}).json()
    for doc in (public, internal):
        assert client.post(f"/api/documents/{doc['id']}/links", headers=admin, json={"entity_type": "initiative", "entity_id": initiative["id"]}).status_code == 201
    collab = login(client, "collab@a.example")
    listing = client.get(base, headers=collab).json()
    assert [d["name"] for d in listing["items"]] == [DOCUMENT["name"]] and listing["total"] == 1
    assert client.get(f"/api/documents/{internal['id']}", headers=collab).status_code == 404
    assert client.get(f"/api/documents/{public['id']}", headers=collab).status_code == 200
    detail = client.get(f"/api/initiatives/{initiative['id']}/detail", headers=collab).json()
    assert [d["name"] for d in detail["documents"]] == [DOCUMENT["name"]]
    exec_a = login(client, "exec@a.example")
    assert client.get(base, headers=exec_a).json()["total"] == 1
    assert client.get(f"/api/documents/{internal['id']}", headers=exec_a).status_code == 404
    assert [d["name"] for d in client.get(f"/api/initiatives/{initiative['id']}/detail", headers=exec_a).json()["documents"]] == [DOCUMENT["name"]]
    assert client.get(base, headers=admin).json()["total"] == 2
    assert client.get(f"/api/documents/{internal['id']}", headers=admin).status_code == 200
    assert len(client.get(f"/api/initiatives/{initiative['id']}/detail", headers=admin).json()["documents"]) == 2


def test_links_are_unique_validated_and_removable(client, world):
    admin, initiative = _admin_and_initiative(client, world)
    base = f"/api/engagements/{world.eng_a.id}/documents"
    doc = client.post(base, headers=admin, json=DOCUMENT).json()
    other_doc = client.post(base, headers=admin, json={**DOCUMENT, "name": "Otro"}).json()
    link = client.post(f"/api/documents/{doc['id']}/links", headers=admin, json={"entity_type": "initiative", "entity_id": initiative["id"]})
    assert link.status_code == 201, link.text
    assert link.json()["entity_type"] == "initiative"
    activity = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=admin).json()["items"][0]
    assert activity["summary"] == 'Syner Admin linked Document "Diagnóstico operativo v1" to Initiative "Automatización"'
    assert client.post(f"/api/documents/{doc['id']}/links", headers=admin, json={"entity_type": "initiative", "entity_id": initiative["id"]}).status_code == 409
    foreign = client.post(f"/api/engagements/{world.eng_b.id}/initiatives", headers=admin, json={"name": "De B"}).json()
    assert client.post(f"/api/documents/{doc['id']}/links", headers=admin, json={"entity_type": "initiative", "entity_id": foreign["id"]}).status_code == 422
    assert client.post(f"/api/documents/{doc['id']}/links", headers=admin, json={"entity_type": "unicorn", "entity_id": initiative["id"]}).status_code == 422
    other_link = client.post(f"/api/documents/{other_doc['id']}/links", headers=admin, json={"entity_type": "initiative", "entity_id": initiative["id"]}).json()
    assert client.delete(f"/api/documents/{doc['id']}/links/{other_link['id']}", headers=admin).status_code == 404
    assert len(client.get(f"/api/documents/{other_doc['id']}", headers=admin).json()["links"]) == 1
    assert client.delete(f"/api/documents/{doc['id']}/links/{link.json()['id']}", headers=admin).status_code == 204
    assert client.get(f"/api/documents/{doc['id']}", headers=admin).json()["links"] == []
    assert [d["name"] for d in client.get(f"/api/initiatives/{initiative['id']}/detail", headers=admin).json()["documents"]] == ["Otro"]


def test_documents_filter_by_category_and_are_isolated(client, world):
    admin = login(client, "admin@syner.example")
    base = f"/api/engagements/{world.eng_a.id}/documents"
    created = client.post(base, headers=admin, json=DOCUMENT).json()
    client.post(base, headers=admin, json={**DOCUMENT, "name": "Minuta", "category": "Meetings"})
    client.post(f"/api/engagements/{world.eng_b.id}/documents", headers=admin, json={**DOCUMENT, "name": "De B"})
    assert client.get(base, headers=admin, params={"category": "Meetings"}).json()["items"][0]["name"] == "Minuta"
    assert client.get(base, headers=login(client, "exec@a.example")).json()["total"] == 2
    assert client.get(f"/api/documents/{created['id']}", headers=login(client, "exec@b.example")).status_code == 404
    assert client.get(base, headers=login(client, "collab@b.example")).status_code == 404


def test_internal_document_activity_is_hidden_from_collaborators(client, world):
    admin, initiative = _admin_and_initiative(client, world)
    base = f"/api/engagements/{world.eng_a.id}/documents"
    internal = client.post(base, headers=admin, json={**DOCUMENT, "name": "Notas internas Syner", "internal_only": True}).json()
    client.post(f"/api/documents/{internal['id']}/links", headers=admin, json={"entity_type": "initiative", "entity_id": initiative["id"]})
    client.post(base, headers=admin, json=DOCUMENT)
    collab = login(client, "collab@a.example")
    feed = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=collab).json()
    assert not any("Notas internas" in a["summary"] for a in feed["items"])
    assert any(a["summary"] == f'Syner Admin created Document "{DOCUMENT["name"]}"' for a in feed["items"])
    dashboard = client.get(f"/api/engagements/{world.eng_a.id}/dashboard", headers=collab).json()
    assert not any("Notas internas" in a["summary"] for a in dashboard["recent_activity"])
    exec_feed = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=login(client, "exec@a.example")).json()
    assert not any("Notas internas" in a["summary"] for a in exec_feed["items"])
    admin_feed = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=login(client, "admin@syner.example")).json()
    assert any("Notas internas" in a["summary"] for a in admin_feed["items"])
    # hidden rows: created internal Document + linked internal Document
    assert feed["total"] == admin_feed["total"] - 2
    assert exec_feed["total"] == admin_feed["total"] - 2


def test_toggling_internal_only_rewrites_activity_visibility(client, world):
    admin, initiative = _admin_and_initiative(client, world)
    base = f"/api/engagements/{world.eng_a.id}/documents"
    doc = client.post(base, headers=admin, json={**DOCUMENT, "name": "Antes público"}).json()
    client.post(f"/api/documents/{doc['id']}/links", headers=admin, json={"entity_type": "initiative", "entity_id": initiative["id"]})
    collab = login(client, "collab@a.example")
    assert any("Antes público" in a["summary"] for a in client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=collab).json()["items"])
    assert client.patch(f"/api/documents/{doc['id']}", headers=admin, json={"internal_only": True}).status_code == 200
    feed = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=collab).json()
    assert not any("Antes público" in a["summary"] for a in feed["items"])
    assert client.get(f"/api/documents/{doc['id']}", headers=collab).status_code == 404
    assert client.patch(f"/api/documents/{doc['id']}", headers=admin, json={"internal_only": False}).status_code == 200
    assert any("Antes público" in a["summary"] for a in client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=collab).json()["items"])
