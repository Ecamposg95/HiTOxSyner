from tests.factories import login

CTA = {"behavior": "Dar feedback directo", "trigger": "Comité semanal", "stakeholder": "Equipo", "due_date": "2026-11-30"}


def _base(world, segment, engagement=None):
    return f"/api/engagements/{(engagement or world.eng_a).id}/lab/{segment}"


def _feed(client, world, headers):
    return client.get(f"/api/engagements/{world.eng_a.id}/activity", headers=headers).json()


def _setup(client, world):
    admin = login(client, "admin@syner.example")
    session = client.post(_base(world, "sessions"), headers=admin, json={"number": 1}).json()
    ana = client.post(_base(world, "participants"), headers=admin, json={"full_name": "Ana Ruiz"}).json()
    luis = client.post(_base(world, "participants"), headers=admin, json={"full_name": "Luis Mora"}).json()
    ana_ctas = [
        client.post(_base(world, "ctas"), headers=admin, json={**CTA, "participant_id": ana["id"], "session_id": session["id"], "behavior": f"Conducta {i}"}).json()["id"]
        for i in range(4)
    ]
    luis_cta = client.post(_base(world, "ctas"), headers=admin, json={**CTA, "participant_id": luis["id"], "session_id": session["id"]}).json()["id"]
    return admin, ana, luis, ana_ctas, luis_cta


def test_contract_defaults_review_dates_and_links_up_to_three_ctas(client, world):
    admin, ana, _, ana_ctas, _ = _setup(client, world)
    base = _base(world, "contracts")
    assert client.post(base, headers=admin, json={"participant_id": ana["id"], "cta_ids": ana_ctas}).status_code == 422
    response = client.post(base, headers=admin, json={"participant_id": ana["id"], "start_date": "2026-11-01", "success_signal": "El equipo reporta acuerdos claros", "cta_ids": ana_ctas[:3]})
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "Draft"
    assert body["review_30_date"] == "2026-12-01" and body["review_60_date"] == "2026-12-31"
    assert sorted(body["cta_ids"]) == sorted(ana_ctas[:3])
    assert _feed(client, world, admin)["items"][0]["summary"] == 'Syner Admin created Action Contract for Participant "Ana Ruiz"'
    assert _feed(client, world, login(client, "exec@a.example"))["total"] == 0
    listing = client.get(base, headers=admin).json()
    assert listing["total"] == 1 and sorted(listing["items"][0]["cta_ids"]) == sorted(ana_ctas[:3])


def test_contract_without_start_date_keeps_review_dates_null_and_explicit_dates_win(client, world):
    admin, ana, luis, ana_ctas, _ = _setup(client, world)
    base = _base(world, "contracts")
    blank = client.post(base, headers=admin, json={"participant_id": ana["id"]}).json()
    assert blank["start_date"] is None and blank["review_30_date"] is None and blank["review_60_date"] is None and blank["cta_ids"] == []
    explicit = client.post(base, headers=admin, json={"participant_id": luis["id"], "start_date": "2026-11-01", "review_30_date": "2026-12-05"}).json()
    assert explicit["review_30_date"] == "2026-12-05" and explicit["review_60_date"] == "2026-12-31"


def test_contract_is_unique_per_participant_and_ctas_must_belong_to_participant(client, world):
    admin, ana, luis, ana_ctas, luis_cta = _setup(client, world)
    base = _base(world, "contracts")
    first = client.post(base, headers=admin, json={"participant_id": ana["id"], "cta_ids": ana_ctas[:2]}).json()
    assert client.post(base, headers=admin, json={"participant_id": ana["id"]}).status_code == 409
    assert client.post(base, headers=admin, json={"participant_id": luis["id"], "cta_ids": [ana_ctas[0]]}).status_code == 422
    foreign = client.post(_base(world, "participants", world.eng_b), headers=admin, json={"full_name": "De B"}).json()
    assert client.post(base, headers=admin, json={"participant_id": foreign["id"]}).status_code == 422
    assert client.post(base, headers=admin, json={"participant_id": luis["id"], "cta_ids": [luis_cta, luis_cta]}).status_code == 201
    listing = client.get(base, headers=admin).json()
    assert listing["total"] == 2
    assert sorted(next(c for c in listing["items"] if c["id"] == first["id"])["cta_ids"]) == sorted(ana_ctas[:2])
    assert next(c for c in listing["items"] if c["participant_id"] == luis["id"])["cta_ids"] == [luis_cta]


