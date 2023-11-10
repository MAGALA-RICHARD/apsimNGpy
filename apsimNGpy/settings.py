"""
This File is to bundle together common configurations which are required to run the simulation.
Be aware that importing this file will automatically result in execution of some functions in this and assigning
of variables in this file.

It may not be of concern, but its good to know. If running a function twice may cause undesirable side effects.
Then that function must not be called here.
"""
import os
import logging
import env
import clr
from os.path import join as opj

try:
    if pythonnet.get_runtime_info() is None:
        pythonnet.load("coreclr")
except:
    print("dotnet not found ,trying alternate runtime")
    pythonnet.load()

# logs folder
Logs = "Logs"
basedir = os.getcwd()
log_messages = opj(basedir, Logs)
if not os.path.exists(log_messages):
    os.mkdir(log_messages)
datime_now = datetime.datetime.now()
timestamp = datime_now.strftime('%a-%m-%y')
logfile_name = 'log_messages' + str(timestamp) + ".log"
log_paths = opj(log_messages, logfile_name)
# f"log_messages{datetime.now().strftime('%m_%d')}.log"
logging.basicConfig(filename=log_paths, level=logging.ERROR, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

try:
    apsim_model = os.path.realpath(get_apsimx_model_path())
except:
    apsim_model = get_apsim_path()

sys.path.append(apsim_model)

try:
    clr.AddReference("Models")
except:
    print("Looking for APSIM")
    apsim_path = shutil.which("Models")
    if apsim_path is not None:
        apsim_path = os.path.split(os.path.realpath(apsim_path))[0]
        sys.path.append(apsim_path)
    clr.AddReference("Models")

clr.AddReference("System")

DEFAULT_NUM_CORES = 6  # a default number of cores to use in simulations. Use this instead of 10.
DEFAULT_PATH = env.get('DEFAULT_PATH', r'C:\Users\rmagala\Box\p\my_PEWI\RESEARCH_PROJECT_20210622\chapter 2\YieldEvaluation')
