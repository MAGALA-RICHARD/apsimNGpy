# api_server.py
import random
from ctypes import c_double
from threading import Lock
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
from apsimNGpy import configuration
from apsimNGpy import logger
from sessions import SessionManager, start_cleanup_task
# import untils
from utils import (
    start_apsim_server,
    run_with_changes,
    connect_to_remote_server,
    PROPERTY_TYPE_DOUBLE
)

app = FastAPI(title="APSIM Server Python API")

# ---------------------------
# GLOBAL STATE
# ---------------------------
SESSIONS: Dict[str, object] = {}

# init session manager
session_manager = SessionManager()

lock = Lock()

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 27747


def get_free_port():
    return random.randint(30000, 40000)


class ApsimBinRequest(BaseModel):
    path: str = configuration.bin_path


# start model
class Start(BaseModel):
    model: str


# Start clean up immediately
@app.on_event("startup")
def startup():
    start_cleanup_task(session_manager, interval=60, timeout=30)
    logger.info("🧹 Auto-cleanup started")


ApsimBin = ApsimBinRequest()


@app.put("/apsim_bin")
def set_apsim_bin(data: ApsimBinRequest):
    from apsimNGpy.config import locate_model_bin_path
    try:
        path = Path(locate_model_bin_path(data.path))
    except NotADirectoryError:
        raise HTTPException(status_code=404, detail=f"{data.path} is not a directory")

    # Validate existence
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"path {path} does not exist"
        )

    # Idempotent check
    if getattr(ApsimBin, "path", None) == str(path):
        return {
            "message": "APSIM bin already set",
            "path": str(path)
        }

    # Set the path
    ApsimBin.path = str(path)

    return {
        "message": "APSIM bin updated",
        "path": str(path)
    }


# ---------------------------
# START SERVER for each session or model
# ---------------------------
@app.post("/session")
def create_session(start: Start):
    import time
    from pathlib import Path
    from apsimNGpy import load_crop_from_disk
    bin_path = ApsimBin.path
    SERVER_PATH = bin_path
    session = session_manager.create(start.model)
    if start.model.endswith(".apsimx"):
        model = start.model
    else:
        model = load_crop_from_disk(start.model, bin_path=bin_path, out=f'f_{session.session_id}.apsimx')
    if not Path(model).exists() or not Path(model).is_file():
        raise HTTPException(status_code=404, detail=f"model path {model} does not exist")
    process = start_apsim_server(
        server_path=SERVER_PATH,
        file_path=model,
        port=session.port
    )
    time.sleep(2.5)
    sock = connect_to_remote_server("127.0.0.1", session.port)
    session.process = process
    session.socket = sock

    return {
        "session_id": session.session_id,
        "port": SERVER_PORT,
        "model": session.model_name
    }


@app.delete("/sessions/{session_id}")
def stop_session(session_id: str):
    try:
        session = session_manager.get(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")

    # 🔥 safely terminate APSIM process
    if session.process:
        try:
            session.process.terminate()
            session.process.wait(timeout=5)  # ensure cleanup
        except Exception:
            # fallback in case terminating fails
            session.process.kill()

    # remove session
    session_manager.delete(session_id)

    return {
        "status": "stopped",
        "session_id": session_id
    }


# ---------------------------
# REQUEST MODELS
# ---------------------------
class Change(BaseModel):
    path: str
    value: float
    paramtype: int = PROPERTY_TYPE_DOUBLE


class RunRequest(BaseModel):
    session_id: str
    changes: List[Change]


# ---------------------------
# SESSION MANAGEMENT
# ---------------------------
# @app.post("/session")
# def _create_session():
#     try:
#         sock = connect_to_remote_server(SERVER_HOST, SERVER_PORT)
#     except Exception as e:
#         raise HTTPException(500, f"Connection failed: {e}")
#
#     session_id = str(uuid4())
#     SESSIONS[session_id] = sock
#
#     return {"session_id": session_id}


def run_http(session):
    session.client.get(f"http://127.0.0.1:{session.port}/run")


# ---------------------------
# RUN SIMULATION
# ---------------------------
@app.post("/run")
def run_simulation(req: RunRequest):
    try:
        session = session_manager.get(req.session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session  {req.session_id}not found")

    if session.status == "expired":
        raise HTTPException(status_code=410, detail="Session expired")

    try:
        # 🔥 update activity (important for an expiration system)
        session_manager.touch(req.session_id)

        try:
            run_with_changes(session.socket, [])
            # session.process.wait()
            return {"status": "completed", "session_id": req.session_id}
        except Exception as e:
            raise HTTPException(500, str(e))


    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------
# READ RESULTS
# ---------------------------
@app.get("/results/{session_id}")
def get_results(session_id: str):
    from utils import read_from_socket, read_output
    try:
        session = session_manager.get(session_id)
        # update activity (important for auto-expiration)
        session_manager.touch(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    if session.status == "expired":
        raise HTTPException(status_code=410, detail="Session expired")

    try:
        # update activity (important for auto-expiration)
        session_manager.touch(session_id)

        data= read_output(session.socket, 'Report', {
            'Yield': c_double,
            'Clock.Today': c_double
        })

        # OPTIONAL: filter + type casting (replacement for read_output)
        filtered = []
        for row in data:
            filtered.append({
                "Yield": float(row.get("Yield", 0)),
                "Clock.Today": float(row.get("Clock.Today", 0))
            })

        return filtered

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
