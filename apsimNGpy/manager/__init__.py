from apsimNGpy.settings import logger
from pathlib import Path


def show_module_deprecation(__file__):
    stem = Path(__file__).parent.stem
    name = Path(__file__).stem
    logger.warning(
        f"\nSoil module `apsimNGpy.{stem}.{name}` will be permanently moved to "
        "apsimNGpy.soils and are scheduled for deprecation in future versions."
    )
