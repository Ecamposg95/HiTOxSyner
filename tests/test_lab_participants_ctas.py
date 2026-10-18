from tests.factories import login

CTA = {
    "trigger": "Cuando el comité semanal se desvía hacia culpas personales",
    "behavior": "Dar feedback directo y específico en el momento",
    "stakeholder": "Equipo de operaciones",
    "evidence_expected": "Minuta del comité con el feedback registrado",
    "due_date": "2026-11-30",
    "accountability_partner": "Luis Mora",
    "impact": "Reducir retrabajo por acuerdos ambiguos",
}


def _base(world, segment, engagement=None):
    return f"/api/engagements/{(engagement or world.eng_a).id}/lab/{segment}"


def _feed(client, world, headers):
    return client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=headers).json()


def _setup(client, world):
    admin = login(client, "admin@syner.example")
    s1 = client.post(_base(world, "sessions"), headers=admin, json={"number": 1}).json()
    s2 = client.post(_base(world, "sessions"), headers=admin, json={"number": 2}).json()
    pod1 = client.post(_base(world, "pods"), headers=admin, json={"number": 1, "name": "Pod Norte"}).json()
    pod2 = client.post(_base(world, "pods"), headers=admin, json={"number": 2, "name": "Pod Sur"}).json()
    return admin, s1, s2, pod1, pod2


def _participant(client, world, admin, name, pod_id=None):
    return client.post(_base(world, "participants"), headers=admin, json={"full_name": name, "area": "Operaciones", "title": "Gerente", "pod_id": pod_id}).json()


def test_syner_creates_participant_assigns_pod_and_toggles_active(client, world):
    admin, _, _, pod1, _ = _setup(client, world)
    response = client.post(_base(world, "participants"), headers=admin, json={"full_name": "Ana Ruiz", "area": "Operaciones", "title": "Directora", "pod_id": pod1["id"]})
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["is_active"] is True and body["pod_id"] == pod1["id"] and body["engagement_id"] == str(world.eng_a.id)
    assert _feed(client, world, admin)["items"][0]["summary"] == 'Syner Admin created Participant "Ana Ruiz"'
    assert _feed(client, world, login(client, "exec@a.example"))["total"] == 0
    updated = client.patch(f"/api/lab/participants/{body['id']}", headers=admin, json={"is_active": False, "pod_id": None})
    assert updated.status_code == 200 and updated.json()["is_active"] is False and updated.json()["pod_id"] is None
    assert client.get(_base(world, "participants"), headers=admin, params={"is_active": "true"}).json()["total"] == 0
    assert client.get(_base(world, "participants"), headers=admin, params={"pod_id": pod1["id"]}).json()["total"] == 0
    assert client.get(_base(world, "participants"), headers=admin).json()["total"] == 1
    assert client.patch(f"/api/lab/participants/{body['id']}", headers=admin, json={"full_name": None}).status_code == 422
    assert client.post(_base(world, "participants"), headers=admin, json={"full_name": ""}).status_code == 422


def test_participant_pod_must_belong_to_engagement(client, world):
    admin, _, _, pod1, _ = _setup(client, world)
    foreign_pod = client.post(_base(world, "pods", world.eng_b), headers=admin, json={"number": 1, "name": "De B"}).json()
    assert client.post(_base(world, "participants"), headers=admin, json={"full_name": "Ana Ruiz", "pod_id": foreign_pod["id"]}).status_code == 422
    participant = _participant(client, world, admin, "Ana Ruiz", pod1["id"])
    assert client.patch(f"/api/lab/participants/{participant['id']}", headers=admin, json={"pod_id": foreign_pod["id"]}).status_code == 422
    assert client.get(_base(world, "participants"), headers=admin).json()["items"][0]["pod_id"] == pod1["id"]


def test_cta_requires_behavior_and_links_within_engagement(client, world):
    admin, s1, _, pod1, _ = _setup(client, world)
    ana = _participant(client, world, admin, "Ana Ruiz", pod1["id"])
    response = client.post(_base(world, "ctas"), headers=admin, json={**CTA, "participant_id": ana["id"], "session_id": s1["id"]})
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "Committed" and body["evidence_notes"] == "" and body["due_date"] == "2026-11-30"
    assert body["participant_id"] == ana["id"] and body["session_id"] == s1["id"]
    assert _feed(client, world, admin)["items"][0]["summary"] == 'Syner Admin created CTA for Participant "Ana Ruiz" in Lab Session 1'
    assert client.post(_base(world, "ctas"), headers=admin, json={"participant_id": ana["id"], "session_id": s1["id"]}).status_code == 422
    assert client.post(_base(world, "ctas"), headers=admin, json={"participant_id": ana["id"], "session_id": s1["id"], "behavior": ""}).status_code == 422
    foreign_session = client.post(_base(world, "sessions", world.eng_b), headers=admin, json={"number": 1}).json()
    foreign_participant = client.post(_base(world, "participants", world.eng_b), headers=admin, json={"full_name": "De B"}).json()
    before = _feed(client, world, admin)["total"]
    assert client.post(_base(world, "ctas"), headers=admin, json={**CTA, "participant_id": foreign_participant["id"], "session_id": s1["id"]}).status_code == 422
    assert client.post(_base(world, "ctas"), headers=admin, json={**CTA, "participant_id": ana["id"], "session_id": foreign_session["id"]}).status_code == 422
    assert client.patch(f"/api/lab/ctas/{body['id']}", headers=admin, json={"participant_id": foreign_participant["id"]}).status_code == 422
    assert client.patch(f"/api/lab/ctas/{body['id']}", headers=admin, json={"behavior": None}).status_code == 422
    assert client.get(_base(world, "ctas"), headers=admin).json()["total"] == 1
    assert _feed(client, world, admin)["total"] == before


