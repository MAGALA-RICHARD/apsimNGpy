import os, sys; sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core import weather

__all__ = [ApsimModel, weather]
