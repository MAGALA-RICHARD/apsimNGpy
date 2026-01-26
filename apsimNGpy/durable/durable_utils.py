import inspect
from apsimNGpy.core.mult_cores import MultiCoreManager

code = inspect.getsource(MultiCoreManager.run_all_jobs)


class CheckPoint:
    def __init__(self):
        self.epoch = 0


code = "{i for i in range(10)}"
