import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("APP_ENV", "test")

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    print("health ok")

def test_stats():
    r = client.get("/api/subtitles/stats")
    assert r.status_code == 200
    data = r.json()
    assert data["total_lines"] > 0
    print("stats ok", data)

def test_speakers():
    r = client.get("/api/subtitles/speakers")
    assert r.status_code == 200
    data = r.json()
    speakers = [s["speaker"] for s in data]
    print("speakers ok count", len(data))
    # Should include known characters
    known = {"Mary", "Grace", "Ryland", "Stratt", "Rocky"}
    found = known.intersection(set(speakers))
    print("known found:", found)
    assert len(found) >= 3

def test_lines():
    r = client.get("/api/subtitles/lines?limit=5")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 5
    print("lines ok")

def test_timeline():
    r = client.get("/api/subtitles/timeline?window=60")
    assert r.status_code == 200
    data = r.json()
    assert len(data) > 0
    print("timeline ok points", len(data))

def test_search_semantic():
    r = client.get("/api/search/semantic?q=spaceship")
    assert r.status_code == 200
    data = r.json()
    assert "results" in data
    print("semantic search ok results", len(data["results"]))

def test_search_text():
    r = client.get("/api/search/text?q= oxygen")
    assert r.status_code == 200
    data = r.json()
    assert "results" in data
    print("text search ok results", len(data["results"]))

def test_analytics():
    r = client.get("/api/analytics/top-words?limit=10")
    assert r.status_code == 200
    data = r.json()
    assert len(data) > 0
    print("top words ok", len(data))

    r = client.get("/api/analytics/sentiment-distribution")
    assert r.status_code == 200
    print("sentiment distribution ok")

    r = client.get("/api/analytics/duration-stats")
    assert r.status_code == 200
    print("duration stats ok")

if __name__ == "__main__":
    test_health()
    test_stats()
    test_speakers()
    test_lines()
    test_timeline()
    test_search_semantic()
    test_search_text()
    test_analytics()
    print("\nAll tests passed.")
