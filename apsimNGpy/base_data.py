import os
from importlib.resources import files
wp = 'NewMetrrr.met'
def _weather(path):
    resource_directory = files('apsimNGpy')
    data_file_path = resource_directory / 'basefiles' / wp
    nameout = os.path.join(path, wp)
    contents = data_file_path.read_text()
    with open(nameout, "w+") as openfile:
        openfile.write(contents)
    return nameout

def _get_maize_example(file_path):
    resource_directory = files('apsimNGpy')
    json_file_path = resource_directory / 'basefiles' / 'corn_base.apsimx'
    contents = json_file_path.read_text()
    nameout = os.path.join(file_path, 'corn_base.apsimx')
    with open(nameout, "w+") as openfile:
        openfile.write(contents)
    return nameout

def _get_maize_NF_experiment(file_path):
    resource_directory = files('apsimNGpy')
    json_file_path = resource_directory / 'basefiles' / 'EXPERIMENT.apsimx'
    contents = json_file_path.read_text()
    nameout = os.path.join(file_path, 'EXPERIMENT.apsimx')
    with open(nameout, "w+") as openfile:
        openfile.write(contents)
    return nameout
def _get_maize_NF_experiment_NT(file_path):
    resource_directory = files('apsimNGpy')
    json_file_path = resource_directory / 'basefiles' / 'EXPERIMENT_NT.apsimx'
    contents = json_file_path.read_text()
    nameout = os.path.join(file_path, 'EXPERIMENT_NT.apsimx')
    with open(nameout, "w+") as openfile:
        openfile.write(contents)
    return nameout
def _get_SWIM(file_path):
    resource_directory = files('apsimNGpy')
    json_file_path = resource_directory / 'basefiles' / 'SWIM.apsimx'
    contents = json_file_path.read_text()
    nameout = os.path.join(file_path, 'SWIM.apsimx')
    with open(nameout, "w+") as openfile:
        openfile.write(contents)
    return nameout

class load_example_files():
    def __init__(self, path):
       """
        path: string pathlike object where to copy the default example to
        """
       self.weather_example = _weather(path)
       self.maize = _get_maize_example(path)
       self.experiment_nitrogen_residue  = _get_maize_NF_experiment_NT(path)
       self.experiment_nitrogen_residue_nt = _get_maize_NF_experiment_NT(path)
       self.swim = _get_SWIM(path)

