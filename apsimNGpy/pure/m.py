PARENT_OF = {
    "Models.Core.Simulations": {"Models.Core.Simulation"},
    "Models.Core.Simulation": {
        "Models.Clock",
        "Models.Climate.Weather",
        "Models.Summary",
        "Models.Storage.DataStore",
        "Models.Report",
        "Models.MicroClimate",
        "Models.Manager",
        "Models.Operations",
        "Models.Memo",
        "Models.Core.Folder",
        "Models.Factorial.Experiment",
        "Models.Core.Zone",
    },
    "Models.Factorial.Experiment": {
        "Models.Factorial.Factors",
        "Models.Factorial.Permutation",
    },
    "Models.Core.Zone": {
        "Models.PMF.Plant",
        "Models.Soils.Soil",
        "Models.Surface.SurfaceOrganicMatter",
        "Models.Fertiliser",
        "Models.Irrigation",
    },
    "Models.PMF.Plant": {"Models.PMF.Cultivar"},
    "Models.Soils.Soil": {
        "Models.Soils.Physical",
        "Models.Soils.Organic",
        "Models.Soils.Chemical",
        "Models.WaterModel.WaterBalance",
        "Models.Soils.Water",
        "Models.Soils.Sample",
        "Models.Soils.SoilCrop",
        "Models.Soils.Solute",
        "Models.Soils.Nutrients.Nutrient",
        "Models.Soils.CERESSoilTemperature",
    },
}


from collections import defaultdict

schemas = {
 'Models.Climate.Weather, Models', 'Models.Clock, Models',
 'Models.Core.Folder, Models', 'Models.Core.Simulation, Models',
 'Models.Core.Simulations, Models', 'Models.Core.Zone, Models',
 'Models.Factorial.Experiment, Models', 'Models.Factorial.Factors, Models',
 'Models.Factorial.Permutation, Models', 'Models.Fertiliser, Models',
 'Models.Irrigation, Models', 'Models.Manager, Models', 'Models.Memo, Models',
 'Models.MicroClimate, Models', 'Models.Operations, Models',
 'Models.PMF.Cultivar, Models', 'Models.PMF.Plant, Models',
 'Models.Report, Models', 'Models.Soils.Arbitrator.SoilArbitrator, Models',
 'Models.Soils.CERESSoilTemperature, Models', 'Models.Soils.Chemical, Models',
 'Models.Soils.Nutrients.Nutrient, Models', 'Models.Soils.Organic, Models',
 'Models.Soils.Physical, Models', 'Models.Soils.Sample, Models',
 'Models.Soils.Soil, Models', 'Models.Soils.SoilCrop, Models',
 'Models.Soils.Solute, Models', 'Models.Soils.Water, Models',
 'Models.Storage.DataStore, Models', 'Models.Summary, Models',
 'Models.Surface.SurfaceOrganicMatter, Models', 'Models.WaterModel.WaterBalance, Models'
}

def clean(s):  # drop trailing ", Models"
    return s.split(",")[0].strip()

by_ns = defaultdict(list)
for s in map(clean, schemas):
    parts = s.split(".")
    ns = ".".join(parts[:2]) if len(parts) > 2 else parts[0]   # e.g., "Models.Core"
    by_ns[ns].append(s)

# Pretty print by namespace
for ns in sorted(by_ns):
    print(f"{ns}:")
    for t in sorted(by_ns[ns]):
        print(f"  - {t}")

print("\nSuggested parents:")
for s in sorted(map(clean, schemas)):
    parent = next((p for p, kids in PARENT_OF.items() if s in kids), None)
    print(f"{s}  ←  {parent or '(attach under Simulation)'}")



from apsimNGpy.pure import models

prop = dir(models)
data=  set()
for i in prop:
    mo = getattr(models, i)
    if hasattr(mo, 'Schema'):
        print(i, mo.Schema)
        data.add(mo.Schema)
