import os.path as osp


def change_version(apsim_version):
    if osp.exists(apsim_version) and apsim_version.endswith(".bin"):
        return apsim_version
