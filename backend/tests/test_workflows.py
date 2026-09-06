SIMPLE_DEFINITION = {
    "nodes": [
        {"id": "trigger", "type": "trigger.manual", "data": {}},
        {"id": "check", "type": "action.condition", "data": {"left": "x", "op": "==", "right": "x"}},
    ],
    "edges": [{"source": "trigger", "target": "check"}],
}


def test_create_list_and_get_workflow(client, auth_headers):
    res = client.post(
        "/api/workflows",
        json={"name": "My Workflow", "description": "test", "definition": SIMPLE_DEFINITION, "is_active": True},
        headers=auth_headers,
    )
    assert res.status_code == 200
    workflow_id = res.json()["id"]

    listed = client.get("/api/workflows", headers=auth_headers)
    assert len(listed.json()) == 1

    fetched = client.get(f"/api/workflows/{workflow_id}", headers=auth_headers)
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "My Workflow"


def test_workflow_requires_auth(client):
    res = client.get("/api/workflows")
    assert res.status_code == 401


def test_run_workflow_now_logs_each_node(client, auth_headers):
    create = client.post(
        "/api/workflows",
        json={"name": "Runnable", "definition": SIMPLE_DEFINITION, "is_active": True},
        headers=auth_headers,
    )
    workflow_id = create.json()["id"]

    run = client.post(f"/api/workflows/{workflow_id}/run", headers=auth_headers)
    assert run.status_code == 200
    body = run.json()
    assert body["status"] == "success"
    assert len(body["log"]) == 2


def test_webhook_triggers_workflow_without_auth(client, auth_headers):
    create = client.post(
        "/api/workflows",
        json={"name": "Webhook flow", "definition": SIMPLE_DEFINITION, "is_active": True},
        headers=auth_headers,
    )
    workflow_id = create.json()["id"]

    res = client.post(f"/api/webhooks/{workflow_id}", json={"source": "test"})
    assert res.status_code == 200
    assert res.json()["status"] == "success"


def test_webhook_rejects_unknown_workflow(client):
    res = client.post("/api/webhooks/does-not-exist", json={})
    assert res.status_code == 404


def test_deleting_workflow_removes_it(client, auth_headers):
    create = client.post(
        "/api/workflows",
        json={"name": "To delete", "definition": SIMPLE_DEFINITION, "is_active": True},
        headers=auth_headers,
    )
    workflow_id = create.json()["id"]

    client.delete(f"/api/workflows/{workflow_id}", headers=auth_headers)
    fetched = client.get(f"/api/workflows/{workflow_id}", headers=auth_headers)
    assert fetched.status_code == 404
