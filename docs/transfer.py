import schedule
import time
import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='  [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)
CWD = Path(__file__).parent
target = CWD.parent.parent / 'docs'
source = CWD.parent.parent.parent / "apsimNGpy-documentations/doc/"


def transfer():
    try:
        shutil.copytree(source, target, dirs_exist_ok=True)
        logger.info(f"copy from {str(source)} to {str(target)} successful")
    except Exception as e:
        logger.error(repr(e))


if __name__ == "__main__":
    schedule.every(2).minutes.do(transfer)
    while True:
        schedule.run_pending()
        time.sleep(60)