def test_contract_update_replaces_ctas_recomputes_dates_and_logs_status(client, world):
    admin, ana, _, ana_ctas, luis_cta = _setup(client, world)
    base = _base(world, "contracts")
    contract = client.post(base, headers=admin, json={"participant_id": ana["id"], "start_date": "2026-11-01", "cta_ids": ana_ctas[:2]}).json()
    url = f"/api/lab/contracts/{contract['id']}"
    replaced = client.patch(url, headers=admin, json={"cta_ids": [ana_ctas[1], ana_ctas[3]]})
    assert replaced.status_code == 200, replaced.text
    assert sorted(replaced.json()["cta_ids"]) == sorted([ana_ctas[1], ana_ctas[3]])
    moved = client.patch(url, headers=admin, json={"start_date": "2026-12-01"}).json()
    assert moved["review_30_date"] == "2026-12-31" and moved["review_60_date"] == "2027-01-30"
    pinned = client.patch(url, headers=admin, json={"review_30_date": "2027-01-05"}).json()
    assert pinned["review_30_date"] == "2027-01-05" and pinned["review_60_date"] == "2027-01-30"
    activated = client.patch(url, headers=admin, json={"status": "Active"})
    assert activated.status_code == 200 and activated.json()["status"] == "Active"
    activity = _feed(client, world, admin)["items"][0]
    assert activity["action"] == "status_changed"
    assert activity["summary"] == 'Syner Admin updated Action Contract of Participant "Ana Ruiz" from Draft to Active'
    assert client.patch(url, headers=admin, json={"cta_ids": ana_ctas}).status_code == 422
    assert client.patch(url, headers=admin, json={"cta_ids": [luis_cta]}).status_code == 422
    assert client.patch(url, headers=admin, json={"participant_id": None}).status_code == 422
    assert client.patch(url, headers=admin, json={"cta_ids": None}).status_code == 422
    assert sorted(client.get(base, headers=admin).json()["items"][0]["cta_ids"]) == sorted([ana_ctas[1], ana_ctas[3]])


def test_contracts_filter_by_status_and_client_roles_get_403(client, world):
    admin, ana, luis, ana_ctas, _ = _setup(client, world)
    base = _base(world, "contracts")
    active = client.post(base, headers=admin, json={"participant_id": ana["id"], "status": "Active"}).json()
    client.post(base, headers=admin, json={"participant_id": luis["id"]})
    filtered = client.get(base, headers=admin, params={"status": "Active"}).json()
    assert filtered["total"] == 1 and filtered["items"][0]["id"] == active["id"]
    for email in ("exec@a.example", "collab@a.example"):
        headers = login(client, email)
        assert client.get(base, headers=headers).status_code == 403
        assert client.post(base, headers=headers, json={"participant_id": ana["id"]}).status_code == 403
        assert client.patch(f"/api/lab/contracts/{active['id']}", headers=headers, json={"status": "Closed"}).status_code == 403
    exec_b = login(client, "exec@b.example")
    assert client.get(base, headers=exec_b).status_code == 404
    assert client.patch(f"/api/lab/contracts/{active['id']}", headers=exec_b, json={"status": "Closed"}).status_code == 404


def test_cta_linked_to_contract_cannot_change_participant(client, world):
    admin, ana, luis, ana_ctas, _ = _setup(client, world)
    contract = client.post(_base(world, "contracts"), headers=admin, json={"participant_id": ana["id"], "cta_ids": ana_ctas[:1]}).json()
    url = f"/api/lab/contracts/{contract['id']}"
    cta_url = f"/api/lab/ctas/{ana_ctas[0]}"
    blocked = client.patch(cta_url, headers=admin, json={"participant_id": luis["id"]})
    assert blocked.status_code == 409
    assert blocked.json()["detail"] == "El CTA pertenece a un Leadership Action Contract; quítalo del contrato antes de cambiar el participante"
    listing = client.get(_base(world, "ctas"), headers=admin).json()["items"]
    assert next(c for c in listing if c["id"] == ana_ctas[0])["participant_id"] == ana["id"]
    assert client.patch(url, headers=admin, json={"status": "Active"}).status_code == 200
    assert client.patch(url, headers=admin, json={"cta_ids": []}).status_code == 200
    assert client.patch(cta_url, headers=admin, json={"participant_id": luis["id"]}).status_code == 200
    assert client.patch(url, headers=admin, json={"success_signal": "Señal"}).status_code == 200


def test_contract_participant_change_conflicts_and_succeeds(client, world):
    admin, ana, luis, ana_ctas, _ = _setup(client, world)
    base = _base(world, "contracts")
    contract = client.post(base, headers=admin, json={"participant_id": ana["id"]}).json()
    client.post(base, headers=admin, json={"participant_id": luis["id"]})
    url = f"/api/lab/contracts/{contract['id']}"
    assert client.patch(url, headers=admin, json={"participant_id": luis["id"]}).status_code == 409
    sofia = client.post(_base(world, "participants"), headers=admin, json={"full_name": "Sofía León"}).json()
    moved = client.patch(url, headers=admin, json={"participant_id": sofia["id"], "cta_ids": []})
    assert moved.status_code == 200 and moved.json()["participant_id"] == sofia["id"]
