import pytest

from tests.factories import login

LISTINGS = ["findings", "initiatives", "actions", "milestones", "decisions", "meetings", "documents", "activity"]


@pytest.mark.parametrize("segment", LISTINGS)
def test_listing_pagination_limits_are_enforced(client, world, segment):
    headers = login(client, "exec@a.example")
    base = f"/api/engagements/{world.eng_a.id}/{segment}"
    assert client.get(base, headers=headers, params={"limit": 201}).status_code == 422
    assert client.get(base, headers=headers, params={"limit": 0}).status_code == 422
    assert client.get(base, headers=headers, params={"offset": -1}).status_code == 422
    response = client.get(base, headers=headers, params={"limit": 200, "offset": 0})
    assert response.status_code == 200 and response.json() == {"items": [], "total": 0}


def test_offset_and_limit_slice_results(client, world):
    admin = login(client, "admin@syner.example")
    base = f"/api/engagements/{world.eng_a.id}/findings"
    for i in range(3):
        client.post(base, headers=admin, json={"title": f"Hallazgo {i}"})
    page = client.get(base, headers=admin, params={"limit": 2, "offset": 2}).json()
    assert page["total"] == 3 and len(page["items"]) == 1
    assert client.get(base, headers=admin, params={"limit": 2, "offset": 10}).json() == {"items": [], "total": 3}
