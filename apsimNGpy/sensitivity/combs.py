from itertools import product
import json
from pathlib import Path

comb_json = "comb.json"

crop_rotations = ("Maize", "Maize, Wheat")
nitrogen = (0, 84, 252)

cbs = product(crop_rotations, nitrogen)


def add_comb_json(comb):
    jp = Path(comb_json)

    if jp.exists():
        with open(jp, "r") as f:
            completed = json.load(f)
    else:
        completed = {"completed": []}

    completed["completed"].append(comb)

    with open(jp, "w") as f:
        json.dump(completed, f, indent=4)