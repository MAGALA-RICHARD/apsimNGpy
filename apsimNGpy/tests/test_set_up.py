import os
from pathlib import Path
import argparse
from apsimNGpy.config import path_checker

ACTIONS_APSIM_BINARY = Path(__file__).parent / 'apsim_binaries'
from apsimNGpy import set_apsim_bin_path


def setup_apsim_binary(par=None, bin_directory=None):
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-bp",
        "--bin",
        type=Path,
        required=False,
        help="Path to APSIM binary directory", )

    args = parser.parse_args(par)
    if path_checker(bin_directory):
        bin_path = bin_directory
    elif args.bin is not None:
        bin_path = args.bin.resolve()
    else:
        bin_path = ACTIONS_APSIM_BINARY
    if path_checker(bin_path):
        bin_path = Path(bin_path).resolve()
    else:
        raise ValueError(f"Invalid APSIM binary path: {bin_path}")
    setp = set_apsim_bin_path(bin_path)
    print('bin path set: ', setp)
    return bin_path


if __name__ == '__main__':
    _bin_path = setup_apsim_binary()
