from os.path import join, realpath, dirname, exists, split, basename
from os import listdir, walk, getcwd, mkdir
import shutil
import glob

def detect_apsim_installation():
  for rr, dd, ff in walk("C:/"):
    for d  in ff:
      if d.startswith('Model')  and d.endswith(".exe"):
        f = join(rr, d)
        if f is not None:
          return f
        else:
         f= input("APSIM automatic apsim detectio failed, Please write the path to apsim installation: ")
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

class apsimx_examples:
        def __init__(self):
            for i in copied_files:
                name, ext = basename(i).split(".")
                setattr(self, name, i)
apsimx_example_data = apsimx_examples()


