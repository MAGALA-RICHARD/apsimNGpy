import os
import tempfile
from abc import ABC, abstractmethod
from os import chdir as _chdir
from os import path
from pathlib import Path
from unittest import TestCase

import joblib

from apsimNGpy.core.base_data import load_default_simulations
from apsimNGpy.core.core import CoreModel
from apsimNGpy.settings import logger

wd = Path.cwd() / 'apsimNGpy_tests'

from apsimNGpy.settings import SCRATCH


def get_files(pattern):
    return list(Path(SCRATCH).rglob(pattern))


class BaseTester(TestCase, ABC):

    # def setUp(self):
    #     # Mock the model path and other attributes
    #     self.model_path = Path(load_default_simulations(crop='Maize', simulations_object=False), )
    #     self.model_path2 = Path(load_default_simulations(crop='Soybean', simulations_object=False), )
    #     self.logger = logger
    #     self.out_path = Path.cwd() / 'test_output.apsimx'
    #     self.test_ap_sim = CoreModel(model=self.model_path)
    #
    #     self.out = path.realpath('test_save_output.apsimx')

    # ensure all child classes implement teardown
    @abstractmethod
    def tearDown(self):
        pass

    @staticmethod
    def set_wd(_wd=None):
        if _wd is None:
            WD = Path.cwd() / 'apsimNGpy_tests'
        else:
            WD = _wd
        WD.mkdir(exist_ok=True)
        _chdir(wd)
