import os
from apsimNGpy.settings import logger
from apsimNGpy.core.base_data import load_default_simulations
from unittest import TestCase
from os import path
from pathlib import Path
from apsimNGpy.core.core import APSIMNG
from abc import ABC, abstractmethod
from os import chdir as _chdir
from os import remove
import tempfile
wd = Path.cwd() / 'apsimNGpy_tests'

wd.mkdir(exist_ok=True)
#_chdir(wd)
temp_dir = tempfile.TemporaryDirectory()
os.chdir(temp_dir.name)

class BaseTester(TestCase):

    def setUp(self):
        # Mock the model path and other attributes
        self.model_path = Path(load_default_simulations(crop='maize', simulations_object=False))
        self.model_path2 = Path(load_default_simulations(crop='soybean', simulations_object=False))
        self.logger= logger
        self.out_path = Path.cwd() / 'test_output.apsimx'
        self.test_ap_sim = APSIMNG(model=self.model_path)

        self.out = path.realpath('test_save_output.apsimx')

    def tearDown(self):
        if path.exists(self.out):
            remove(self.out)



