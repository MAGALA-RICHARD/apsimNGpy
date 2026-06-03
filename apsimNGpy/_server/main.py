# api_server.py
import random
from ctypes import c_double
from threading import Lock
from typing import Dict, List, Optional, Any, Union

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from pathlib import Path
from apsimNGpy import configuration, timer
from apsimNGpy import logger
from sessions import SessionManager, start_cleanup_task
from pydantic import BaseModel, Field, ConfigDict
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
    dll: bool = True


# Start clean up immediately
@app.on_event("startup")
def startup():
    start_cleanup_task(session_manager, interval=60, timeout=30)
    logger.info("🧹 Auto-cleanup started")


@app.on_event("shutdown")
def del_files_on_shutdown():
    # clean up copied files on shutdown

    for i in tuple(session_manager.sessions_in_mem):
        session_manager.delete(i)


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
    import shutil
    from apsimNGpy import load_crop_from_disk
    bin_path = ApsimBin.path
    SERVER_PATH = bin_path
    session = session_manager.create(start.model)
    if start.model.endswith(".apsimx"):
        model = start.model
        model = shutil.copy(model, f'f_{session.session_id}.apsimx')
    else:
        model = load_crop_from_disk(start.model, bin_path=bin_path, out=f'f_{session.session_id}.apsimx')
    session.file_path = model
    if not Path(model).exists() or not Path(model).is_file():
        raise HTTPException(status_code=404, detail=f"model path {model} does not exist")
    process = start_apsim_server(
        server_path=SERVER_PATH,
        file_path=model,
        port=session.port,
        use_dll=start.dll
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


class Editor(BaseModel):
    model_type: str
    model_name: str
    parameters: Dict[str, Union[int, float, str, bool]]
    simulations: List[str] = Field(default_factory=list)


class RunRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    session_id: str
    changes: List[Change]
    edits: List[Editor] = Field(default_factory=list)


# ---------------------------
# RUN SIMULATION
# ---------------------------
@app.post("/run")
@timer
def run_simulation(req: RunRequest):
    from apsimNGpy import ApsimModel
    try:
        session = session_manager.get(req.session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session  {req.session_id} not found")

    if session.status == "expired":
        raise HTTPException(status_code=410, detail="Session expired")

    try:
        #  update activity (important for an expiration system)
        session_manager.touch(req.session_id)

        try:
            with ApsimModel(session.file_path) as model:
                if req.edits:

                    for edit in req.edits:
                        logger.info(edit.parameters)
                        model.edit_model(
                            model_type=edit.model_type,
                            model_name=edit.model_name,
                            # simulations = edit.simulations,
                            **edit.parameters
                        )
                model.run()
                df = model.results
                res = df.mean(numeric_only=True)
                session.results = res
            # session.process.wait()
            return {"status": "completed", "session_id": req.session_id}
        except Exception as e:
            raise HTTPException(500, str(e))


    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class InspectRequest(BaseModel):
    identifier: str
    model_type: str
    # parameters: List[str]


@app.post("/inspect/{session_id}")
def inspect_params(session_id, inspect_request: InspectRequest):
    from apsimNGpy import ApsimModel
    session = session_manager.get(session_id)
    # update activity (important for auto-expiration)
    session_manager.touch(session_id)
    if inspect_request.identifier:
        with ApsimModel(session.file_path) as model:
            node_id = inspect_request.identifier
            node = model.has_node(node_id, node_type=inspect_request.model_type)
            if node and isinstance(node, bool):
                obj = model.inspect_model_parameters(model_type=inspect_request.model_type, model_name=node_id,
                                                     )
            elif isinstance(node, dict, ) and node['fullpath']:
                obj = model.inspect_model_parameters_by_path(node_id)
            else:
                obj = model.inspect_model_parameters(model_type=inspect_request.model_type, model_name=node_id,
                                                     )
            return obj


# ---------------------------
# READ RESULTS
# ---------------------------
@app.get("/results/{session_id}")
def get_results(session_id: str):
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
        return session.results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
