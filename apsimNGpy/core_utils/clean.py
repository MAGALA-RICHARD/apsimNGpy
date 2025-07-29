from pathlib import Path
import logging
from typing import Union

logging.basicConfig(
    level=logging.INFO,  # or DEBUG, WARNING, ERROR, CRITICAL
    format='\n[%(levelname)s]: %(message)s'
)


def clean(root_dir: Union[str, Path], recursive=False) -> None:
    path = Path(root_dir).resolve()
    glob = 'rglob' if recursive else 'glob'

    def _get_files():
        ax = getattr(path, glob)('*.apsimx')
        db = getattr(path, glob)('*.db')
        remove = list(ax) + list(db) + list(getattr(path, glob)('*.db-shm')) + list(getattr(path, glob)('*.csv'))
        return remove

    fl = _get_files()
    len1 = len(fl)

    for i in fl:
        try:
            i.unlink(missing_ok=True)
        except PermissionError:
            logging.info(f"skipping '{i}' due to permission error")
    # get files again
    fl2 = _get_files()
    len2 = len(fl2)
    removed = len1 - len2
    logging.info(f" Cleaned {removed} unwanted files")


if __name__ == '__main__':
    clean('.')
