def test_health_returns_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_health_includes_version(client):
    r = client.get("/health")
    assert "version" in r.json()
