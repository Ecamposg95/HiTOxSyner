from tests.factories import login


def _sessions(world, engagement=None):
    return f"/api/engagements/{(engagement or world.eng_a).id}/lab/sessions"


def _pods(world, engagement=None):
    return f"/api/engagements/{(engagement or world.eng_a).id}/lab/pods"


def _feed(client, world, headers):
    return client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=headers).json()


def test_syner_creates_session_with_catalog_defaults_and_internal_activity(client, world):
    admin = login(client, "admin@syner.example")
    response = client.post(_sessions(world), headers=admin, json={"number": 2, "held_on": "2026-11-05"})
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["name"] == "Trust, Conflict & Difficult Conversations"
    assert body["theme"] == "CONFRONTAR"
    assert body["status"] == "Planned" and body["attendance_count"] is None and body["syner_notes"] == ""
    assert body["held_on"] == "2026-11-05" and body["engagement_id"] == str(world.eng_a.id)
    assert _feed(client, world, admin)["items"][0]["summary"] == 'Syner Admin created Lab Session 2 "Trust, Conflict & Difficult Conversations"'
    assert _feed(client, world, login(client, "exec@a.example"))["total"] == 0
    assert _feed(client, world, login(client, "collab@a.example"))["total"] == 0


def test_session_number_is_unique_per_engagement_and_within_range(client, world):
    admin = login(client, "admin@syner.example")
    assert client.post(_sessions(world), headers=admin, json={"number": 1}).status_code == 201
    assert client.post(_sessions(world), headers=admin, json={"number": 1}).status_code == 409
    assert client.post(_sessions(world), headers=admin, json={"number": 5}).status_code == 422
    assert client.post(_sessions(world), headers=admin, json={"number": 0}).status_code == 422
    assert client.post(_sessions(world, world.eng_b), headers=admin, json={"number": 1}).status_code == 201
    listing = client.get(_sessions(world), headers=admin).json()
    assert listing["total"] == 1 and listing["items"][0]["number"] == 1


def test_sessions_list_ordered_by_number_and_custom_name_kept(client, world):
    admin = login(client, "admin@syner.example")
    client.post(_sessions(world), headers=admin, json={"number": 3})
    client.post(_sessions(world), headers=admin, json={"number": 1, "name": "Sesión inaugural", "theme": "DECIDIR"})
    items = client.get(_sessions(world), headers=admin).json()["items"]
    assert [s["number"] for s in items] == [1, 3]
    assert items[0]["name"] == "Sesión inaugural" and items[1]["name"] == "From Silos to Flow" and items[1]["theme"] == "ALINEAR"


def test_session_update_marks_done_and_logs_status_change_internally(client, world):
    admin = login(client, "admin@syner.example")
    created = client.post(_sessions(world), headers=admin, json={"number": 1}).json()
    response = client.patch(
        f"/api/lab/sessions/{created['id']}", headers=admin,
        json={"status": "Done", "attendance_count": 18, "held_on": "2026-10-20", "syner_notes": "Buena energía en el grupo."},
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "Done" and response.json()["attendance_count"] == 18
    activity = _feed(client, world, admin)["items"][0]
    assert activity["action"] == "status_changed"
    assert activity["summary"] == 'Syner Admin updated Lab Session 1 "The Brain Under Pressure" from Planned to Done'
    assert _feed(client, world, login(client, "exec@a.example"))["total"] == 0
    assert client.patch(f"/api/lab/sessions/{created['id']}", headers=admin, json={"attendance_count": -1}).status_code == 422
    assert client.patch(f"/api/lab/sessions/{created['id']}", headers=admin, json={"name": None}).status_code == 422
    cleared = client.patch(f"/api/lab/sessions/{created['id']}", headers=admin, json={"held_on": None, "attendance_count": None})
    assert cleared.status_code == 200 and cleared.json()["held_on"] is None and cleared.json()["attendance_count"] is None


def test_only_syner_manages_sessions_and_pods(client, world):
    admin = login(client, "admin@syner.example")
    session = client.post(_sessions(world), headers=admin, json={"number": 1}).json()
    pod = client.post(_pods(world), headers=admin, json={"number": 1, "name": "Pod Norte"}).json()
    for email in ("exec@a.example", "collab@a.example"):
        headers = login(client, email)
        assert client.get(_sessions(world), headers=headers).status_code == 403
        assert client.post(_sessions(world), headers=headers, json={"number": 2}).status_code == 403
        assert client.patch(f"/api/lab/sessions/{session['id']}", headers=headers, json={"status": "Done"}).status_code == 403
        assert client.get(_pods(world), headers=headers).status_code == 403
        assert client.post(_pods(world), headers=headers, json={"number": 2, "name": "Pod Sur"}).status_code == 403
        assert client.patch(f"/api/lab/pods/{pod['id']}", headers=headers, json={"name": "Otro"}).status_code == 403
    exec_b = login(client, "exec@b.example")
    assert client.get(_sessions(world), headers=exec_b).status_code == 404
    assert client.post(_sessions(world), headers=exec_b, json={"number": 2}).status_code == 404
    assert client.patch(f"/api/lab/sessions/{session['id']}", headers=exec_b, json={"status": "Done"}).status_code == 404
    assert client.patch(f"/api/lab/pods/{pod['id']}", headers=exec_b, json={"name": "Otro"}).status_code == 404
    assert client.get(_sessions(world), headers=admin).json()["total"] == 1


def test_pods_crud_unique_number_and_isolation(client, world):
    admin = login(client, "admin@syner.example")
    response = client.post(_pods(world), headers=admin, json={"number": 1, "name": "Pod Norte"})
    assert response.status_code == 201, response.text
    pod = response.json()
    assert client.post(_pods(world), headers=admin, json={"number": 1, "name": "Repetido"}).status_code == 409
    assert client.post(_pods(world), headers=admin, json={"number": 0, "name": "Cero"}).status_code == 422
    assert client.post(_pods(world, world.eng_b), headers=admin, json={"number": 1, "name": "De B"}).status_code == 201
    assert _feed(client, world, admin)["items"][0]["summary"] == 'Syner Admin created Pod "Pod Norte"'
    renamed = client.patch(f"/api/lab/pods/{pod['id']}", headers=admin, json={"name": "Pod Norte+"})
    assert renamed.status_code == 200 and renamed.json()["name"] == "Pod Norte+"
    other = client.post(_pods(world), headers=admin, json={"number": 2, "name": "Pod Sur"}).json()
    assert client.patch(f"/api/lab/pods/{other['id']}", headers=admin, json={"number": 1}).status_code == 409
    listing = client.get(_pods(world), headers=admin).json()
    assert listing["total"] == 2 and [p["name"] for p in listing["items"]] == ["Pod Norte+", "Pod Sur"]
