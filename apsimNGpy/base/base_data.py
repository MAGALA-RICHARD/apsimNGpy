import os.path
from importlib.resources import files
from os.path import join, realpath, dirname, exists, split, basename
from os import listdir, walk, getcwd, mkdir
from apsimNGpy.model.soilmodel import SoilModel
import shutil
from apsimNGpy.utililies.pythonet_config import get_apsim_path

from pathlib import Path
from functools import cache
import glob

wp = 'NewMetrrr.met'


def _weather(path):
    resource_directory = files('apsimNGpy')
    data_file_path = resource_directory / 'basefiles' / wp
    nameout = join(path, wp)
    contents = data_file_path.read_text()
    with open(nameout, "w+") as openfile:
        openfile.write(contents)
    return nameout


def _get_maize_example(file_path):
    resource_directory = files('apsimNGpy')
    json_file_path = resource_directory / 'basefiles' / 'corn_base.apsimx'
    contents = json_file_path.read_text()
    nameout = join(file_path, 'corn_base.apsimx')
    with open(nameout, "w+") as openfile:
        openfile.write(contents)
    return nameout


def _get_maize(file_path):
    resource_directory = files('apsimNGpy')
    json_file_path = resource_directory / 'basefiles' / 'maize.apsimx'
    contents = json_file_path.read_text()
    nameout = join(file_path, 'maize.apsimx')
    with open(nameout, "w+") as openfile:
        openfile.write(contents)
    return nameout


def _get_maize_no_till(file_path):
    resource_directory = files('apsimNGpy')
    json_file_path = resource_directory / 'basefiles' / 'maize_nt.apsimx'
    contents = json_file_path.read_text()
    nameout = join(file_path, 'maize_nt.apsimx')
    with open(nameout, "w+") as openfile:
        openfile.write(contents)
    return nameout


def _get_maize_NF_experiment(file_path):
    resource_directory = files('apsimNGpy')
    json_file_path = resource_directory / 'basefiles' / 'EXPERIMENT.apsimx'
    contents = json_file_path.read_text()
    nameout = join(file_path, 'EXPERIMENT.apsimx')
    with open(nameout, "w+") as openfile:
        openfile.write(contents)
    return nameout


def _get_maize_NF_experiment_NT(file_path):
    resource_directory = files('apsimNGpy')
    json_file_path = resource_directory / 'basefiles' / 'EXPERIMENT_NT.apsimx'
    contents = json_file_path.read_text()
    nameout = join(file_path, 'EXPERIMENT_NT.apsimx')
    with open(nameout, "w+") as openfile:
        openfile.write(contents)
    return nameout


def _get_SWIM(file_path):
    resource_directory = files('apsimNGpy')
    json_file_path = resource_directory / 'basefiles' / 'SWIM.apsimx'
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
    def __init__(self, path):
        """
        LoadExampleFiles constructor.

        Args:
        path (str): The path where default example files will be copied to.

        Raises:
        NameError: If the specified path does not exist.
        """
        if not exists(path):
            raise NameError("entered path does not exists please try again, \n ============================")
        else:
            self.path = path

    @property
    def get_maize_with_cover_crop(self):
        """
        Get the example data for maize with a cover crop.

        Returns:
        str: The example data for maize with a cover crop.
                """
        self.weather_example = _weather(self.path)
        return _clean_up(_get_maize_example(self.path))

    @property
    def get_experiment_nitrogen_residue(self):
        """
        Get the example data for an experiment involving nitrogen residue.

        Returns:
        str: The example data for the nitrogen residue experiment.
        """
        self.weather_example = _weather(self.path)
        return _clean_up(_get_maize_NF_experiment(self.path))

    @property
    def get_get_experiment_nitrogen_residue_NT(self):
        self.weather_example = _weather(self.path)
        return _clean_up(_get_maize_NF_experiment_NT(self.path))

    @property
    def get_swim(self):
        self.weather_example = _weather(self.path)
        return _clean_up(_get_SWIM(self.path))

    @property
    def get_maize(self):
        self.weather_example = _weather(self.path)
        return _clean_up(_get_maize(self.path))

    @property
    def get_maize_no_till(self):
        self.weather_example = _weather(self.path)
        return _clean_up(_get_maize_no_till(self.path))

    def get_maize_model(self):
        return SoilModel(self.get_maize)

    def get_maize_model_no_till(self):
        return SoilModel(self.get_maize_no_till)


try:
    pat = os.environ['APSIM']
except KeyError:
    pat = get_apsim_path()

if pat:
    apsim = os.path.dirname(pat)
    examples = join(apsim, 'Examples')
dr = listdir(examples)

examples_files = {}
for i in dr:
    if i.endswith(".apsimx"):
        name, ext = i.split(".")
        examples_files[name] = join(examples, i)
copy_path = join(getcwd(), 'apsim_default_model_examples')

if not exists(copy_path):
    mkdir(copy_path)

weather_path = os.path.join(examples, "WeatherFiles")

pp = Path.home()
os.chdir(pp)


class DetectApsimExamples:
    def __init__(self):
        self.all = []
        for name, file in examples_files.items():
            setattr(self, name, name)
            self.all.append(name)

    def get_example(self, crop):
        path = join(copy_path, crop) + '.apsimx'
        cp = shutil.copy(examples_files[crop], path)
        apsim = SoilModel(cp)
        wp = os.path.join(weather_path, os.path.basename(apsim.show_met_file_in_simulation()))
        apsim.replace_met_file(wp)
        return apsim

    def get_all(self):
        return [self.get_example(i) for i in self.all]


ApsimExample = DetectApsimExamples()
