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


class load_example_files():
    def __init__(self, path):
        """
        path: string pathlike object where to copy the default example to
        """
        if not exists(path):
            raise NameError ("entered path does not exists please try again, \n ============================")
        else:
          self.path = path

    def _clean_up(self, path):
        Path(f"{path}.db").unlink(missing_ok=True)
        Path(f"{path}.db-shm").unlink(missing_ok=True)
        Path(f"{path}.db-wal").unlink(missing_ok=True)
        return path

    @property
    def get_maize_with_cover_crop(self):
        self.weather_example = _weather(self.path)
        return self._clean_up(_get_maize_example(self.path))

    @property
    def get_experiment_nitrogen_residue(self):
        self.weather_example = _weather(self.path)
        return self._clean_up(_get_maize_NF_experiment(self.path))

    @property
    def get_get_experiment_nitrogen_residue_NT(self):
        self.weather_example = _weather(self.path)
        return self._clean_up(_get_maize_NF_experiment_NT(self.path))

    @property
    def get_swim(self):
        self.weather_example = _weather(self.path)
        return self._clean_up(_get_SWIM(self.path))

    @property
    def get_maize(self):
        self.weather_example = _weather(self.path)
        return self._clean_up(_get_maize(self.path))

    @property
    def get_maize_no_till(self):
        self.weather_example = _weather(self.path)
        return self._clean_up(_get_maize_no_till(self.path))



try:
   pat = os.environ['APSIM']
except KeyError:
    pat = get_apsim_path()


if pat:
    apsim =os.path.dirname(pat)
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


class DetectApsimExamples:
    def __init__(self):
        for name, file in examples_files.items():
            setattr(self, name, name)

    def get_example(self, crop):
        path = join(copy_path, crop) + '.apsimx'
        cp = shutil.copy(examples_files[crop], path)
        apsim = SoilModel(cp)
        wp = os.path.join(weather_path, os.path.basename(apsim.show_met_file_in_simulation()))
        apsim.replace_met_file(wp)
        return apsim


apsim_example = DetectApsimExamples()
