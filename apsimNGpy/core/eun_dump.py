from apsimNGpy import timer, load_crop_from_disk, ApsimModel, get_node_by_path, configuration
from pathlib import Path
from Models.Core.Run import Runner
from APSIM.Core import Node
from Models.Storage import DataStore
from apsimNGpy import CLR

RunTypeEnum = Runner.RunTypeEnum


def run_apsim_simulation(fp, simulation_names=None):
    fp = str(Path(fp).resolve())

    # 🔹 Load raw model
    read = CLR.get_file_reader(method='file')
    sims = read[CLR.Models.Core.Simulations](fp, None, True)

    if sims is None:
        raise RuntimeError("Failed to load APSIM file")

    sims.FileName = fp

    # 🔥 STEP 1: Build APSIM graph (CRITICAL)

    model = sims.Model

    # 🔥 STEP 2: Fix DataStore AFTER Node.Create
    stores = get_node_by_path(sims, node_path=f'.{sims.Name}.DataStore', cast_as='auto')

    if not stores:
        raise RuntimeError("No DataStore found")

    ds = stores

    # Use memory DB (optional)
    ds.FileName = ":memory:"
    ds.UseInMemoryDB = True
    ds.ReadOnly = False
    ds.UpdateFileName()
    ds.Open()  # 🔥 REQUIRED

    # 🔥 STEP 3: Runner
    if simulation_names:
        import System
        sim_names_array = System.Array[str](simulation_names)
    else:
        sim_names_array = None

    runner = Runner(
        model,
        runType=RunTypeEnum.MultiThreaded,
        simulationNamesToRun=sim_names_array
    )

    errors = runner.Run()

    # 🔥 STEP 4: Read results
    ds.Reader.Refresh()
    tables = list(ds.Reader.TableNames)

    return {
        "success": len(errors) == 0,
        "errors": [str(e) for e in errors] if errors else [],
        "tables": tables
    }


fp = load_crop_from_disk('Maize', out='rs.apsimx')
db = Path(fp).with_suffix('.db')

run = run_apsim_simulation(fp, simulation_names=['simulation'])
for i in run:
    print(i, run[i])
# read_db_table(db, report_name='Report')

import subprocess
from pathlib import Path


@timer
def run_odm(project_dir: str, image: str = "opendronemap/odm", extra_args: list[str] | None = None):
    """
    Run OpenDroneMap via Docker.

    Parameters
    ----------
    project_dir : str
        Path to ODM project directory (must contain 'images' folder)
    image : str
        Docker image to use
    extra_args : list[str]
        Additional ODM CLI arguments (e.g. ['--fast-orthophoto'])

    Returns
    -------
    dict
        { "success": bool, "stdout": str, "stderr": str }
    """

    project_dir = Path(project_dir).resolve()

    if not project_dir.exists():
        raise FileNotFoundError(f"Project directory not found: {project_dir}")

    if not (project_dir / "images").exists():
        raise ValueError("ODM project must contain an 'images' folder")

    # Default ODM arguments
    odm_args = [
        "--project-path", "/datasets",
        project_dir.name
    ]

    if extra_args:
        odm_args.extend(extra_args)

    cmd = [
        "docker", "run", "--rm",
        "-v", f"{project_dir.parent}:/datasets",
        image,
        *odm_args
    ]

    print("Running:", " ".join(cmd))

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    return {
        "success": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr
    }
import subprocess
import time

def start_docker_windows():
    subprocess.Popen(
        r"C:\Program Files\Docker\Docker\Docker Desktop.exe",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # wait until Docker is ready
    for _ in range(30):
        try:
            subprocess.run(["docker", "info"], check=True,
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
            print("Docker is ready")
            return True
        except subprocess.CalledProcessError:
            time.sleep(2)

    raise RuntimeError("Docker failed to start")


#start_docker_windows()

rr = run_odm(r'D:\odm_project', extra_args=['--dem-resolution', '2', '--smrf-threshold', '0.4', '--smrf-window', '24'])
print('success', rr['success'])
stdout =  rr['stdout'] or rr['stderror']
xc= repr(stdout)
print(xc)
import socket


class Connect:

    def __init__(self, host="127.0.0.1", port=27746):
        self._socket = None
        self.HOST = host
        self.PORT = port
        self.connected = False

    def connect(self):
        # idempotent
        if not self.connected:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.HOST, self.PORT))
            self.connected = True
            print("Connected to APSIM server")
            self._socket = sock
            return sock

    def disconnect(self):
        if self.connected:
            self._socket.close()
            self.connected = False


