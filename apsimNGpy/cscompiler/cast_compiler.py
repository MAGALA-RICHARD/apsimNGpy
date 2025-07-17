import subprocess
import os
from pprint import pprint
from apsimNGpy.settings import logger
from pathlib import Path

# Set working directory
project_path = os.path.abspath(r"./")
build_config = "Debug"


def compile_cast():
    # Build command
    cmd = ["dotnet", "build", "--configuration", build_config]

    try:
        result = subprocess.run(cmd, cwd=project_path, check=True, capture_output=True, text=True)
        logger.info('✔ Build succeeded!')

    except subprocess.CalledProcessError as e:
        logger.info(e.stderr)
        raise RuntimeError("❌Build failed!\n")


def add_ref_cast(verbose=False):
    data = list(Path(project_path).rglob('*cast.dll'))
    if not data:
        compile_cast()
        # try again
        data = list(Path(project_path).rglob('*cast.dll'))
        if not data:
            raise FileNotFoundError("cast.dll not found perhaps compilation was not successful")

    from apsimNGpy.core.pythonet_config import start_pythonnet
    start_pythonnet()
    import clr
    cast_path = str(data[0])
    clr.AddReference(cast_path)
    if verbose:
        logger.info('Cast loaded successfully from {}'.format(cast_path))


add_ref_cast(True)
