import requests

base = "http://127.0.0.1:8000"
session = requests.Session()

plant = 'Maize'
# 1. Create session
res = requests.post(
    f"{base}/session",
    json={
        "model": "Wheat"
    }
)
print(f"session: {res.status_code}")
session_id = res.json()["session_id"]
print(f"session_id: {session_id}")

# 2. Run simulation


run = session.post(f"{base}/run", json={
    "session_id": session_id,
    "changes": []
})

print(f"Run: {run.status_code}", )


