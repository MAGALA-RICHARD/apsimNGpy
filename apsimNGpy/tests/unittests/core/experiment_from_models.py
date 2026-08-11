from pathlib import Path
from uuid import uuid4

from apsimNGpy.core.apsim import ApsimModel

from apsimNGpy.core.experiment import create_experiment_from_models, create_experiment_from_file
from apsimNGpy.core.experiment_tools import factor_spec
import unittest


class TestExperimentFromModels(unittest.TestCase):
    def test_experiment_from_models(self):
        experiment = create_experiment_from_models(
            model="Maize",
            specifications=factor_spec(
                "Maize",
                param_node_location="Sow using a variable rule",
                node_type="Manager",
                param_identifier="Population",
                values=[6, 10, 14],
                rename="population",
            ),
        )
        self.assertEqual(True, hasattr(experiment, "n_factors"))
        self.assertEqual(1, experiment.n_factors)
        experiment.run()
        df = experiment.results
        self.assertEqual(df.SimulationID.nunique(), 3)

    def test_experiment_from_file(self):
        csf_file_name = f'tmp_{uuid4()}.csv'
        try:
            from apsimNGpy.core.sim_tools import create_factor_table
            vals = {"[Maize].Leaf.Photosynthesis.RUE.FixedValue": (1, 3, 2.5),
                    '[Sow using a variable rule].Script.Population': (1, 12, 6)}
            X = create_factor_table(**vals, name_column='FactorFromFile')
            X.to_csv(csf_file_name)
            model = create_experiment_from_file(
                model="Maize",
                experiment_from_file=csf_file_name,
                name_column="FactorFromFile",

            )
            model.run()
            df = model.results
            self.assertEqual(df.FactorFromFile.nunique(), 3)
        finally:
            Path(csf_file_name).unlink(missing_ok=True)

    def assert_raises_FileNotFoundError(self):
        with self.assertRaises(FileNotFoundError):
            model = create_experiment_from_file(
                model="Maize",
                experiment_from_file="factors.xlsx",
                name_column="Treatment",
                sheet="SobolSamples",
            )

    def test_experiment_from_apsimx_many_simulations(self):
        with ApsimModel('Maize') as model:
            create_experiment_from_models(
                model=model,
                specifications=factor_spec(
                    "Maize",
                    param_node_location="Sow using a variable rule",
                    node_type="Manager",
                    param_identifier="Population",
                    values=[6, 10, 14],
                    rename="population",
                ),

            )

    def test_experiment_from_apsim_model(self):
        with ApsimModel('Maize') as model:
            # add more simulation
            model.clone_simulation(rename='sim2', base_simulation=0)
            model.clone_simulation(rename='sim3', base_simulation=0)
            assert len(model) == 3, 'Cloning simulation was not successful'
            experiment = create_experiment_from_models(
                model=model,
                specifications=factor_spec(
                    "Maize",
                    param_node_location="Sow using a variable rule",
                    node_type="Manager",
                    param_identifier="Population",
                    values=[6, 10, 14],
                    rename="population",
                ),
                base_simulation=2
            )
            self.assertEqual(True, hasattr(experiment, "n_factors"))
            self.assertEqual(1, experiment.n_factors)
            experiment.run()
            df = experiment.results
            self.assertEqual(df.SimulationID.nunique(), 3)

    def test_raises_index_error_when_base_simulation_not_found(self):
        with self.assertRaises(IndexError):
            create_experiment_from_models(
                model="Maize",
                specifications=factor_spec(
                    "Maize",
                    param_node_location="Sow using a variable rule",
                    node_type="Manager",
                    param_identifier="Population",
                    values=[6, 10, 14],
                    rename="population",
                ),
                base_simulation=2
            )


if __name__ == "__main__":
    unittest.main()
