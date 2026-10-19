import uuid

import pytest

from tests.factories import login


def _initiative(client, world, engagement=None):
    admin = login(client, "admin@syner.example")
    eng = engagement or world.eng_a
    return admin, client.post(f"/api/engagements/{eng.id}/initiatives", headers=admin, json={"name": "Automatización"}).json()


@pytest.mark.parametrize("email", ["admin@syner.example", "exec@a.example", "collab@a.example"])
def test_every_role_can_comment_and_activity_targets_the_entity(client, world, email):
    _, initiative = _initiative(client, world)
    headers = login(client, email)
    response = client.post(f"/api/engagements/{world.eng_a.id}/comments", headers=headers, json={"entity_type": "initiative", "entity_id": initiative["id"], "body": "Revisemos alcance."})
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["body"] == "Revisemos alcance."
    assert body["author_name"] in ("Syner Admin", "Exec A", "Collab A")
    activity = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=headers, params={"entity_type": "initiative", "entity_id": initiative["id"]}).json()["items"][0]
    assert activity["action"] == "commented"
    assert activity["summary"] == f'{body["author_name"]} commented on Initiative "Automatización"'


def test_comments_list_in_chronological_order_for_the_entity(client, world):
    admin, initiative = _initiative(client, world)
    base = f"/api/engagements/{world.eng_a.id}/comments"
    client.post(base, headers=admin, json={"entity_type": "initiative", "entity_id": initiative["id"], "body": "Primero"})
    client.post(base, headers=admin, json={"entity_type": "initiative", "entity_id": initiative["id"], "body": "Segundo"})
    finding = client.post(f"/api/engagements/{world.eng_a.id}/findings", headers=admin, json={"title": "Otro"}).json()
    client.post(base, headers=admin, json={"entity_type": "finding", "entity_id": finding["id"], "body": "Del finding"})
    listing = client.get(base, headers=login(client, "collab@a.example"), params={"entity_type": "initiative", "entity_id": initiative["id"]}).json()
    assert listing["total"] == 2
    assert [c["body"] for c in listing["items"]] == ["Primero", "Segundo"]
    assert client.get(base, headers=admin).status_code == 422


def test_comment_target_must_exist_in_this_engagement(client, world):
    admin, foreign = _initiative(client, world, engagement=world.eng_b)
    base = f"/api/engagements/{world.eng_a.id}/comments"
    assert client.post(base, headers=admin, json={"entity_type": "initiative", "entity_id": foreign["id"], "body": "x"}).status_code == 422
    assert client.post(base, headers=admin, json={"entity_type": "initiative", "entity_id": str(uuid.uuid4()), "body": "x"}).status_code == 422
    assert client.post(base, headers=admin, json={"entity_type": "unicorn", "entity_id": foreign["id"], "body": "x"}).status_code == 422
    assert client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=admin).json()["total"] == 0


def test_body_is_required_and_comments_are_scoped(client, world):
    admin, initiative = _initiative(client, world)
    base = f"/api/engagements/{world.eng_a.id}/comments"
    assert client.post(base, headers=admin, json={"entity_type": "initiative", "entity_id": initiative["id"], "body": ""}).status_code == 422
    assert client.get(base, headers=login(client, "exec@b.example"), params={"entity_type": "initiative", "entity_id": initiative["id"]}).status_code == 404
    assert client.post(base, headers=login(client, "collab@b.example"), json={"entity_type": "initiative", "entity_id": initiative["id"], "body": "x"}).status_code == 404


def test_listing_comments_rejects_unknown_entity_type(client, world):
    headers = login(client, "collab@a.example")
    response = client.get(
        f"/api/engagements/{world.eng_a.id}/comments", headers=headers,
        params={"entity_type": "unicorn", "entity_id": str(uuid.uuid4())},
    )
    assert response.status_code == 422
    assert "entity_type" in response.json()["detail"]
