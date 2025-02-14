import argparse

from apsimNGpy.core.config import set_apsim_bin_path, get_apsim_bin_path


def set_bin_path():
    parser = argparse.ArgumentParser(description='set ups')
    parser.add_argument('-bp', '--bin_path', type=str, default= None,
                        help=f'set ups path using apsimNGPy config module see: set_apsim_bin_path')

    parser.add_argument('-cbp', '--current_bin_path', type=str, default= False)

    args = parser.parse_args()
    bp = args.bin_path
    if bp:
        set_apsim_bin_path(args.bin_path)
    cbp = args.current_bin_path
    if cbp:
        # call get_apsim_bin_path
        cbp = get_apsim_bin_path()
        print(f"Current APSIM binary installed path: {cbp}")


if __name__ == '__main__':
    set_bin_path()
