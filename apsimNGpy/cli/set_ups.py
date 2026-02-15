import argparse
import sys
from os import path
from apsimNGpy.config import configuration, set_apsim_bin_path, auto_detect_apsim_bin_path


def print_msg(msg, normal=True):
    """Print messages with color."""
    color = "\033[96m" if normal else "\033[91m"
    print(f'  {color}{msg}\033[0m')


class ColoredHelpFormatter(argparse.HelpFormatter):
    """Custom argparse formatter with colored section headings."""

    def start_section(self, heading):
        heading = f"\033[91m{heading}\033[0m"
        super().start_section(heading)


def apsim_bin_path():
    parser = argparse.ArgumentParser(
        description='Manage APSIM NG bin path using apsimNGpy config.',
        formatter_class=ColoredHelpFormatter
    )

    parser.add_argument(
        '-u', '--update', type=str,
        help='Update APSIM bin path using apsimNGpy.config.set_apsim_bin_path.'
    )
    parser.add_argument(
        "-s", "--show_bin_path",
        action="store_true",
        help='Show current APSIM bin path.'
    )
    parser.add_argument(
        "-v", "--version",
        action="store_true",
        help="Show current APSIM NG version."
    )
    parser.add_argument(
        "-a", "--auto_search",
        action="store_true",
        help="Search and display available APSIM NG bin path(s)."
    )

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(0)

    args = parser.parse_args()

    if args.update:
        if not path.exists(args.update):
            print_msg(f"{args.update} does not exist", normal=False)
            sys.exit(1)
        set_apsim_bin_path(args.update)
        print_msg(f"Bin path updated to: {args.update}")
        sys.exit(0)

    if args.show_bin_path:
        current_path = configuration.bin_path
        print_msg(current_path)
        sys.exit(0)

    if args.auto_search:
        auto = auto_detect_apsim_bin_path()
        if not auto:
            print_msg("No bin path detected", normal=False)
        else:
            print_msg(f"Detected: {auto}")
        sys.exit(0)

    if args.version:
        v = configuration.bin_path
        print_msg(f"APSIM version: {v}")
        sys.exit(0)


if __name__ == '__main__':
    #sys.argv.append('-s')
    apsim_bin_path()
    sys.argv.append('-a')
    apsim_bin_path()
