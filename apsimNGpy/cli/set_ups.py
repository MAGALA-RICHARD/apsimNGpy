import argparse
from os import path
import logging
from apsimNGpy.core_utils.utils import timer
from apsimNGpy.core.config import set_apsim_bin_path, get_apsim_bin_path, auto_detect_apsim_bin_path
from apsimNGpy.settings import logger
import sys
from apsimNGpy.core.runner import get_apsim_version

@timer
def apsim_bin_path():
    parser = argparse.ArgumentParser(description='set ups')
    parser.add_argument('-u', '--update', type=str, default=None,
                        help=f'Updates apsim bin path using apsimNGPy config module see: set_apsim_bin_path')

    parser.add_argument(
        "-s", "--show_bin_path",
        action="store_true",
        help="Set this flag to show current bin path."
    )

    parser.add_argument(
        "-v", "--version",
        action="store_true",
        help="Set this flag to show current apsim version."
    )

    parser.add_argument(
        "-a", "--auto_search",
        action="store_true",
        help="Set this flag to search and display any existing apsim bin path."
    )
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    args = parser.parse_args()
    bp = args.update
    if bp:
        if not path.exists(bp):
            raise FileNotFoundError(f"-bp {bp} does not exist")
        set_apsim_bin_path(bp)

    if args.show_bin_path:
        cbp = get_apsim_bin_path()
        logger.info(f"Current APSIM binary installed path: '{cbp}'")
    if args.auto_search:
        logger.info("searching apsim bin path.................")
        print()
        auto = auto_detect_apsim_bin_path()
        if not auto:
            logger.info("No apsim bin was found")
        else:

            logger.info(f"Detected: '{auto}'")
            print()
    if args.version:
        print(get_apsim_version())


if __name__ == '__main__':
    apsim_bin_path()
