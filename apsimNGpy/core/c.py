import unittest
from functools import lru_cache
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from apsimNGpy.core.config import apsim_version, stamp_name_with_version
from apsimNGpy.core.core import CoreModel, Models
from apsimNGpy.core.model_tools import find_model, validate_model_obj, find_child
from apsimNGpy.settings import logger
from apsimNGpy.tests.unittests.base_unit_tests import BaseTester
from apsimNGpy.core.base_data import load_default_simulations
from apsimNGpy.core.pythonet_config import is_file_format_modified
with CoreModel('Maize') as model:
    model.run(verbose=True)

    print('Path exists before exit:', Path(model.path).exists())
    print('datastore Path exists before exit:', Path(model.datastore).exists())
print('Path exists after exit:', Path(model.path).exists())
print('datastore Path exists after exit:', Path(model.datastore).exists())