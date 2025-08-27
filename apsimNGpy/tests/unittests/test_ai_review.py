import os
import unittest
from pathlib import Path
from typing import Set

import pandas as pd

from apsimNGpy.core.config import apsim_version, stamp_name_with_version
from apsimNGpy.core.core import CoreModel, Models
from apsimNGpy.core.model_tools import find_model, validate_model_obj, find_child
from apsimNGpy.tests.unittests.base_unit_tests import BaseTester
from apsimNGpy.core.base_data import load_default_simulations
from apsimNGpy.core.pythonet_config import is_file_format_modified

IS_NEW_APSIM = is_file_format_modified()
RUN_ONLINE = os.getenv("APSIM_ONLINE_TESTS") == "1"


class TestCoreModel(BaseTester):
    """Unit tests for CoreModel and related helper utilities."""

    @classmethod
    def setUpClass(cls):
        # Use a temporary working area per test class
        cls._tmpdir = Path.cwd() / "test_core_tmp"
        cls._tmpdir.mkdir(parents=True, exist_ok=True)

        # Avoid mutating global CWD for the process; keep a reference
        cls._old_cwd = Path.cwd()
        os.chdir(cls._tmpdir)

        cls.VERSION = apsim_version()

    @classmethod
    def tearDownClass(cls):
        # Restore original CWD
        os.chdir(cls._old_cwd)

        # Best-effort cleanup of temp folder if empty
        try:
            cls._tmpdir.rmdir()
        except OSError:
            # Directory not empty or in use; leave it
            pass

    def setUp(self):
        # Track every path we create so tearDown can clean it
        self.paths: Set[Path] = set()

        # Precompute filenames (stamped)
        self.user_file_name = Path(
            stamp_name_with_version(os.path.realpath("test_core_model.apsimx"))
        )
        self.weather_file_nasa = Path(os.path.realpath("test_met_nasa.met"))
        self.weather_file_daymet = Path(os.path.realpath("test_met_daymet.met"))
        self.test_user_out_path = os.path.realpath("test_user_file_name.apsimx")
        self.test_user_out_path_stamped = stamp_name_with_version(self.test_user_out_path)


        self.model = "Maize"
        self.test_ap_sim = CoreModel(self.model, out_path=str(self.user_file_name))

        # Register files for cleanup (some may be created later)
        self.paths.update(
            {
                self.user_file_name,
                self.weather_file_nasa,
                self.weather_file_daymet,
                self.test_user_out_path,
            }
        )

    def tearDown(self):
        # Clean model artifacts
        try:
            self.test_ap_sim.clean_up()
        except Exception:
            pass

        # Delete any files we created
        for p in list(self.paths):
            try:
                if Path(p).exists():
                    os.remove(p)
            except Exception:
                # Ignore stubborn files; test should still conclude
                pass

    # ---------------- Core path/output tests ----------------

    def test_out_path(self):
        """User-specified output path is respected and non-empty."""
        if os.path.exists(self.test_user_out_path_stamped):
            os.remove(self.test_user_out_path_stamped)

        model = CoreModel(self.model, out_path=str(self.test_user_out_path))
        print(model.path, 'from model')
        print(self.test_user_out_path)
        self.paths.add(Path(model.path))

        self.assertEqual(str(model.path), str(self.test_user_out_path_stamped))
        self.assertGreater(Path(self.test_user_out_path_stamped).stat().st_size, 0, "out_path is empty")

        model.clean_up()

    def test_random_out_path(self):
        """Random output path is created when not provided."""
        model = CoreModel(self.model, out_path=None)
        self.paths.add(Path(model.path))
        self.assertTrue(Path(model.path).exists())
        model.clean_up()

    # ---------------- Running & results ----------------

    def test_run(self):
        """Run with list and string report names; confirm DataFrame results."""
        self.test_ap_sim.run(report_name=["Report"])
        self.assertIsInstance(
            self.test_ap_sim.results, pd.DataFrame, "Expected DataFrame with list report_name"
        )

        self.test_ap_sim.run(report_name="Report", verbose=False)
        df = self.test_ap_sim.results
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty, "Model ran, but results are empty")
        self.assertTrue(self.test_ap_sim.ran_ok, f"Run failed: {repr(self.test_ap_sim)}")

        self.paths.add(self.user_file_name)

    def test_get_simulated_output(self):
        """get_simulated_output returns a DataFrame after run."""
        self.test_ap_sim.run()
        if not self.test_ap_sim.ran_ok:
            self.skipTest("Model did not run successfully; skipping output test.")
        repos = self.test_ap_sim.get_simulated_output(report_names="Report")
        self.assertIsInstance(repos, pd.DataFrame, f"Expected DataFrame, got {type(repos)}")

    # ---------------- Inspection helpers ----------------

    def test_get_reports(self):
        self.assertIsInstance(self.test_ap_sim.inspect_model("Report"), list)

    def test_inspect_clock(self):
        self.assertIsInstance(self.test_ap_sim.inspect_model("Clock"), list)

    def test_inspect_simulation(self):
        self.assertIsInstance(
            self.test_ap_sim.inspect_model("Models.Core.Simulation", fullpath=False), list
        )

    def test_find_simulations(self):
        """find_simulations works with None, str, tuple, and list."""
        sim = "Simulation"
        msg = f"find_simulations failed to return requested simulation object: {sim}"

        self.assertTrue(self.test_ap_sim.find_simulations(), msg=msg)
        self.assertTrue(self.test_ap_sim.find_simulations(simulations=sim), msg=msg)
        self.assertTrue(self.test_ap_sim.find_simulations(simulations=(sim,)), msg=msg)
        self.assertTrue(self.test_ap_sim.find_simulations(simulations=[sim]), msg=msg)

    # ---------------- Management & editing ----------------

    def test_update_mgt(self):
        """update_mgt accepts a management dict/list and applies changes."""
        amount = 23.557777
        script_name = "Fertilise at sowing"

        # If your API expects a dict:
        mgt_script = {"Name": script_name, "Amount": amount}
        # If it expects a list of dicts, use: [mgt_script]

        self.test_ap_sim.update_mgt(management=mgt_script)

        value = self.test_ap_sim.inspect_model_parameters(
            "Manager", simulations="Simulation", model_name=script_name, parameters="Amount"
        )
        amount_in = float(value["Amount"])
        self.assertEqual(amount_in, amount)

    def test_replace_soil_property_values(self):
        parameter = "Carbon"
        param_values = [2.4, 1.4]

        self.test_ap_sim.replace_soil_property_values(
            parameter=parameter, param_values=param_values, soil_child="Organic"
        )

        lst = self.test_ap_sim.inspect_model_parameters(
            model_type="Organic", simulations="all", model_name="Organic", parameters="Carbon"
        )["Carbon"].tolist()

        self.assertIsInstance(lst, list, f"Expected list, got {type(lst)}")
        self.assertTrue(lst)
        self.assertEqual(
            lst[:2],
            param_values,
            f"replace_soil_property_values failed: got {lst[:2]} vs {param_values}",
        )

    def test_replace_soil_properties_by_path(self):
        param_values = [1.45, 1.95]
        self.test_ap_sim.edit_model(model_type="Organic", model_name="Organic", Carbon=param_values)

    def test_update_mgt_by_path(self):
        # fmt='.'
        path_dot = ".Simulations.Simulation.Field.Sow using a variable rule"
        self.test_ap_sim.update_mgt_by_path(path=path_dot, Population=7.5, fmt=".")
        self.test_ap_sim.run()
        self.assertTrue(self.test_ap_sim.ran_ok, "Simulation did not run for fmt='.'")

        # fmt='/'
        path_slash = "/Simulations/Simulation/Field.Sow using a variable rule"
        self.test_ap_sim.update_mgt_by_path(path=path_slash, Population=7.5, fmt="/")
        self.test_ap_sim.run()
        self.assertTrue(self.test_ap_sim.ran_ok, "Simulation did not run for fmt='/'")

    def test_create_experiment(self):
        """Creates a factorial experiment, adds a factor, and runs."""
        if IS_NEW_APSIM:
            self.skipTest("Experiment path tested elsewhere for new APSIM format.")
        else:
            self.test_ap_sim.create_experiment()
            self.test_ap_sim.add_factor(
                specification="[Fertilise at sowing].Script.Amount = 0 to 200 step 20",
                factor_name="Nitrogen",
            )
            self.test_ap_sim.run()
            self.assertTrue(self.test_ap_sim.ran_ok, "Run failed after adding experiment/factor")

    def test_add_crop_replacements(self):
        self.test_ap_sim.add_crop_replacements(_crop="Maize")
        xp = find_child(self.test_ap_sim.Simulations, child_name="Replacements", child_class="Models.Core.Folder")
        self.assertTrue(bool(xp), "Adding replacements failed")

    def test_replace_soils_values_by_path(self):
        node = ".Simulations.Simulation.Field.Soil.Organic"
        self.test_ap_sim.replace_soils_values_by_path(node_path=node, indices=[0], Carbon=1.3)
        v = self.test_ap_sim.get_soil_values_by_path(node, "Carbon")["Carbon"][0]
        self.assertEqual(v, 1.3)

    def test_add_db_table(self):
        self.test_ap_sim.add_db_table(
            variable_spec=[
                "[Clock].Today",
                "[Soil].Nutrient.TotalC[1]/1000 as SOC1",
                "[Maize].Grain.Total.Wt*10 as Yield",
            ],
            rename="report4",
            set_event_names=["[Maize].Harvesting", "[Clock].EndOfYear"],
        )

        reports = self.test_ap_sim.inspect_model("Models.Report()", fullpath=False)
        self.assertIn("report4", reports, "report4 not found in reports")

        self.test_ap_sim.run("report4")
        self.assertTrue(self.test_ap_sim.ran_ok, "Run failed after adding report table.")

    def test_loading_defaults_with(self):
        model = CoreModel(model="Maize")
        model.run()
        self.assertTrue(model.ran_ok, "Run failed after loading defaults in CoreModel.")
        self.paths.add(Path(model.path))
        model.clean_up()

    def test_edit_with_path_som(self):
        model = CoreModel(model="Maize")
        initial_ratio = 200.0
        model.edit_model_by_path(
            ".Simulations.Simulation.Field.SurfaceOrganicMatter",
            InitialCNR=initial_ratio,
            verbose=False,
        )
        icnr = model.inspect_model_parameters(
            model_type="SurfaceOrganicMatter",
            model_name="SurfaceOrganicMatter",
            parameters="InitialCNR",
        )
        self.assertEqual(
            icnr["InitialCNR"], initial_ratio, "InitialCNR not updated by edit_model_by_path"
        )
        self.paths.add(Path(model.path))
        model.clean_up()

    # ---------------- Model lookup utilities ----------------

    def test_find_models_and_validate(self):
        """find_model/validate_model_obj should resolve names & paths correctly."""
        clock_model = find_model("clock")
        validate_model_obj(clock_model)
        self.assertEqual(clock_model, Models.Clock)

        simulation_model = find_model("Simulation")
        validate_model_obj(simulation_model)
        self.assertEqual(simulation_model, Models.Core.Simulation)

        clock = validate_model_obj("Models.Clock")
        self.assertEqual(clock, Models.Clock)

        simulation = validate_model_obj("Models.Core.Simulation")
        self.assertEqual(simulation, Models.Core.Simulation)

        experiment = validate_model_obj("Experiment")
        self.assertEqual(experiment, Models.Factorial.Experiment)

        factors = validate_model_obj("Factors")
        self.assertEqual(factors, Models.Factorial.Factors)

    def test_add_model_simulation(self):
        if IS_NEW_APSIM:
            self.skipTest("Add model simulation test not applicable for new APSIM format.")
        else:
            try:
                # NOTE: keep the kwarg name consistent with your API (`adoptive_parent` vs `adaptive_parent`)
                self.test_ap_sim.add_model(
                    "Simulation",
                    adoptive_parent="Simulations",
                    rename="soybean_replaced",
                    source="Soybean",
                    override=True,
                )
                sims = self.test_ap_sim.inspect_model("Simulation", fullpath=False)
                self.assertIn("soybean_replaced", sims, "Adding simulation failed")
            finally:
                self.test_ap_sim.remove_model(model_class="Simulation", model_name="soybean_replaced")

    def test_inspect_file(self):
        inspected = self.test_ap_sim.inspect_file(console=False)
        self.assertTrue(inspected)

    # ---------------- Weather (network-dependent; optional) ----------------

    def test_get_weather_from_web_nasa(self):
        model = load_default_simulations("Maize")
        model.get_weather_from_web(
            lonlat=(-93.50456, 42.601247),
            start=1990,
            end=2001,
            source="nasa",
            filename=str(self.weather_file_nasa),
        )
        model.run()
        self.assertTrue(model.ran_ok)
        self.paths.add(Path(model.path))
        model.clean_up()

    def test_get_weather_from_web_daymet(self):
        model = load_default_simulations("Maize")
        model.get_weather_from_web(
            lonlat=(-93.50456, 42.601247),
            start=1990,
            end=2001,
            source="daymet",
            filename=str(self.weather_file_daymet),
        )
        model.run()
        self.assertTrue(model.ran_ok)
        self.paths.add(Path(model.path))
        model.clean_up()


if __name__ == "__main__":
    unittest.main()
