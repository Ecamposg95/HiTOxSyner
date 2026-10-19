import json
from datetime import date, timedelta

from tests.factories import login

FORBIDDEN_KEYS = {"participant", "trigger", "behavior", "full_name", "syner_notes"}
SECRETS = ("Ana Ruiz", "Luis Mora", "Sofía León", "Dar feedback", "Escalar bloqueos", "Notas internas", "Cerrar reuniones", "Delegar")


def _keys(value, found=None):
    found = set() if found is None else found
    if isinstance(value, dict):
        for key, inner in value.items():
            found.add(key)
            _keys(inner, found)
    elif isinstance(value, list):
        for inner in value:
            _keys(inner, found)
    return found


def _lab(world, segment):
    return f"/api/engagements/{world.eng_a.id}/lab/{segment}"


def _populate(client, world):
    admin = login(client, "admin@syner.example")
    today = date.today()
    s1 = client.post(_lab(world, "sessions"), headers=admin, json={"number": 1, "held_on": (today - timedelta(days=7)).isoformat(), "status": "Done", "attendance_count": 18, "syner_notes": "Notas internas"}).json()
    s2 = client.post(_lab(world, "sessions"), headers=admin, json={"number": 2, "held_on": (today + timedelta(days=10)).isoformat()}).json()
    pod1 = client.post(_lab(world, "pods"), headers=admin, json={"number": 1, "name": "Pod Norte"}).json()
    pod2 = client.post(_lab(world, "pods"), headers=admin, json={"number": 2, "name": "Pod Sur"}).json()
    ana = client.post(_lab(world, "participants"), headers=admin, json={"full_name": "Ana Ruiz", "pod_id": pod1["id"]}).json()
    luis = client.post(_lab(world, "participants"), headers=admin, json={"full_name": "Luis Mora", "pod_id": pod2["id"]}).json()
    sofia = client.post(_lab(world, "participants"), headers=admin, json={"full_name": "Sofía León"}).json()

    def cta(participant, session, behavior, status=None):
        created = client.post(_lab(world, "ctas"), headers=admin, json={"participant_id": participant["id"], "session_id": session["id"], "behavior": behavior, "trigger": "Comité"}).json()
        if status:
            client.patch(f"/api/lab/ctas/{created['id']}", headers=admin, json={"status": status})
        return created

    cta(ana, s1, "Dar feedback directo", "Evidenced")
    cta(ana, s2, "Cerrar reuniones con acuerdos")
    cta(luis, s1, "Escalar bloqueos en 24 horas", "In Progress")
    cta(sofia, s1, "Delegar decisiones operativas", "Dropped")
    client.post(_lab(world, "contracts"), headers=admin, json={"participant_id": ana["id"], "status": "Active"})
    client.post(_lab(world, "contracts"), headers=admin, json={"participant_id": luis["id"]})
    return admin, s2


def test_summary_aggregates_and_hides_personal_data(client, world):
    _populate(client, world)
    response = client.get(_lab(world, "summary"), headers=login(client, "exec@a.example"))
    assert response.status_code == 200, response.text
    body = response.json()
    assert [s["number"] for s in body["sessions"]] == [1, 2]
    assert body["sessions"][0]["status"] == "Done" and body["sessions"][0]["attendance_count"] == 18
    assert body["sessions"][0]["name"] == "The Brain Under Pressure" and body["sessions"][0]["theme"] == "DECIDIR"
    assert body["sessions_done"] == 1
    assert body["cta_totals"] == {"committed": 1, "in_progress": 1, "evidenced": 1, "dropped": 1, "total": 4}
    assert body["evidenced_pct"] == 25
    assert [(b["session_number"], b["session_name"], b["totals"]["total"]) for b in body["by_session"]] == [(1, "The Brain Under Pressure", 3), (2, "Trust, Conflict & Difficult Conversations", 1)]
    assert body["by_session"][0]["totals"]["evidenced"] == 1 and body["by_session"][0]["totals"]["dropped"] == 1
    assert [(b["pod_number"], b["pod_name"], b["totals"]["total"]) for b in body["by_pod"]] == [(1, "Pod Norte", 2), (2, "Pod Sur", 1)]
    assert body["active_contracts"] == 1
    assert not (_keys(body) & FORBIDDEN_KEYS)
    text = json.dumps(body, ensure_ascii=False)
    assert all(secret not in text for secret in SECRETS)
    assert client.get(_lab(world, "summary"), headers=login(client, "admin@syner.example")).status_code == 200
    assert client.get(_lab(world, "summary"), headers=login(client, "collab@a.example")).status_code == 403
    assert client.get(_lab(world, "summary"), headers=login(client, "exec@b.example")).status_code == 404


