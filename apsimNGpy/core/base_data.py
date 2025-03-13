import glob
import logging
import os
import os.path
import shutil
from os.path import join, realpath
from pathlib import Path
import uuid
from apsimNGpy.core.apsim import ApsimModel as SoilModel
from apsimNGpy.core.config import get_apsim_bin_path, apsim_version
from apsimNGpy.settings import logger
from apsimNGpy.settings import SCRATCH
WEATHER_CO = 'NewMetrrr.met'
# DATA = 'data' after tests, this did not work
WEA = 'Iem_IA0200.met'
APSIM_DATA = 'apsim'
WEATHER = 'weather'

BIN_path = get_apsim_bin_path()
# removed all other functions loading apsim files from the local repository only default apsim simulations
EXAMPLES_DATA = example_files_path = BIN_path.replace('bin', 'Examples')
version_number = apsim_version()
useVn = version_number.replace(".", "_")


def __get_example(crop, path=None, simulations_object=True):
    """
    Get an APSIM example file set_wd for a specific crop model.

    This function copies the APSIM example file for the specified crop model to the target set_wd,
    creates a SoilModel instance from the copied file, replaces its weather file with the
    corresponding weather file, and returns the SoilModel instance.

    Args:
    crop (str): The name of the crop model for which to retrieve the APSIM example.
    set_wd (str, optional): The target set_wd where the example file will be copied. Defaults to the current working dir_path.
    simulations_object (bool): Flag indicating whether to return a SoilModel instance or just the copied file set_wd.

    Returns:
    SoilModel or str: An instance of the SoilModel class representing the APSIM example for the specified crop model
                      or the set_wd to the copied file if `simulations_object` is False.

    Raises:
    OSError: If there are issues with copying or replacing files.
    """

    if not path:
        copy_path = Path(os.getcwd())
    else:
        copy_path = Path(path)

    target_path = copy_path / f"temp_{uuid.uuid1()}_{crop}.apsimx"
    target_location = glob.glob(
        f"{EXAMPLES_DATA}*/{crop}.apsimx")  # no need to capitalize only correct spelling is required
    # unzip

    if target_location:
        file_path = str(target_location[0])
        copied_file = shutil.copy2(file_path, target_path)

        if not simulations_object:
            return copied_file

        aPSim = SoilModel(file_path, out_path=target_path)
        return aPSim
    else:
        logger.info(f"No crop named:' '{crop}' found at '{example_files_path}'")


def load_default_simulations(crop: str, set_wd: [str, Path] = None,
                             simulations_object: bool = True):
    """
    Load default simulation model from aPSim folder
    :param crop: string of the crop to load e.g. Maize, not case-sensitive
    :param set_wd: string of the set_wd to copy the model
    :param simulations_object: bool to specify whether to return apsimNGp.core simulation object defaults to True
    :return: apsimNGpy.core.APSIMNG simulation objects
    #>>># Example
    # load apsimNG object directly
    >>> model = load_default_simulations('Maize', simulations_object=True)
    # try running
    >>> model.run()
    # collect the results
    >>> df = model.results
    >>> print(df)
    # just return the set_wd
    >>> model =load_default_simulations('Maize', simulations_object=False)
    >>> print(model)
    """
    # capitalize() no longer needed glob regex just matches crop if spelled correctly
    return __get_example(crop, set_wd, simulations_object)


def load_default_sensitivity_model(method: str, set_wd: str = None, simulations_object: bool = True):
    """
     Load default simulation model from aPSim folder
    :@param method: string of the sentitivity child to load e.g. "Morris" or Sobol, not case-sensitive
    :@param set_wd: string of the set_wd to copy the model
    :@param simulations_object: bool to specify whether to return apsimNGp.core simulation object defaults to True
    :@return: apsimNGpy.core.APSIMNG simulation objects
     Example
    # load apsimNG object directly
    >>> morris_model = load_default_sensitivity_model(method = 'Morris', simulations_object=True)

    # >>> morris_model.run()

    """
    dir_path = os.path.join(EXAMPLES_DATA, 'Sensitivity')
    if not set_wd:
        copy_path = Path(os.getcwd())
    else:
        copy_path = set_wd
    target_location = glob.glob(
        f"{dir_path}*/{method}.apsimx")  # no need to capitalize only correct spelling is required
    # unzip
    target_path = join(copy_path, method) + useVn + '.apsimx'
    if target_location:
        file_path = str(target_location[0])
        copied_file = shutil.copy2(file_path, target_path)

        if not simulations_object:
            return copied_file

        aPSim = SoilModel(copied_file, set_wd=set_wd)
        return aPSim
    else:
        logger.info(f"No sensitivity model for method:' '{method}' found at '{dir_path}'")


if __name__ == '__main__':
    ...
    # pp = Path('G:/ndata')
    # pp.mkdir(exist_ok=True)
    # os.chdir(pp)
    # mn = load_default_simulations('Maize', simulations_object=True)
    # mn.update_mgt(management=({"Name": 'Fertilise at sowing', 'Amount': 200}))
    # sobol = load_default_sensitivity_model(method='sobol')
    # logging.info('running sobol')
    # sobol.run('Report')
    # mn.run("Report")
if __name__ == "__main__":
        import doctest
        doctest.testmod()
