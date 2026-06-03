from apsimNGpy.core.apsim import ApsimModel
cultivar_path_for_sowed_maize = ".Simulations.Simulation.Field.Maize.CultivarFolder.Dekalb_XL82"
with ApsimModel('Maize') as model:
    model.edit_model_by_path(
        path=cultivar_path_for_sowed_maize,
        commands='[Grain].MaximumGrainsPerCob.FixedValue',
        values=20,
        sowed=True,
        rename='edm'
    )