from tests.factories import login


def test_dashboard_tiles_and_sections(client, world):
    admin = login(client, "admin@syner.example")
    eng = world.eng_a.id
    client.patch(f"/api/engagements/{eng}", headers=admin, json={"health": "Attention", "progress_pct": 35, "executive_summary": "Arranque."})
    client.post(f"/api/engagements/{eng}/findings", headers=admin, json={"title": "Crítico", "impact": "Critical"})
    client.post(f"/api/engagements/{eng}/findings", headers=admin, json={"title": "Alto", "impact": "High"})
    client.post(f"/api/engagements/{eng}/findings", headers=admin, json={"title": "Bajo", "impact": "Low"})
    active = client.post(f"/api/engagements/{eng}/initiatives", headers=admin, json={"name": "Activa", "status": "Execution"}).json()
    client.post(f"/api/engagements/{eng}/initiatives", headers=admin, json={"name": "Pausada", "status": "On Hold"})
    client.post(f"/api/engagements/{eng}/actions", headers=admin, json={"title": "Abierta", "due_date": "2026-11-01", "initiative_id": active["id"]})
    client.post(f"/api/engagements/{eng}/actions", headers=admin, json={"title": "Hecha", "status": "Completed"})

    response = client.get(f"/api/engagements/{eng}/dashboard", headers=login(client, "exec@a.example"))
    assert response.status_code == 200
    body = response.json()
    assert body["engagement"]["executive_summary"] == "Arranque."
    assert body["tiles"] == {
        "health": "Attention", "progress_pct": 35, "active_initiatives": 1,
        "open_actions": 1, "decisions_required": 0, "critical_findings": 1,
    }
    assert [i["name"] for i in body["active_initiatives"]] == ["Activa"]
    assert {f["title"] for f in body["key_findings"]} == {"Crítico", "Alto"}
    assert [a["title"] for a in body["next_actions"]] == ["Abierta"]
    assert len(body["recent_activity"]) >= 7
    assert [p["phase"] for p in body["roadmap"]] == ["Discover", "Diagnose", "Design", "Prioritize", "Execute", "Measure"]
    assert body["decisions_required"] == []
    assert body["next_milestones"] == []


def test_dashboard_is_scoped(client, world):
    assert client.get(f"/api/engagements/{world.eng_a.id}/dashboard", headers=login(client, "collab@b.example")).status_code == 404
