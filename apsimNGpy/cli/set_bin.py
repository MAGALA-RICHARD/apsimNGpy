from fastapi import FastAPI, HTTPException, Query
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core_utils.utils import timer
from apsimNGpy.core.config import (
    set_apsim_bin_path,
    get_apsim_bin_path,
    auto_detect_apsim_bin_path,
)
from apsimNGpy.core.runner import get_apsim_version
from os import path
from pydantic import BaseModel
import os
app = FastAPI(title="APSIM Binary Manager API")


@app.get("/set-path")
def set_bin_path(update: str = Query(..., description="Path to set as APSIM bin path")):
    if not path.exists(update):
        raise HTTPException(status_code=400, detail=f"Path '{update}' does not exist.")
    set_apsim_bin_path(update)
    return {"message": f"Updated APSIM bin path to: {update}"}


@app.get("/get-path")
def show_bin_path():
    cbp = get_apsim_bin_path()
    return {"current_bin_path": cbp}


@app.get("/auto-detect")
def auto_search_path():
    auto = auto_detect_apsim_bin_path()
    if not auto:
        raise HTTPException(status_code=404, detail="No APSIM bin path detected.")
    return {"detected_path": auto}


@app.get("/version")
def get_version():
    version = get_apsim_version()
    return {"apsim_version": version}

model = None

class LoadRequest(BaseModel):
    name: str

@app.post("/load")
def load_model(req: LoadRequest):
    global model
    model = ApsimModel(req.name)
    return {"message": f"Model '{req.name}' loaded."}
@app.post("/inspect")
def inspect(_model:str):
    insp = model.inspect_model(_model)
    return {"model_inspect": insp}
@app.post("/run")
def run_model():
    if not model:
        raise HTTPException(status_code=400, detail="Model not loaded.")
    model.run(verbose=True)
    model.results.to_csv('m.csv')
    os.startfile('m.csv')
    return {"message": "Model is running."}

def fast():
    import uvicorn
    uvicorn.run("apsimNGpy.cli.set_bin:app", host="127.0.0.1", port=8000, reload=True)


