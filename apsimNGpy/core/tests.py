import glob
import os,sys
import platform
from apsimNGpy.config import Config
current_path  = os.path.dirname(os.path.abspath(__file__))

sys.path.append(current_path)
sys.path.append(os.path.dirname(current_path))
from pythonet_config import GetAPSIMPath
from core import APSIMNG
# auto detect
loaded = GetAPSIMPath()
loaded.auto_detect()
print(current_path)
if platform.system() == 'Darwin':
    # Define the pattern
    pattern = '/Applications/APSIM*.app/Contents/Resources/bin'

    # Use glob to find matching paths
    matching_paths = glob.glob(pattern)

    # Output the results
    for path in matching_paths:
        print(path)
    if path[0]:
        Config.set_aPSim_bin_path(path)





if __name__ == '__main__':

    # test
    from pathlib import Path
    from time import perf_counter

    # Model = FileFormat.ReadFromFile[Models.Core.Simulations](model, None, False)
    os.chdir(Path.home())
    from apsimNGpy.core.base_data import LoadExampleFiles, load_default_simulations

    al = LoadExampleFiles(Path.cwd())
    modelm = al.get_maize

    model = load_default_simulations(crop ='maize')
    for _ in range(1):

        for rn in ['Maize, Soybean, Wheat', 'Maize', 'Soybean, Wheat']:
            a = perf_counter()
            # model.RevertCheckpoint()

            print(model.extract_user_input('Simple Rotation'))
            b = perf_counter()

            print(b - a, 'seconds')
            model.run('report')
            print(model.results.mean(numeric_only=True))

        a = perf_counter()

        res = model.run_simulations(reports="Report", clean_up=False, results=True)
        b = perf_counter()
        print(b - a, 'seconds')
        mod = model.Simulations
        # xp = mod.FindAllInScope[Models.Manager]('Simple Rotation')
        # a = [i for i in xp]
        # for p in a:
        #  for i in range(len(p.Parameters)):
        #      kvp =p.Parameters[i]
        #      if kvp.Key == "Crops":
        #          updated_kvp = KeyValuePair[str, str](kvp.Key, "UpdatedValue")
        #          p.Parameters[i] = updated_kvp
        #      print(p.Parameters[i])
