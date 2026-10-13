def test_unknown_api_route_is_json_404_not_index_html(client):
    response = client.get("/api/no-existe")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {"detail": "Not Found"}


def test_non_api_route_serves_spa_or_explicit_404(client):
    response = client.get("/initiatives/abc")
    assert response.status_code in (200, 404)
    if response.status_code == 404:
        assert response.json() == {"detail": "Frontend build not found"}
    else:
        assert "<div id=\"root\">" in response.text
