import requests

base = "http://127.0.0.1:8000"
session = requests.Session()

plant = 'Soybean'
# 1. Create session
res = requests.post(
    f"{base}/session",
    json={
        "model": "Maize",
        'dll': False,

    }
)
print(f"session: {res.status_code}")
session_id = res.json()["session_id"]
print(f"session_id: {session_id}")

# 2. Run simulation


run = session.post(
    f"{base}/run",
    json={
        "session_id": session_id,
        "changes": [],
        "edits": [
            {
                "model_type": "Models.Manager",
                "model_name": "Sow using a variable rule",
                "parameters": {"Population": 12},
            },
            {'model_type': 'Models.Manager', 'model_name': 'Fertilise at sowing',
             "parameters": {"Amount": 0.00}, }
        ],
    },
)
print(f"Run: {run.status_code}", )

results = session.get(f"{base}/results/{session_id}")

print(f"Status: {results.status_code}")
for i in results.json():
    print(i, ':', results.json()[i])

param = session.post(
    f"{base}/inspect/{session_id}",
    json={
        "identifier": "Fertilise at sowing",
        "model_type": "Models.Manager"
    }
)
print(f"Inspect: {param.status_code}")
if param.status_code == 200:
   print(param.json())
