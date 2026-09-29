from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_question_answering():
    payload = {
        "question": "What is the time complexity of QuickSort in the average case?",
        "subject": "Data Structures & Algorithms",
        "level": "intermediate"
    }
    response = client.post("/api/qa", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "answer" in data["data"]
    assert "key_points" in data["data"]
    assert len(data["data"]["key_points"]) > 0

def test_empty_question_validation():
    payload = {
        "question": "   ",
        "subject": "Math",
        "level": "beginner"
    }
    response = client.post("/api/qa", json=payload)
    assert response.status_code == 422 # Pydantic min_length validation failure