def test_cta_filters_by_session_pod_and_status(client, world):
    admin, s1, s2, pod1, pod2 = _setup(client, world)
    ana = _participant(client, world, admin, "Ana Ruiz", pod1["id"])
    luis = _participant(client, world, admin, "Luis Mora", pod2["id"])
    base = _base(world, "ctas")
    c1 = client.post(base, headers=admin, json={**CTA, "participant_id": ana["id"], "session_id": s1["id"]}).json()
    c2 = client.post(base, headers=admin, json={**CTA, "participant_id": ana["id"], "session_id": s2["id"], "behavior": "Cerrar cada reunión con acuerdos escritos"}).json()
    client.post(base, headers=admin, json={**CTA, "participant_id": luis["id"], "session_id": s1["id"], "behavior": "Escalar bloqueos en 24 horas"})
    client.patch(f"/api/lab/ctas/{c2['id']}", headers=admin, json={"status": "Evidenced", "evidence_notes": "Minutas de tres reuniones"})
    assert client.get(base, headers=admin, params={"session_id": s1["id"]}).json()["total"] == 2
    assert client.get(base, headers=admin, params={"pod_id": pod1["id"]}).json()["total"] == 2
    evidenced = client.get(base, headers=admin, params={"status": "Evidenced"}).json()
    assert evidenced["total"] == 1 and evidenced["items"][0]["id"] == c2["id"]
    only = client.get(base, headers=admin, params={"pod_id": pod2["id"], "session_id": s1["id"]}).json()
    assert only["total"] == 1 and only["items"][0]["behavior"] == "Escalar bloqueos en 24 horas"
    assert client.get(base, headers=admin, params={"status": "Dropped"}).json()["total"] == 0
    assert client.get(base, headers=admin).json()["items"][0]["id"] == c1["id"]


def test_cta_status_change_logs_internal_activity_only(client, world):
    admin, s1, _, pod1, _ = _setup(client, world)
    ana = _participant(client, world, admin, "Ana Ruiz", pod1["id"])
    cta = client.post(_base(world, "ctas"), headers=admin, json={**CTA, "participant_id": ana["id"], "session_id": s1["id"]}).json()
    response = client.patch(f"/api/lab/ctas/{cta['id']}", headers=admin, json={"status": "Evidenced", "evidence_notes": "Minuta del comité del 12 de noviembre"})
    assert response.status_code == 200 and response.json()["status"] == "Evidenced"
    admin_feed = _feed(client, world, admin)
    assert admin_feed["items"][0]["action"] == "status_changed"
    assert admin_feed["items"][0]["summary"] == 'Syner Admin updated CTA of Participant "Ana Ruiz" from Committed to Evidenced'
    assert admin_feed["total"] >= 6
    for email in ("exec@a.example", "collab@a.example"):
        headers = login(client, email)
        feed = _feed(client, world, headers)
        assert feed["total"] == 0
        dashboard = client.get(f"/api/engagements/{world.eng_a.id}/dashboard", headers=headers).json()
        assert all("Ana Ruiz" not in a["summary"] and "CTA" not in a["summary"] for a in dashboard["recent_activity"])
    cleared = client.patch(f"/api/lab/ctas/{cta['id']}", headers=admin, json={"due_date": None})
    assert cleared.status_code == 200 and cleared.json()["due_date"] is None


def test_client_roles_cannot_access_participants_and_ctas(client, world):
    admin, s1, _, pod1, _ = _setup(client, world)
    ana = _participant(client, world, admin, "Ana Ruiz", pod1["id"])
    cta = client.post(_base(world, "ctas"), headers=admin, json={**CTA, "participant_id": ana["id"], "session_id": s1["id"]}).json()
    for email in ("exec@a.example", "collab@a.example"):
        headers = login(client, email)
        assert client.get(_base(world, "participants"), headers=headers).status_code == 403
        assert client.post(_base(world, "participants"), headers=headers, json={"full_name": "X"}).status_code == 403
        assert client.patch(f"/api/lab/participants/{ana['id']}", headers=headers, json={"is_active": False}).status_code == 403
        assert client.get(_base(world, "ctas"), headers=headers).status_code == 403
        assert client.post(_base(world, "ctas"), headers=headers, json={**CTA, "participant_id": ana["id"], "session_id": s1["id"]}).status_code == 403
        assert client.patch(f"/api/lab/ctas/{cta['id']}", headers=headers, json={"status": "Dropped"}).status_code == 403
    exec_b = login(client, "exec@b.example")
    assert client.get(_base(world, "participants"), headers=exec_b).status_code == 404
    assert client.get(_base(world, "ctas"), headers=exec_b).status_code == 404
    assert client.patch(f"/api/lab/participants/{ana['id']}", headers=exec_b, json={"is_active": False}).status_code == 404
    assert client.patch(f"/api/lab/ctas/{cta['id']}", headers=exec_b, json={"status": "Dropped"}).status_code == 404
    assert client.get(_base(world, "ctas"), headers=admin).json()["items"][0]["status"] == "Committed"
