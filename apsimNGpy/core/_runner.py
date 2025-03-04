from pathlib import Path
import logging
from pathlib import Path
from subprocess import run, CalledProcessError, CompletedProcess, PIPE
import platform
from apsimNGpy.core.config import get_apsim_bin_path
from typing import NamedTuple
from apsimNGpy.core.model_loader import load_model_from_dict
from apsimNGpy.utililies.utils import timer

logger = logging.getLogger(__name__)


def run_model_externally(model, verbose: bool = False) -> CompletedProcess[str]:
    """Runs an APSIM model externally, ensuring cross-platform compatibility."""

    # Get the APSIM binary path
    apsim_bin_path = Path(get_apsim_bin_path())

    # Determine executable based on OS
    if platform.system() == "Windows":
        apsim_exe = apsim_bin_path / "Models.exe"
    else:  # Linux or macOS
        apsim_exe = apsim_bin_path / "Models"

    # Define the APSIMX file path
    apsim_file = model

    # Run APSIM with the specified file
    try:
        result = run([str(apsim_exe), str(apsim_file)], stdout=PIPE, stderr=PIPE,)

        if verbose:
            logger.info("APSIM Run Successful!")
            logger.info(result.stdout)  # Print APSIM output
        #logger.info("Errors:", result.stderr)
        return result
    except CalledProcessError as e:
        logger.error("Error running APSIM:")
        logger.error(e.stderr)

        raise
