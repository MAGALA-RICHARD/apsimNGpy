import argparse
from os import path
import logging
from apsimNGpy.core_utils.utils import timer
from apsimNGpy.core.config import set_apsim_bin_path, get_apsim_bin_path, auto_detect_apsim_bin_path
from apsimNGpy.settings import logger
import sys
from apsimNGpy.core.runner import get_apsim_version
from pprint import pprint

def print_msg(msg, normal = True):
    if normal:
       print(f'\033[96m{msg}\033[0m')
    else:
        print(f'\033[91m{msg}\033[0m')


class ColoredHelpFormatter(argparse.HelpFormatter):
    def start_section(self, heading):
        heading = f"\033[95m{heading}\033[0m"  # Purple color
        super().start_section(heading)
def apsim_bin_path():
    parser = argparse.ArgumentParser(description='Investigating apsimNGpy APSIM bin path', formatter_class=ColoredHelpFormatter)
    parser.add_argument('-u', '--update', type=str, default=None,
                        help=f'Updates apsim bin path using apsimNGPy config module see: set_apsim_bin_path')

    parser.add_argument(
        "-s", "--show_bin_path",
        action="store_true",
        help='\033[93mSet this flag to show current bin path.\033[0m'
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
        parser.print_help(sys.stderr, )
        sys.exit(1)
    args = parser.parse_args()
    bp = args.update
    if bp:
        if not path.exists(bp):
            raise FileNotFoundError(print_msg(msg = f'{bp} does not exist',normal=False))
        set_apsim_bin_path(bp)
        sys.exit(1)

    if args.show_bin_path:
        cbp = get_apsim_bin_path()
        print(cbp)
        print_msg(msg = cbp, normal=True)
        sys.exit(1)
    if args.auto_search:
        print()
        auto = auto_detect_apsim_bin_path()
        if not auto:
            print_msg(msg = 'No bin path detected', normal=False)

        else:
            print_msg(msg = f'detected: {auto}', normal=True)
            print()
        sys.exit(1)
    if args.version:
        v = get_apsim_version()
        print_msg(v)
        sys.exit(1)


if __name__ == '__main__':
    apsim_bin_path()
