import shutil
from pathlib import Path

from apsimNGpy.core.config import configuration, locate_model_bin_path


class MimicBinPath:
    def __init__(self, bin_path: str | None = None, location: str | None = None):
        self.bin_path = bin_path or configuration.bin_path
        self.bin_path = locate_model_bin_path(self.bin_path)
        self.location = location
        self.created =False

    def __enter__(self):
        self.dir_bin_new = Path(f'{self.location}/bin_path_testing12').resolve() if self.location else Path("bin_path_testing12").resolve()
        assert self.dir_bin_new.resolve() != Path(self.bin_path).resolve(), 'please change new bin path location'
        if self.dir_bin_new.exists():

            shutil.rmtree(self.dir_bin_new, ignore_errors= True)

        self.created_bin_path = shutil.copytree(self.bin_path, self.dir_bin_new)
        print(self.created_bin_path)
        self.created = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.created:
           shutil.rmtree(self.dir_bin_new)


def mimic_different_bin_path(existing_bin_path: str):
    bin = locate_model_bin_path(existing_bin_path)

    bin = list(bin.rglob('*Models*'))
    return bin

with MimicBinPath() as bin:
    print(bin.created_bin_path)

print('+++++++++++')

print(configuration.bin_path)
configuration.set_temporal_bin_path(r"C:\Program Files\APSIM2024.5.7493.0\bin")
print(configuration.bin_path)
configuration.release_temporal_bin_path()
print(configuration.bin_path)
# unittest.main()
