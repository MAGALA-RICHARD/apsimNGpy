from pathlib import Path

import requests

base = "http://127.0.0.1:8000"
session = requests.Session()

plant = 'Soybean'
# 1. Create session
fp = str(Path(r'D:\Elimin_rye_cover_crop_2026\APSIMX\cc_cover.apsimx').resolve())
res = requests.post(
    f"{base}/session",
    json={
        "model":'Maize',
        'dll':True


    }
)
print(f"session: {res.status_code}")
session_id = res.json()["session_id"]
print(f"session_id: {session_id}")

# 2. Run simulation

changes = [{
    'path': '[Leaf].Photosynthesis.RUE.FixedValue',
    'value': float(1.3),
    'paramtype': 1
}]
run = session.post(
    f"{base}/run",
    json={
        "session_id": session_id,
        "changes": [],

    },
)
print(f"Run: {run.status_code}", )

# results = session.get(f"{base}/results/{session_id}")
#
# print(f"Status: {results.status_code}")
# for i in results.json():
#     print(i, ':', results.json()[i])


