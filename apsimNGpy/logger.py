from rich.console import Console
from rich.logging import RichHandler
import logging

console = Console(force_terminal=True)
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, show_time=True, show_level=True, show_path=True)]
)
logger = logging.getLogger("app")

