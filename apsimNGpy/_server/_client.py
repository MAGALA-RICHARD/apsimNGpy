import requests
import streamlit as st

base = "http://127.0.0.1:8000"
session = requests.Session()

with st.sidebar:
    plant = st.selectbox('Select plant', options=[
        'Maize', "Soybean", 'Barley', 'AgPasture', "Mungbean"
    ])
# 1. Create session
res = requests.post(
    f"{base}/session",
    json={
        "model": plant
    }
)
st.markdown(f"session: {res.status_code}")
session_id = res.json()["session_id"]
st.markdown(f"session_id: {session_id}")

# 2. Run simulation
with st.sidebar:
    run_button = st.button('Run')
if 'run' not in st.session_state:
    st.session_state.run = None
if run_button:
        run = session.post(f"{base}/run", json={
            "session_id": session_id,
            "changes": []
        })
        st.session_state.run  = run
        st.markdown(f"Run: {run.status_code}", )

# 3. Get results
if st.button('get results'):
    if st.session_state.run:
        ran = st.session_state.run.json()
        if ran['status'] == 'completed':
            ran_id = ran['session_id']
            res = session.get(f"{base}/results/{ran_id}")
            st.markdown(f"Results: {res.status_code}")
            st.markdown(res.json())
        else:
            st.warning('running was not successful')
    else:
        st.warning('running was not successful')
