import argparse
from os import path

from apsimNGpy.core.config import set_apsim_bin_path, get_apsim_bin_path, auto_detect_apsim_bin_path


def apsim_bin_path():
    parser = argparse.ArgumentParser(description='set ups')
    parser.add_argument('-u', '--update', type=str, default= None,
                        help=f'set ups path using apsimNGPy config module see: set_apsim_bin_path')

    parser.add_argument(
        "-s", "--show_bin_path",
        action="store_true",
        help="Set this flag to show current bin path."
    )

    parser.add_argument(
        "-a", "--auto_search",
        action="store_true",
        help="Set this flag to search and display any existing apsim bin path."
    )

    args = parser.parse_args()
    bp = args.update
    if bp:
        if not path.exists(bp):
            raise FileNotFoundError(f"-bp {bp} does not exist")
        set_apsim_bin_path(bp)

    if args.show_bin_path:
        cbp = get_apsim_bin_path()
        print(f"Current APSIM binary installed path: '{cbp}'")
    if args.auto_search:
        print("searching apsim bin path.................", end='\r')
        print()
        auto = auto_detect_apsim_bin_path()
        if not auto:
            print("No apsim bin was found")
        else:

            print(f"apsim bin path detected at: '{auto}'")
            print()


if __name__ == '__main__':
    apsim_bin_path()
