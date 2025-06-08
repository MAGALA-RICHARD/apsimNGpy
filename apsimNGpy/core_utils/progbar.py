import sys
import time

# ANSI escape codes for colors
COLOR_CODES = {
    # Standard foreground colors
    'black': '\033[30m',
    'red': '\033[31m',
    'green': '\033[32m',
    'yellow': '\033[33m',
    'blue': '\033[34m',
    'magenta': '\033[35m',
    'cyan': '\033[36m',
    'white': '\033[37m',

    # Bright foreground colors
    'bright_black': '\033[90m',
    'bright_red': '\033[91m',
    'bright_green': '\033[92m',
    'bright_yellow': '\033[93m',
    'bright_blue': '\033[94m',
    'bright_magenta': '\033[95m',
    'bright_cyan': '\033[96m',
    'bright_white': '\033[97m',

    # Background colors
    'bg_black': '\033[40m',
    'bg_red': '\033[41m',
    'bg_green': '\033[42m',
    'bg_yellow': '\033[43m',
    'bg_blue': '\033[44m',
    'bg_magenta': '\033[45m',
    'bg_cyan': '\033[46m',
    'bg_white': '\033[47m',

    # Bright background colors
    'bg_bright_black': '\033[100m',
    'bg_bright_red': '\033[101m',
    'bg_bright_green': '\033[102m',
    'bg_bright_yellow': '\033[103m',
    'bg_bright_blue': '\033[104m',
    'bg_bright_magenta': '\033[105m',
    'bg_bright_cyan': '\033[106m',
    'bg_bright_white': '\033[107m',

    # Reset code
    'reset': '\033[0m'
}

def print_progress_bar(iteration, total, prefix='', suffix='', length=10, fill='█', color='green', leader_head=' '):

    color_code = COLOR_CODES.get(color.lower(), '')
    reset_code = COLOR_CODES['reset']

    percent = f"{100 * (iteration / float(total)):.1f}"
    filled_length = int(length * iteration // total)
    bar = color_code + fill * filled_length + reset_code + leader_head * (length - filled_length)
    sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}')
    sys.stdout.flush()
    if total==iteration:
        print()

def progress(total, color ='blue'):
    for i in range(total + 1):

        print_progress_bar(i, total, prefix='Progress', suffix='Complete', length=10, color=color)
        time.sleep(0.03)  # Simulate work

if __name__ == '__main__':
  progress(100)

