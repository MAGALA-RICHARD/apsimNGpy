import os
import unittest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

import pandas as pd

# Import the module where APSIMNG class is define
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
        self.test_ap_sim2 = APSIMNG(model=self.model_path2)
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
        result_path = save_model_to_file(self.test_ap_sim2.Simulations, out=self.out)
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
        self.assertIsInstance(som, dict)

    def test_change_som(self):
        inrm = 105
        icnr = 29
        self.test_ap_sim.change_som(inrm=inrm, icnr=icnr)
        som = self.test_ap_sim.check_som()
        self.assertIsInstance(som, dict)
        inrmOut, icnrOut = int(som['Simulation'][0]), int(som['Simulation'][1])
        self.assertEqual(inrm, inrmOut)
        self.assertEqual(icnr, icnrOut)

    def test_clear_links(self):
        """ Test clear_links method ensures that Simulations.ClearLinks is called. """
        with patch.object(self.test_ap_sim, 'Simulations', create=True) as mock_simulations:
            mock_simulations.ClearLinks = MagicMock()
            self.test_ap_sim.clear_links()
            mock_simulations.ClearLinks.assert_called_once()

    def tearDown(self):
        if os.path.exists(self.out):
            os.remove(self.out)
        del self.test_ap_sim
        pass


if __name__ == '__main__':
    unittest.main()
