from datetime import UTC, datetime

from fastapi.testclient import TestClient


def test_seeded_meeting_library_and_detail(client: TestClient) -> None:
    profile_response = client.get("/api/v1/me")
    assert profile_response.status_code == 200
    assert profile_response.json()["data"]["isDemo"] is True

    response = client.get("/api/v1/meetings")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["pagination"]["totalItems"] == 6
    assert len(payload["items"]) == 6
    assert payload["items"][0]["meetingAtUtc"] > payload["items"][-1]["meetingAtUtc"]

    meeting_id = payload["items"][0]["id"]
    detail_response = client.get(f"/api/v1/meetings/{meeting_id}")
    detail = detail_response.json()["data"]

    assert detail_response.status_code == 200
    assert len(detail["participants"]) >= 2
    assert len(detail["transcriptSegments"]) >= 8
    assert detail["summary"]["overview"]
    assert len(detail["chapters"]) == 3
    assert len(detail["actionItems"]) >= 2


def test_dashboard_returns_one_compact_workspace_payload(client: TestClient) -> None:
    response = client.get("/api/v1/dashboard")

    assert response.status_code == 200
    dashboard = response.json()["data"]
    assert len(dashboard["meetings"]) == 6
    assert dashboard["openActionItems"]
    assert all("transcriptSegments" not in meeting for meeting in dashboard["meetings"])
    assert all(item["meetingId"] and item["meetingTitle"] for item in dashboard["openActionItems"])


def test_api_responses_include_security_headers(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"


def test_library_search_filter_and_sort(client: TestClient) -> None:
    search_response = client.get("/api/v1/meetings", params={"search": "Northstar"})
    assert search_response.status_code == 200
    assert [item["title"] for item in search_response.json()["data"]["items"]] == [
        "Northstar Customer Onboarding"
    ]

    participant_response = client.get(
        "/api/v1/meetings", params={"participant": "Arjun", "sortOrder": "asc"}
    )
    participant_items = participant_response.json()["data"]["items"]
    assert len(participant_items) >= 2
    assert participant_items[0]["meetingAtUtc"] < participant_items[-1]["meetingAtUtc"]


def test_meeting_and_action_item_crud(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/meetings",
        json={
            "title": "API Contract Review",
            "meetingAtUtc": datetime(2026, 8, 14, 8, 30, tzinfo=UTC).isoformat(),
            "participantNames": ["Anusha", "Maya Chen"],
            "transcript": (
                "Anusha: We should finalize the API contract before the frontend integration.\n"
                "Maya Chen: I will review error envelopes and pagination fields today.\n"
                "Anusha: Great, then we can generate the TypeScript client tomorrow."
            ),
        },
    )
    assert create_response.status_code == 201
    meeting = create_response.json()["data"]
    assert meeting["title"] == "API Contract Review"
    assert len(meeting["transcriptSegments"]) == 3
    assert any(
        "review error envelopes" in item["description"].lower() for item in meeting["actionItems"]
    )

    update_response = client.patch(
        f"/api/v1/meetings/{meeting['id']}", json={"title": "API and Client Contract Review"}
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["title"] == "API and Client Contract Review"

    assignee_id = meeting["participants"][0]["id"]
    action_response = client.post(
        f"/api/v1/meetings/{meeting['id']}/action-items",
        json={
            "description": "Generate the frontend API types",
            "assigneeParticipantId": assignee_id,
        },
    )
    assert action_response.status_code == 201
    action = action_response.json()["data"]

    complete_response = client.patch(
        f"/api/v1/action-items/{action['id']}", json={"isCompleted": True}
    )
    assert complete_response.status_code == 200
    assert complete_response.json()["data"]["isCompleted"] is True

    invalid_assignee_response = client.patch(
        f"/api/v1/action-items/{action['id']}",
        json={"assigneeParticipantId": "not-a-meeting-participant"},
    )
    assert invalid_assignee_response.status_code == 422

    delete_response = client.delete(f"/api/v1/meetings/{meeting['id']}")
    assert delete_response.status_code == 204
    assert client.get(f"/api/v1/meetings/{meeting['id']}").status_code == 404


def test_global_search_returns_timestamp_context(client: TestClient) -> None:
    response = client.get("/api/v1/search", params={"q": "activation"})

    assert response.status_code == 200
    results = response.json()["data"]
    assert results
    assert all(result["resultType"] == "transcript" for result in results)
    assert all(result["segmentId"] and result["startInSeconds"] is not None for result in results)


def test_global_search_understands_natural_language_questions(client: TestClient) -> None:
    response = client.get("/api/v1/search", params={"q": "What did we decide about onboarding?"})

    assert response.status_code == 200
    results = response.json()["data"]
    assert results
    assert any("onboarding" in result["snippet"].lower() for result in results)


def test_ask_echo_returns_grounded_answer_and_sources(client: TestClient) -> None:
    response = client.post("/api/v1/ask", json={"question": "What did we decide about onboarding?"})

    assert response.status_code == 200
    answer = response.json()["data"]
    assert answer["answer"]
    assert answer["sources"]
    assert answer["usedAi"] is False
    assert any("onboarding" in source["snippet"].lower() for source in answer["sources"])


def test_invalid_transcript_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/v1/meetings",
        json={
            "title": "Empty transcript",
            "meetingAtUtc": datetime.now(UTC).isoformat(),
            "participantNames": ["Anusha"],
            "transcript": "too short",
        },
    )

    assert response.status_code == 422


def test_transcript_edits_and_saved_moments_persist(client: TestClient) -> None:
    meeting = client.get("/api/v1/meetings").json()["data"]["items"][0]
    detail = client.get(f"/api/v1/meetings/{meeting['id']}").json()["data"]
    segment = detail["transcriptSegments"][0]

    edit_response = client.patch(
        f"/api/v1/transcript-segments/{segment['id']}",
        json={"text": f"{segment['text']} Updated for clarity."},
    )
    assert edit_response.status_code == 200
    assert edit_response.json()["data"]["text"].endswith("Updated for clarity.")

    moment_response = client.post(
        f"/api/v1/meetings/{meeting['id']}/moments",
        json={"segmentId": segment["id"], "kind": "important", "note": "Key decision"},
    )
    assert moment_response.status_code == 201
    moment = moment_response.json()["data"]
    assert moment["authorName"] == "Anusha"

    refreshed = client.get(f"/api/v1/meetings/{meeting['id']}").json()["data"]
    assert any(item["id"] == moment["id"] for item in refreshed["moments"])
    assert client.delete(f"/api/v1/moments/{moment['id']}").status_code == 204
