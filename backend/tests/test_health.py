def test_health_returns_ok(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_detailed_health_reports_dependencies(client):
    res = client.get("/health/detailed")
    assert res.status_code == 200
    body = res.json()
    assert "database" in body
    assert "ai_providers" in body
    assert set(body["ai_providers"].keys()) == {"claude", "gemini"}


def test_metrics_endpoint_exposes_prometheus_format(client):
    client.get("/health")  # generate at least one request to count
    res = client.get("/metrics")
    assert res.status_code == 200
    assert "flowmind_requests_total" in res.text
