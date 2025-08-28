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
    def clean_up_apsim_data(self, apsimx_path) -> None:
        """
        Delete all data related to an apsimx path generated during a simulation
        @param apsimx_path: apsimx path on disk generated during simulation
        @return: None
        """
        path = Path(apsimx_path)
        db = path.with_suffix('.db')
        bak = path.with_suffix('.bak')
        db_wal = path.with_suffix('.db-wal')
        db_shm = path.with_suffix('.db-shm')
        db_csv = path.with_suffix('.Report.csv')
        clean_candidates = {bak, db, bak, db_wal, path, db_shm, db_csv}
        for candidate in clean_candidates:
            try:
                candidate.unlink(missing_ok=True)
            except PermissionError:
                pass

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
