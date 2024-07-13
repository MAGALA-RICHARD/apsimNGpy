
class Config:
    """
    The configuration of this aPsimNGpy in general providing the place
    for declaring global variables.
    """

    ApSIM_LOCATION = None

    @classmethod
    def set_aPSim_bin_path(cls, path):
        cls.software_path = path

    @classmethod
    def get_aPSim_bin_path(cls):
        return cls.ApSIM_LOCATION