def test_summary_for_empty_lab_returns_zeros(client, world):
    body = client.get(_lab(world, "summary"), headers=login(client, "exec@a.example")).json()
    assert body == {
        "sessions": [], "sessions_done": 0,
        "cta_totals": {"committed": 0, "in_progress": 0, "evidenced": 0, "dropped": 0, "total": 0},
        "evidenced_pct": 0, "by_session": [], "by_pod": [], "active_contracts": 0,
    }


def test_dashboard_lab_card_only_with_sessions_and_hidden_from_collaborators(client, world):
    dashboard = f"/api/engagements/{world.eng_a.id}/dashboard"
    exec_a = login(client, "exec@a.example")
    assert client.get(dashboard, headers=exec_a).json()["lab"] is None
    admin, s2 = _populate(client, world)
    lab = client.get(dashboard, headers=exec_a).json()["lab"]
    assert lab["next_session"]["number"] == 2 and lab["next_session"]["name"] == "Trust, Conflict & Difficult Conversations"
    assert lab["sessions_done"] == 1 and lab["sessions_total"] == 2
    assert lab["active_ctas"] == 2 and lab["evidenced_pct"] == 25 and lab["active_contracts"] == 1
    assert not (_keys(lab) & FORBIDDEN_KEYS)
    assert all(secret not in json.dumps(lab, ensure_ascii=False) for secret in SECRETS)
    assert client.get(dashboard, headers=login(client, "collab@a.example")).json()["lab"] is None
    assert client.get(dashboard, headers=admin).json()["lab"]["sessions_total"] == 2
    client.patch(f"/api/lab/sessions/{s2['id']}", headers=admin, json={"status": "Done"})
    after = client.get(dashboard, headers=exec_a).json()["lab"]
    assert after["next_session"] is None and after["sessions_done"] == 2


def test_summary_and_dashboard_ignore_other_engagements(client, world):
    admin, _ = _populate(client, world)
    exec_a = login(client, "exec@a.example")
    summary_url, dashboard_url = _lab(world, "summary"), f"/api/engagements/{world.eng_a.id}/dashboard"
    before_summary = client.get(summary_url, headers=exec_a).json()
    before_lab = client.get(dashboard_url, headers=exec_a).json()["lab"]

    def lab_b(segment):
        return f"/api/engagements/{world.eng_b.id}/lab/{segment}"

    for number in (1, 2, 3):
        client.post(lab_b("sessions"), headers=admin, json={"number": number, "status": "Done", "attendance_count": 5})
    session_b = client.get(lab_b("sessions"), headers=admin).json()["items"][0]
    pod_b = client.post(lab_b("pods"), headers=admin, json={"number": 1, "name": "Pod B"}).json()
    part_b = client.post(lab_b("participants"), headers=admin, json={"full_name": "De B", "pod_id": pod_b["id"]}).json()
    for i in range(3):
        cta = client.post(lab_b("ctas"), headers=admin, json={"participant_id": part_b["id"], "session_id": session_b["id"], "behavior": f"B{i}", "trigger": "t"})
        assert cta.status_code == 201, cta.text
    assert client.post(lab_b("contracts"), headers=admin, json={"participant_id": part_b["id"], "status": "Active"}).status_code == 201

    assert client.get(summary_url, headers=exec_a).json() == before_summary
    assert client.get(dashboard_url, headers=exec_a).json()["lab"] == before_lab
