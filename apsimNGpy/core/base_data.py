import os.path
from importlib.resources import files
from os.path import join, realpath, dirname, exists, split, basename
from os import listdir, walk, getcwd, mkdir
from apsimNGpy.core.pythonet_config import LoadPythonnet,APSIM_PATH
import shutil
from apsimNGpy import data as DATA
conf = LoadPythonnet()()
from apsimNGpy.core.apsim import ApsimModel as SoilModel
from pathlib import Path
from functools import cache
import os
WEATHER_CON = 'NewMetrrr.met'
#DATA = 'data' after tests, this did not work

APSIM_DATA = 'apsim'
WEATHER = 'weather'


def _weather(path):
    resource_directory = files(DATA)
    data_file_path = resource_directory / WEATHER / WEATHER_CON
    nameout = join(path, WEATHER_CON)
    contents = data_file_path.read_text()
    with open(nameout, "w+") as openfile:
        openfile.write(contents)
    return nameout


def _get_maize_example(file_path):
    resource_directory = files(DATA)
    json_file_path = resource_directory / APSIM_DATA / 'corn_base.apsimx'
    contents = json_file_path.read_text()
    nameout = join(file_path, 'corn_base.apsimx')
    with open(nameout, "w+") as openfile:
        openfile.write(contents)
    return nameout


def _get_maize(file_path):
    resource_directory = files(DATA)
    json_file_path = resource_directory / APSIM_DATA / 'maize.apsimx'
    contents = json_file_path.read_text()
    nameout = join(file_path, 'maize.apsimx')
    with open(nameout, "w+") as openfile:
        openfile.write(contents)
    return nameout


def _get_maize_no_till(file_path):
    resource_directory = files(DATA)
    json_file_path = resource_directory / APSIM_DATA / 'maize_nt.apsimx'
    contents = json_file_path.read_text()
    nameout = join(file_path, 'maize_nt.apsimx')
    with open(nameout, "w+") as openfile:
        openfile.write(contents)
    return nameout


def _get_maize_NF_experiment(file_path):
    """
    copies the apsimx data from 'EXPERIMENT.apsimx' file
    returns the path
    """
    resource_directory = files(DATA)
    json_file_path = resource_directory / APSIM_DATA / 'EXPERIMENT.apsimx'
    contents = json_file_path.read_text()
    nameout = join(file_path, 'EXPERIMENT.apsimx')
    with open(nameout, "w+") as openfile:
        openfile.write(contents)
    return nameout


def _get_maize_NF_experiment_NT(file_path):
    resource_directory = files(DATA)
    json_file_path = resource_directory / APSIM_DATA / 'EXPERIMENT_NT.apsimx'
    contents = json_file_path.read_text()
    nameout = join(file_path, 'EXPERIMENT_NT.apsimx')
    with open(nameout, "w+") as openfile:
        openfile.write(contents)
    return nameout


def _get_SWIM(file_path):
    resource_directory = files(DATA)
    json_file_path = resource_directory / APSIM_DATA / 'SWIM.apsimx'
    contents = json_file_path.read_text()
    nameout = join(file_path, 'SWIM.apsimx')
    with open(nameout, "w+") as openfile:
        openfile.write(contents)
    return nameout


def _clean_up(path):
    Path(f"{path}.db").unlink(missing_ok=True)
    Path(f"{path}.db-shm").unlink(missing_ok=True)
    Path(f"{path}.db-wal").unlink(missing_ok=True)
    return path


