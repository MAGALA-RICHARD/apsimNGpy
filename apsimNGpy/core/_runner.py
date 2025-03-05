import os
from pathlib import Path
import logging
from pathlib import Path
from subprocess import run, CalledProcessError, CompletedProcess, PIPE
import platform
from apsimNGpy.core.config import get_apsim_bin_path
from typing import NamedTuple
from apsimNGpy.core.model_loader import load_model_from_dict
from apsimNGpy.utililies.utils import timer
from subprocess import *

logger = logging.getLogger(__name__)
apsim_bin_path = Path(get_apsim_bin_path())

# Determine executable based on OS
if platform.system() == "Windows":
    apsim_exe = apsim_bin_path / "Models.exe"
else:  # Linux or macOS
    apsim_exe = apsim_bin_path / "Models"


def run_model_externally(model, verbose: bool = False) -> Popen[str]:
    """Runs an APSIM model externally, ensuring cross-platform compatibility."""

    # Get the APSIM binary path

    # Define the APSIMX file path
    apsim_file = model
    result = Popen([str(apsim_exe), str(apsim_file), '--verbose'], stdout=PIPE, stderr=PIPE, text=True)
    try:
        if verbose:
            logger.info("APSIM Run Successful!")
            logger.info(result.stdout)  # Print APSIM output
        # logger.info("Errors:", result.stderr)
        result.communicate()
        res, err = result.communicate()
        logger.info(res.strip())
        if err:
            logger.error(err.strip)
        return result
    finally:
        if not result.poll():
            result.terminate()


@timer
def run_from_dir(directory, pattern):
    directory = str(directory)
    dir_patern = f"{directory}/{pattern}"
    print(dir_patern)
    process = Popen([str(apsim_exe), dir_patern, '--recursive', '--verbose'])

    process.wait()
    print(process.poll())
