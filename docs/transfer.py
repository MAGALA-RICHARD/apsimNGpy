import schedule
import time
import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='  [%(levelname)s]: %(message)s')
logger = logging.getLogger(__name__)
CWD = Path(__file__).parent
target = CWD.parent / 'docs'
source = CWD.parent.parent / "apsimNGpy-documentations/doc"


def transfer():
    try:
        shutil.copytree(source, target, dirs_exist_ok=True)
        logger.info(f"copy from {str(source)} to {str(target)} successful")
    except Exception as e:
        logger.error(repr(e))


if __name__ == "__main__":
    schedule.every(1).seconds.do(transfer)
    while True:
        schedule.run_pending()
        time.sleep(1)
