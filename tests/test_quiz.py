from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_quiz_generation_and_submission():
    # 1. Generate quiz
    gen_payload = {
        "topic": "Binary Search Trees",
        "num_questions": 3,
        "difficulty": "medium"
    }
    gen_res = client.post("/api/quiz/generate", json=gen_payload)
    assert gen_res.status_code == 200
    gen_data = gen_res.json()
    assert gen_data["success"] is True
    quiz = gen_data["data"]
    assert quiz["total_questions"] >= 1
    assert "questions" in quiz
    quiz_id = quiz["quiz_id"]

    # 2. Submit quiz
    first_q = quiz["questions"][0]
    answers = {"0": first_q["options"][0]}
    submit_res = client.post("/api/quiz/submit", json={"quiz_id": quiz_id, "user_answers": answers})
    assert submit_res.status_code == 200
    sub_data = submit_res.json()
    assert sub_data["success"] is True
    assert "score" in sub_data["data"]
    assert "percentage" in sub_data["data"]
