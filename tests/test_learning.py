from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_learning_path_generation():
    payload = {
        "topic": "Machine Learning",
        "current_level": "Beginner",
        "goal": "Build deep neural networks",
        "hours_per_day": 2.0,
        "duration": "4 Weeks"
    }
    response = client.post("/api/learn/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "stages" in data["data"]
    assert len(data["data"]["stages"]) >= 3

def test_study_plan_generation():
    payload = {
        "exam_date": "2026-11-20",
        "subjects": ["Algorithms", "Database Systems"],
        "hours_per_day": 3.0,
        "current_level": "Intermediate"
    }
    response = client.post("/api/learning/study-plan", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "study_plan" in data["data"]
    assert len(data["data"]["study_plan"]) >= 5
