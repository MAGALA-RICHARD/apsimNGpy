import sys
import time

from sphinx.cmd.quickstart import suffix
from dataclasses import dataclass, field

from sqlalchemy.testing.util import total_size

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


def format_time(seconds):
    millis = int((seconds % 1) * 1000)
    seconds = int(seconds)
    mins, sec = divmod(seconds, 60)
    hrs, mins = divmod(mins, 60)
    return f"{hrs:02d}:{mins:02d}:{sec:02d}.{millis:03d}"

@dataclass
class ProgressBar:
    total: int
    prefix: str = ''
    suffix: str = ''
    length: int = 10
    fill: str = '█'
    color: str = 'green'
    leader_head: str = ' '
    show_time: bool = True
    unit:str = 'iteration'

    iteration: int = field(default=0, init=False)
    start_time: float = field(default_factory=time.perf_counter, init=False)

    def update(self, step: int = 1):
        self.iteration += step
        self._render()
        if self.iteration >= self.total:
            self.close()

    def close(self):
        self.iteration =0
        print()

    def refresh(self, new_total = None):
        """Force a redraw of the current progress bar without changing the iteration."""
        self.total = new_total or self.total
        self._render()

    def _render(self):
        reset = COLOR_CODES['reset']
        color_code = COLOR_CODES.get(self.color.lower(), '')

        percent = f"{100 * (self.iteration / float(self.total)):.1f}"
        filled_length = int(self.length * self.iteration // self.total)
        bar = color_code + self.fill * filled_length + reset + self.leader_head * (self.length - filled_length)
        prefix = COLOR_CODES['red'] + self.prefix + reset
        suffix = COLOR_CODES['red'] + self.suffix + reset
        percent_str = color_code + percent + '%' + reset

        time_info = ''
        tasks =''
        if self.show_time and self.iteration > 0:
            elapsed = time.perf_counter() - self.start_time
            avg_time = elapsed / self.iteration
            formatted_time = format_time(elapsed)
            time_info = f"{color_code} | {avg_time:.2f}s/{self.unit} | Elapsed time: {formatted_time}{reset}"
            tasks = f'{color_code}[{self.iteration}/{self.total}]{reset}'

        sys.stdout.write(f'\r{prefix} |{bar}| {percent_str}| {tasks}| {suffix}{time_info}')
        sys.stdout.flush()


def print_progress_bar(iteration, total, prefix='', suffix='', length=10, fill='█', color='green', leader_head=' '):
    reset_code  = '\033[0m'
    color_code = COLOR_CODES.get(color.lower(), '')
    percent = f"{100 * (iteration / float(total)):.1f}"
    filled_length = int(length * iteration // total)
    bar = color_code + fill * filled_length + reset_code + leader_head * (length - filled_length)
    prefix = '\033[31m' + prefix + reset_code
    suffix = '\033[31m' + suffix + reset_code
    percent = color_code + percent + reset_code
    p_symbol = color_code + '%' + reset_code

    sys.stdout.write(f'\r{prefix} |{bar}| {percent}{p_symbol} {suffix}' )
    sys.stdout.flush()

    if total==iteration:
        print()

def progress(total, color ='blue'):
    for i in range(total + 1):

        print_progress_bar(i, total, prefix='Progress', suffix='Complete', length=10, color=color, fill='.')
        time.sleep(0.03)  # Simulate work

if __name__ == '__main__':
  from apsimNGpy.core.apsim import ApsimModel
  bar = ProgressBar(total=50, prefix='Progress', suffix='Complete', color='yellow')
  model = ApsimModel('Maize')
  def fun(x):
      xm = x**3/100000000 * 10000000000000000000000000000000000000000
      time.sleep(1)
      return xm**3 *5+4*2 * 100000000/1000000 * 10000
  for y in range(50):
      model.run()
      bar.update()
  bar.close()
  print(34)