class LoadExampleFiles():
    def __init__(self, path=None):
        """
        LoadExampleFiles constructor.

        Args:
        path (str): The path where default example files will be copied to.

        Raises:
        NameError: If the specified path does not exist.
        """
        self.weather_example = None
        if path is None:
            self.path = os.getcwd()
        else:
            self.path = path

    @property
    def get_maize_with_cover_crop(self):
        """
        Get the example data for maize with a cover crop.

        Returns:
        path (str): The example data for maize with a cover crop.
                """
        self.weather_example = _weather(self.path)
        return _clean_up(_get_maize_example(self.path))

    @property
    def get_experiment_nitrogen_residue(self):
        """
        Get the example data for an experiment involving nitrogen residue.

        Returns:
        path (str): The example data for the nitrogen residue experiment.
        """
        self.weather_example = _weather(self.path)
        return _clean_up(_get_maize_NF_experiment(self.path))

    @property
    def get_get_experiment_nitrogen_residue_NT(self):
        """
        Get the example data for an experiment involving nitrogen residue with no-till.

        Returns:
        path (str): The example data for the nitrogen residue experiment with no-till.
        """
        self.weather_example = _weather(self.path)
        return _clean_up(_get_maize_NF_experiment_NT(self.path))

    @property
    def get_swim(self):
        """
        Get the example data for the SWIM model.

        Returns:
        path (str): The example data for the SWIM model.
        """
        self.weather_example = _weather(self.path)
        return _clean_up(_get_SWIM(self.path))

    @property
    def get_maize(self):
        """
        Get the example data for the maize model.

        Returns:
        path (str): The example data for the maize model.
        """
        self.weather_example = _weather(self.path)
        return _clean_up(_get_maize(self.path))

    @property
    def get_maize_no_till(self):
        """
        Get the example data for the maize model with no-till.

        Returns:
        path (str): The example data for the maize model with no-till.
        """
        self.weather_example = _weather(self.path)
        return _clean_up(_get_maize_no_till(self.path))

    @property
    def get_maize_model(self):
        """
        Get a SoilModel instance for the maize model.

        Returns: SoilModel: An instance of the SoilModel class for the maize model. Great for optimisation,
        where you wat a model always in memory to reducing laoding overload
        """
        return SoilModel(self.get_maize)

    @property
    def get_maize_model_no_till(self):
        """
        Get a SoilModel instance for the maize model with no-till.

        Returns: SoilModel: An instance of the SoilModel class for the maize model with no-till. Great for
        optimisation, where you wat a model always in memory to reducing laoding overload
        """
        return SoilModel(self.get_maize_no_till)


try:
    pat = os.environ['APSIM']
except KeyError:
    pat = APSIM_PATH
if pat:
    apsim = os.path.dirname(pat)
    examples = join(apsim, 'Examples')
dr = listdir(examples)

examples_files = {}
for i in dr:
    if i.endswith(".apsimx"):
        name, ext = i.split(".")
        examples_files[name] = join(examples, i)

weather_path = os.path.join(examples, "WeatherFiles")


class DetectApsimExamples:
    def __init__(self, copy_path: str = None):
        self.all = []
        self.copy_path = copy_path
        for name, file in examples_files.items():
            setattr(self, name, name)
            self.all.append(name)

    def get_example(self, crop):
        """
        Get an APSIM example file path for a specific crop model.

        This function copies the APSIM example file for the specified crop model to the target path,
        creates a SoilModel instance from the copied file, replaces its weather file with the
        corresponding weather file, and returns the SoilModel instance.

        Args:
        crop (str): The name of the crop model for which to retrieve the APSIM example.

        Returns: SoilModel: An instance of the SoilModel class representing the APSIM example for the specified crop
        model. the path of this model will be your current working directory

        Raises:
        OSError: If there are issues with copying or replacing files.
        """
        if not self.copy_path:
            self.copy_path = os.getcwd()
        path = join(self.copy_path, crop) + '.apsimx'
        cp = shutil.copy(examples_files[crop], path)
        apsim = SoilModel(cp)
        wp = os.path.join(weather_path, os.path.basename(apsim.show_met_file_in_simulation()))
        apsim.replace_met_file(wp)
        return apsim

    def get_all(self):
        """
            This return all files from APSIM default examples in the example folder. But for what?
        """
        return [self.get_example(i) for i in self.all]


ApsimExample = DetectApsimExamples()

if __name__ == '__main__':
    pp = Path.home()
    os.chdir(pp)
    from apsimNGpy.core.base_data import LoadExampleFiles
    maize = LoadExampleFiles()
    dt = maize.get_maize
