from rich.console import Console
from rich.logging import RichHandler
import logging

# console = Console(force_terminal=True, stderr=True, tab_size=10)
# logging.basicConfig(
#     level="INFO",
#     format="%(message)s",
#     datefmt="[%X]",
#     handlers=[RichHandler(console=console, show_time=True, show_level=True, show_path=False)]
# )
# logger = logging.getLogger("app")
#
# from rich.console import Console
# from rich.logging import RichHandler
# import logging

console = Console(force_terminal=True, stderr=True, tab_size=10)

logger = logging.getLogger("apsimNGpy")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    logger.addHandler(
        RichHandler(
            console=console,
            show_time=True,
            show_level=True,
            show_path=False,
            markup=True,
        )
    )