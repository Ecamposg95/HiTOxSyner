import uuid
from datetime import date

from app.models.enums import ActivityAction, Health
from app.services.activity import diff_changes, log_activity
from tests.factories import login


def test_diff_changes_serializes_enums_dates_and_ignores_equal_values(world):
    payload = {"health": Health.AT_RISK, "start_date": date(2026, 10, 1), "name": "Programa A"}
    changes = diff_changes(world.eng_a, payload)
    assert changes == [
        {"field": "health", "before": "On Track", "after": "At Risk"},
        {"field": "start_date", "before": None, "after": "2026-10-01"},
    ]


def test_log_activity_and_list_scoped(client, db, world):
    entity_id = uuid.uuid4()
    log_activity(
        db, user=world.admin, engagement=world.eng_a, action=ActivityAction.CREATED,
        entity_type="finding", entity_id=entity_id, summary='Syner Admin created Finding "X"',
    )
    log_activity(
        db, user=world.admin, engagement=world.eng_b, action=ActivityAction.CREATED,
        entity_type="finding", entity_id=uuid.uuid4(), summary="other org",
    )
    db.commit()
    headers = login(client, "exec@a.example")
    response = client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["summary"] == 'Syner Admin created Finding "X"'
    assert body["items"][0]["user_name"] == "Syner Admin"
    assert body["items"][0]["entity_id"] == str(entity_id)
    filtered = client.get(
        f"/api/engagements/{world.eng_a.id}/activity",
        headers=headers, params={"entity_type": "finding", "entity_id": str(uuid.uuid4())},
    ).json()
    assert filtered["total"] == 0
    assert client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=login(client, "exec@b.example")).status_code == 404
