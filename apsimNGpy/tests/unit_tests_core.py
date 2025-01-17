import os
import unittest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
import shutil
import pandas as pd

# Import the module where APSIMNG class is defined
from apsimNGpy.core.core import APSIMNG, save_model_to_file
from apsimNGpy.core.model_loader import save_model_to_file

wd = Path.cwd() / 'apsimNGpy_tests'
wd.mkdir(exist_ok=True)
os.chdir(wd)


class TestAPSIMNG(unittest.TestCase):

    def setUp(self):
        from apsimNGpy.core.base_data import load_default_simulations
        # Mock the model path and other attributes
        self.model_path = Path(load_default_simulations(crop='maize', simulations_object=False))
        self.model_path2 = Path(load_default_simulations(crop='soybean', simulations_object=False))
        self.out_path = Path.cwd() / 'test_output.apsimx'
        # self.out_path.mkdir(parents=True, exist_ok=True)
        # self.out_path.mkdir(parents=True, exist_ok=True)
        self.test_ap_sim = APSIMNG(model=self.model_path)

        self.out = os.path.realpath('test_save_output.apsimx')

    def test_run(self):
        """ Test the run method's behavior under normal conditions. """
        with patch.object(self.test_ap_sim, '_DataStore', create=True) as mock_datastore:
            mock_datastore.Open = MagicMock()
            mock_datastore.Close = MagicMock()
            # test if dictionary is returned
            self.test_ap_sim.run(get_dict=True)
            self.assertIsInstance(self.test_ap_sim.results, dict)
            # check is a list is returned if a user passes a tuple or  alist of report names
            self.test_ap_sim.run(report_name=['Report'], get_dict=False)  # false is the default
            self.assertIsInstance(self.test_ap_sim.results, list)
            # one more test
            # check if the use pass  report name as str a strict a pandas.core.frame.DataFrame' is returned
            self.test_ap_sim.run(report_name='Report', get_dict=False)
            df = self.test_ap_sim.results
            self.assertIsInstance(df, pd.DataFrame)
            # check if it is not empty
            self.assertEqual(df.empty, False)
            self.assertTrue(mock_datastore.Open.called)
            self.assertTrue(mock_datastore.Close.called)

    def test_save_edited_file(self, ):
        result_path = save_model_to_file(self.test_ap_sim.Simulations, out=self.out)
        isfile = os.path.isfile(result_path)
        self.assertEqual(isfile, True)

    def test_update_mgt(self):
        """ Test the update method's behavior under"""
        Amount = 23.557777
        script_name = 'Fertilise at sowing'
        mgt_script = {'Name': script_name, 'Amount': Amount},
        self.test_ap_sim.update_mgt(management=mgt_script)
        # extract user infor
        amountIn = float(self.test_ap_sim.extract_user_input(script_name)['Simulation']['Amount'])
        self.assertEqual(amountIn, Amount)

    def test_check_som(self):
        som = self.test_ap_sim.check_som()
        self.assertIsInstance(som, dict, 'check_som should return a dictionary')

    def test_change_som(self):
        inrm = 105
        icnr = 29
        self.test_ap_sim.change_som(inrm=inrm, icnr=icnr)
        som = self.test_ap_sim.check_som()
        self.assertIsInstance(som, dict)
        inrmOut, icnrOut = int(som['Simulation'][0]), int(som['Simulation'][1])
        self.assertEqual(inrm, inrmOut, msg='inrm are not equal possibly change_som was not successful')
        self.assertEqual(icnr, icnrOut, msg='icnr are not equal possibly change_som was not successful')

    def test_clear_links(self):
        """ Test clear_links method ensures that Simulations.ClearLinks is called. """
        with patch.object(self.test_ap_sim, 'Simulations', create=True) as mock_simulations:
            mock_simulations.ClearLinks = MagicMock()
            self.test_ap_sim.clear_links()
            mock_simulations.ClearLinks.assert_called_once()

    def test_find_simulations(self):
        """ Test find_simulations based on three input None, lists and string"""
        # test None
        sim = 'Simulation'
        MSG = f'test_find_simulations failed to return requested simulation object: {sim}'
        self.assertTrue(self.test_ap_sim.find_simulations(simulations=None), msg=MSG)
        # test str
        self.assertTrue(self.test_ap_sim.find_simulations(simulations=sim), msg=MSG)
        # test tuple

        self.assertTrue(self.test_ap_sim.find_simulations(simulations=(sim,)), msg=MSG)
        # test list input
        self.assertTrue(self.test_ap_sim.find_simulations(simulations=[sim]), msg=MSG)

    def test_load_simulated_results(self):
        """ Test load_simulated_results"""
        repos = self.test_ap_sim.load_simulated_results()
        msG = f"expected dictionary but received {type(repos)}"
        self.assertIsInstance(repos, dict, msg=msG)
        # test if dict not empty
        msG = 'expected dict is empty'
        self.assertTrue(self.test_ap_sim.load_simulated_results(), msg=msG)

    def test_get_reports(self):
        self.assertIsInstance(self.test_ap_sim.get_report(names_only=True), dict)

    def test_replace_soil_property_values(self):
        parameter = 'Carbon'
        param_values = [2.4, 1.4]
        self.test_ap_sim.replace_soil_property_values(parameter=parameter, param_values=param_values,
                                                      soil_child='Organic', )
        lisT = self.test_ap_sim.extract_soil_property_by_path(path='Simulation.Organic.Carbon', index =[0,1])
        self.assertIsInstance(lisT, list, msg='expected a list got {}'.format(type(lisT)))
        self.assertTrue(lisT)
        self.assertIsInstance(lisT, list, msg='expected a list got {}'.format(type(lisT)))
        self.assertTrue(lisT)
        # if it was successful
        testP = self.test_ap_sim.extract_soil_property_by_path(path = 'Simulation.Organic.Carbon', index=[0,1])
        self.assertEqual(lisT, param_values, msg = f'replace_soil_property_values was not successful returned {testP}\n got {param_values}')

    def test_replace_soil_properties_by_path(self):
        path = 'None.Soil.physical.None.None.BD'
        param_values = [1.45, 1.95]
        self.test_ap_sim.replace_soil_properties_by_path(path=path, param_values=param_values)

    def test_extract_soil_property_by_path(self):
        lisT = self.test_ap_sim.extract_soil_property_by_path(path='Simulation.Physical.BD')
        self.assertIsInstance(lisT, list, msg='expected a list got {}'.format(type(lisT)))
        self.assertTrue(lisT)

    def tearDown(self):
        if os.path.exists(self.out):
            os.remove(self.out)
        del self.test_ap_sim


if __name__ == '__main__':
    unittest.main()
