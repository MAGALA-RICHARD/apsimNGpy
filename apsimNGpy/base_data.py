from importlib.resources import files
from os.path import join, realpath, dirname, exists, split, basename
from os import listdir, walk, getcwd, mkdir
import shutil
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
       self.weather_example = _weather(path)
       self.maize = _get_maize_example(path)
       self.experiment_nitrogen_residue  = _get_maize_NF_experiment(path)
       self.experiment_nitrogen_residue_nt = _get_maize_NF_experiment_NT(path)
       self.swim = _get_SWIM(path)
# APSIM defaults
#TODO: incoporate other plafforms and also make it detection faster
# avoid hard codying
def detect_apsim_installation():
  for rr, dd, ff in walk("C:/"):
    for d  in ff:
      if d.startswith('Model')  and d.endswith(".exe"):
        f = join(rr, d)
        if f is not None:
          return f
        else:
         f= input("APSIM automatic apth detectio failed, Please write the path to apsim installation: ")
         return f

pat = detect_apsim_installation()
if pat:
   apsim= split(split(pat)[0])[0]
   examples = join(apsim, 'Examples')
dr = listdir(examples)
examples_files = {}
for i in dr:
    if i.endswith(".apsimx"):
        name, ext = i.split(".")
        examples_files[name] = join(examples, i)
copy_path = join(getcwd(),'apsim_default_model_examples')

if not exists(copy_path):
    mkdir(copy_path)
copied_files = [shutil.copy(file, join(copy_path, basename(file))) for file in list(examples_files.values())]

class detect_apsimx_examples:
        def __init__(self):
            for i in copied_files:
                name, ext = basename(i).split(".")
                setattr(self, name, i)
apsimx_default_examples = detect_apsimx_examples()



