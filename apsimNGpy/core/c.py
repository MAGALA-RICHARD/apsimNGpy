from apsimNGpy.core.pythonet_config import load_pythonnet
from pathlib import Path
import os
from apsimNGpy.core_utils.database_utils import read_db_table, get_db_table_names
from APSIM.Core import Node
from apsimNGpy.core.model_loader import load_apsim_model, CastHelpers
import Models
lp = load_pythonnet()
print('running')
from apsimNGpy.core_utils.utils import timer
from apsimNGpy.core.apsim import ApsimModel

diRe = Path.home()/'test_run'
diRe.mkdir(parents=True, exist_ok=True)
os.chdir(diRe)
m_name = 'WhiteClover'
mo = load_apsim_model(m_name, out_path=diRe/f'{m_name}test_run.apsimx')
mo= load_apsim_model(model=r"C:\Users\rmagala\test_run\Maizetest_run.apsimx")
@timer
def run_model():
    # ensure file-based datastore
    sto = mo.DataStore
    print('in_memory:', sto.UseInMemoryDB)
    print('enabled:', sto.Enabled)
    print(dir(mo.DataStore))
    db_path = Path(mo.path).with_suffix(".db")
    mo.DataStore.FileName = str(db_path)

    # Clone simulations, but keep datastore attached
    cc = Node.Clone(mo.Simulations)
    sims = CastHelpers.CastAs[Models.Core.Simulations](cc.Model)

    print("Running:", sims.FileName)

    runner = Models.Core.Run.Runner(
        sims,
        runSimulations=True,
        runPostSimulationTools=False,
        runTests=False,
        wait=True,
        numberOfProcessors=6,
    )

    exc = runner.Run()
    if exc:
        print("Exception(s):", exc)

    print("Runner status:", runner.Status)
    print("DB tables:", get_db_table_names(db_path))
    if 'Report'  in get_db_table_names(db_path):
        df= read_db_table(db_path, 'Report')
        print(df.mean(numeric_only=True))
    if 'Report1' in get_db_table_names(db_path):
        df = read_db_table(db_path, 'Report1')
        print(df)

    # ⚠️ don’t dispose immediately if you want to read afterwards
    return db_path
import clr
clr.AddReference(r'D:\package\apsimNGpy\apsimNGpy\dll\ApsimRunnerBridge\bin\Release\net6.0\ApsimRunnerBridge.dll')
import ApsimRunnerBridge
RunnerBridge = ApsimRunnerBridge.Bridge
os.environ["APSIM_BIN_PATH"] = str(lp.bin_path)
db = RunnerBridge.RunApsim(r"C:\Users\rmagala\Downloads\miguez.apsimx")
print("Output DB:", db)