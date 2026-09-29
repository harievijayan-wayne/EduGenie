from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_summary_generation():
    payload = {
        "content": (
            "Operating systems manage computer hardware and software resources, providing common services "
            "for computer programs. Time-sharing operating systems schedule tasks for efficient use of the system "
            "and may also include accounting software for cost allocation of processor time, mass storage, printing, "
            "and other resources. For hardware functions such as input and output and memory allocation, the operating "
            "system acts as an intermediary between programs and the computer hardware."
        ),
        "summary_length": "Short"
    }
    response = client.post("/api/summarize", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "summary" in data["data"]
    assert "key_points" in data["data"]
    assert "important_terms" in data["data"]
