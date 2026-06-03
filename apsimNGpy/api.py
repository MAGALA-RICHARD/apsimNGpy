from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from apsimNGpy import ApsimModel

app = FastAPI()


class SimulationRequest(BaseModel):
    plant: str
    simulation: int = 0
    rename: str
    payload: list[dict[str, Any]] = Field(default_factory=list)


@app.post("/simulation")
def create_simulation(sim: SimulationRequest):
    try:
        with ApsimModel(sim.plant) as model:
            model.append_simulation(
                simulation=model[sim.simulation],
                payload=sim.payload,
                rename=sim.rename,
            )
            model.save()

        return {
            "status": "success",
            "message": f"Simulation '{sim.rename}' added successfully.",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))