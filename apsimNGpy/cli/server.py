# model_server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core.base_data import load_default_simulations
from fastapi.responses import PlainTextResponse

# Dummy class to simulate your APSIM-like object
class MyModel:
    def __init__(self, name):
        self.name = name
        self.state = {"status": "initialized"}

    def run(self):
        self.state["status"] = "running"

    def stop(self):
        self.state["status"] = "stopped"

    def inspect(self):
        return self.state


# FastAPI setup
app = FastAPI()
model_instance = None

class LoadRequest(BaseModel):
    name: str

@app.post("/load")
def load_model(req: LoadRequest):
    global model_instance
    model_instance = ApsimModel(req.name) if isinstance(req.name, str) else load_default_simulations(req.name)
    return {"message": f"Model '{req.name}' loaded."}

@app.post("/run")
def run_model():
    if not model_instance:
        raise HTTPException(status_code=400, detail="Model not loaded.")
    model_instance.run()
    return {"message": "Model is running."}

@app.get("/inspect")
def inspect_model():
    if not model_instance:
        raise HTTPException(status_code=400, detail="Model not loaded.")
    return model_instance.inspect_file()



if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
