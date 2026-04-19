import requests

base = "http://127.0.0.1:8000"
session = requests.Session()

# 1. Create session
res = requests.post(
    f"{base}/session",
    json={
        "model": "AgPasture"
    }
)
print("session:", res.status_code)
session_id = res.json()["session_id"]
print('running for session id', session_id)
# 2. Run simulation
run = session.post(f"{base}/run", json={
    "session_id": session_id,
    "changes": []
})
print("Run:", run.status_code)

# 3. Get results
res = session.get(f"{base}/results/{session_id}")
print("Results:", res.status_code)
print(res.json())