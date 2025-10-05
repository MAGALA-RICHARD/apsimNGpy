from apsimNGpy.example_jupiter_notebooks.repair import repair_ipynb
from pathlib import Path

cwd = Path(__file__).parent
notebooks = cwd.glob('**/*.ipynb')
for i in notebooks:
    repair_ipynb(in_path=i)
