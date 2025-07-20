import os
import shutil

import psutil


from apsimNGpy.settings import logger
from apsimNGpy.core.base_data import load_default_simulations
from unittest import TestCase
from os import path
from pathlib import Path
from apsimNGpy.core.core import CoreModel
from abc import ABC, abstractmethod
from os import chdir as _chdir
from os import remove
import tempfile
import joblib

wd= Path.cwd() / 'apsimNGpy_tests'
def set_wd(_wd=None):
    if _wd is None:
      WD = Path.cwd() / 'apsimNGpy_tests'
    else: WD = _wd
    WD.mkdir(exist_ok=True)
    _chdir(wd)

set_wd()
TEMPS_DIR = []
temp_dir = tempfile.TemporaryDirectory()
TEMPS_DIR.append(temp_dir)
os.chdir(temp_dir.name)

joblib.dump(TEMPS_DIR, '../temps', )
from apsimNGpy.settings import SCRATCH


def get_files(pattern):
    return list(Path(SCRATCH).rglob(pattern))


def release_file_locks(_dir):
    '''it is too computationally expensive'''
    procs = psutil.process_iter()
    fd = get_files("*.apsimx")
    files = [str(i) for i in fd]
    print(files, "|||||||||||||")
    if not files:
        return None
    for proc in procs:
        try:
            for file in proc.open_files():

                if file.path in files:
                    print("Releasing file {}".format(file.path))
                    proc.terminate()
        except Exception:
            pass


class BaseTester(TestCase):
    try:
        def setUp(self):

            # Mock the model path and other attributes
            self.model_path = Path(load_default_simulations(crop='maize', simulations_object=False), )
            self.model_path2 = Path(load_default_simulations(crop='soybean', simulations_object=False), )
            self.logger = logger
            self.out_path = Path.cwd() / 'test_output.apsimx'
            self.test_ap_sim = CoreModel(model=self.model_path)

            self.out = path.realpath('test_save_output.apsimx')

        def tearDown(self):
            if path.exists(self.out):
                remove(self.out)

        @classmethod
        def setUpClass(cls):

            cls.temp_dir = temp_dir

        @classmethod
        def _tearDownClass(cls):

            try:

                cls.temp_dir.cleanup()
                shutil.rmtree(SCRATCH)
                print('Clean up completed...')
            except PermissionError:
                base = Path(wd)
                p = list(base.rglob('*.apsimx')) + list(base.rglob('*.db')) + list(base.rglob('*.db-shm'))
                for i in p:
                    try:
                        os.remove(i)
                    except PermissionError:
                        print(f'Could not remove `{i}`')

                ...
    finally:
        for temp_dir in TEMPS_DIR:
            print(temp_dir)
            ...
            # temp_dir.cleanup()
