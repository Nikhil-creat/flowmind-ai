def _signup(client, email, name="Test"):
    res = client.post("/api/auth/signup", json={"full_name": name, "email": email, "password": "password123"})
    return res.json()["access_token"]


def test_signup_creates_a_personal_workspace(client, auth_headers):
    res = client.get("/api/workspaces", headers=auth_headers)
    assert res.status_code == 200
    workspaces = res.json()
    assert len(workspaces) == 1
    assert workspaces[0]["role"] == "owner"


def test_create_additional_workspace(client, auth_headers):
    res = client.post("/api/workspaces", json={"name": "Side Project"}, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["role"] == "owner"

    listed = client.get("/api/workspaces", headers=auth_headers).json()
    assert len(listed) == 2


def test_owner_can_invite_existing_user(client, auth_headers):
    token2 = _signup(client, "teammate@example.com", "Teammate")
    workspace_id = client.get("/api/workspaces", headers=auth_headers).json()[0]["id"]

    res = client.post(
        f"/api/workspaces/{workspace_id}/invite",
        json={"email": "teammate@example.com", "role": "member"},
        headers=auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["role"] == "member"

    members = client.get(f"/api/workspaces/{workspace_id}/members", headers=auth_headers).json()
    assert len(members) == 2


def test_invite_unknown_email_fails(client, auth_headers):
    workspace_id = client.get("/api/workspaces", headers=auth_headers).json()[0]["id"]
    res = client.post(
        f"/api/workspaces/{workspace_id}/invite",
        json={"email": "nobody@example.com", "role": "member"},
        headers=auth_headers,
    )
    assert res.status_code == 404


def test_member_cannot_invite_others(client, auth_headers):
    token2 = _signup(client, "member2@example.com", "Member Two")
    workspace_id = client.get("/api/workspaces", headers=auth_headers).json()[0]["id"]
    client.post(
        f"/api/workspaces/{workspace_id}/invite",
        json={"email": "member2@example.com", "role": "member"},
        headers=auth_headers,
    )

    member_headers = {"Authorization": f"Bearer {token2}", "X-Workspace-ID": workspace_id}
    res = client.post(
        f"/api/workspaces/{workspace_id}/invite",
        json={"email": "someone@example.com", "role": "member"},
        headers=member_headers,
    )
    assert res.status_code == 403


def test_workspace_scoped_documents_are_shared_between_members(client, auth_headers):
    token2 = _signup(client, "shared-doc@example.com", "Teammate")
    workspace_id = client.get("/api/workspaces", headers=auth_headers).json()[0]["id"]
    client.post(
        f"/api/workspaces/{workspace_id}/invite",
        json={"email": "shared-doc@example.com", "role": "member"},
        headers=auth_headers,
    )

    create = client.post(
        "/api/workflows",
        json={"name": "Shared", "definition": {"nodes": [{"id": "t", "type": "trigger.manual", "data": {}}], "edges": []}, "is_active": True},
        headers=auth_headers,
    )
    workflow_id = create.json()["id"]

    member_headers = {"Authorization": f"Bearer {token2}", "X-Workspace-ID": workspace_id}
    fetched = client.get(f"/api/workflows/{workflow_id}", headers=member_headers)
    assert fetched.status_code == 200
