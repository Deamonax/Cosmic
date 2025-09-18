from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_analyze_jd_returns_expected_shape():
    response = client.post("/analyze_jd", json={"jd_text": "example"})
    assert response.status_code == 200
    body = response.json()
    assert "summary" in body
    assert isinstance(body["skills"], list)
    assert isinstance(body["sections"], list)


def test_assess_returns_fit_information():
    payload = {
        "jd_json": {
            "title": "Senior Frontend Engineer",
            "location": "Remote",
            "responsibilities": ["Ship features"],
        },
        "candidate_chunks": [
            {
                "id": "chunk-1",
                "heading": "Summary",
                "content": "Extensive React background",
            }
        ],
    }
    response = client.post("/assess", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert {"score", "verdict", "strengths", "gaps", "next_steps"} <= body.keys()


def test_rewrite_cv_returns_sections():
    payload = {"project_id": "proj-123", "mode": "bold"}
    response = client.post("/rewrite_cv", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["project_id"] == "proj-123"
    assert body["mode"] == "bold"
    assert isinstance(body["sections"], list)


def test_qa_returns_question_list():
    payload = {
        "jd_json": {
            "title": "Senior Frontend Engineer",
        },
        "candidate_chunks": [
            {
                "id": "chunk-1",
                "heading": "Summary",
                "content": "Strong frontend background",
            }
        ],
    }
    response = client.post("/qa", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body.get("questions"), list)
    assert all("question" in item and "answer" in item for item in body["questions"])


def test_invalid_payload_returns_400():
    response = client.post("/analyze_jd", json={"jd_text": ""})
    assert response.status_code == 400
    body = response.json()
    assert body["message"] == "Invalid request payload"
    assert isinstance(body["errors"], list)
