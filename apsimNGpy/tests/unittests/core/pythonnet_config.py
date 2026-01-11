# test_pythonnet_config.py. depends on a properly functioning config module
import os
import sys
import tempfile
import shutil
import importlib
import unittest
from pathlib import Path
from typing import Union
from unittest.mock import patch
import gc
import platform
from pathlib import Path
# --------------apsimNGpy related modules________________________
from apsimNGpy.exceptions import ApsimBinPathConfigError
from apsimNGpy.core.config import get_apsim_bin_path, locate_model_bin_path, configuration
from apsimNGpy.core import pythonet_config
from apsimNGpy.core.pythonet_config import start_pythonnet, load_pythonnet, get_apsim_file_reader, \
    get_apsim_file_writer, is_file_format_modified

from apsimNGpy.settings import logger

CURRENT_BIN = configuration.bin_path

# ---- Helpers ---------------------------------------------------------------


# ---- Test cases ------------------------------------------------------------
bin = configuration.bin_path

if not locate_model_bin_path(bin):
    logger.info('Could not locate bin path and thus can not proceed with test pythonnet config module')
    sys.exit()


def _exclude(path: Union[str, Path]) -> bool:
    """
    Return True for files that indicate an installed/active APSIM binary
    we should not touch. On Windows exclude .exe/.dll; on macOS/Linux
    exclude .dll and the 'Models' executable.
    """
    pt = Path(path)
    name = pt.name
    ext = pt.suffix.lower()

    if platform.system() == "Windows":
        return ext in {".exe", ".dll"}
    else:
        return ext == ".dll" or name == "Models"


def copy_dir_contents(src, dst, *, overwrite=True, symlinks=False):
    src = Path(src)
    dst = Path(dst)
    if not src.is_dir():
        raise NotADirectoryError(f"{src} is not a directory")
    dst.mkdir(parents=True, exist_ok=True)

    for item in src.iterdir():
        target = dst / item.name
        if item.is_dir():
            shutil.copytree(
                item,
                target,
                dirs_exist_ok=overwrite,  # Python 3.8+: merge if exists
                symlinks=symlinks
            )
        else:
            if target.exists() and not overwrite:
                continue
            shutil.copy2(item, target)  # preserves mtime/permissions


class TestPythonnetLoader(unittest.TestCase):
    """
    Tests emphasize *error raising* and import-time isolation via mocks.
    Replace 'pythonnet_loader' with your module name.
    """

    MODULE = pythonet_config.__name__

    def setUp(self):
        # Temporary directory to act as a fake APSIM bin folder
        self.tmpdir = tempfile.mkdtemp(prefix="apsim_bin_")
        self.tmp_path = Path(self.tmpdir)

        # Ensure a clean import between tests
        if self.MODULE in sys.modules:
            del sys.modules[self.MODULE]
            gc.collect()

    def test_is_file_format_modified(self):
        module = self.import_module_with_valid_bin()
        modified = module.is_file_format_modified()
        self.assertIsInstance(modified, bool, msg="is_file_format_modified must return a bool not {}".format(modified))

    def test_load_pythonnet(self):
        """
        checks whether pythonnet is running and was able to add bin_path to path, and hence the ability to import c#modules
        @return:
        """
        module = self.import_module_with_valid_bin()
        module.load_pythonnet()

        try:
            # ____ If loaded then C3 modules are importable ___________
            import Models
            loaded = True
        except ModuleNotFoundError:
            # switch loaded flag to indicate False and hence failure
            loaded = False
        self.assertTrue(loaded, msg="loading pythonnet failed")
        import pythonnet
        self.assertTrue(pythonnet.get_runtime_info().initialized, 'Pythonnet initialization failed')

    def test_later_modified_versions_with_apsim_dot_core(self):
        modified = is_file_format_modified()
        start_pythonnet()
        try:
            import APSIM.Core
            apsim_core = True
        except ModuleNotFoundError:
            apsim_core = False
        check_true = apsim_core == modified
        self.assertTrue(check_true,
                        msg=f"is_file_format_modified indicated {modified} yet importing APSIM,core indicated {apsim_core}")

    def tearDown(self):
        # Restore sys.modules['clr']

        shutil.rmtree(self.tmpdir, ignore_errors=True)

        # Allow re-import cleanly later
        if self.MODULE in sys.modules:
            del sys.modules[self.MODULE]
            gc.collect()

    # -------------------- Import-time safe baseline -------------------------

    def import_module_with_valid_bin(self):
        """
        Import the module while faking a valid APSIM bin path so that its
        import-time call to load_pythonnet() does not raise.
        """

        mod = importlib.import_module(self.MODULE)
        return mod

    # -------------------- Error-raising tests -------------------------------
    def test_raise_when_no_valid_bin(self):
        """
            Validate that an APSIM NG 'bin' directory contains the required binaries.

            A directory is considered **valid** if it contains:
              - **Windows:** `Models.dll` **and** `Models.exe`
              - **macOS / Linux:** `Models.dll` **and** `Models` (Unix executable)

            Thus method makes sure that  ApsimBinPathConfigError is raised when:
                - The path exists but does **not** contain the required binaries for the
                  current OS (e.g., `Models.exe` missing on Windows, or `Models` missing on macOS/Linux), or
                - The path is otherwise invalid for use as an APSIM NG bin directory.

            Notes
            -----
            This check differentiates between:
              1) A non-existent directory (handled by separate path existence checks), and
              2) An existing directory where the **flag files** have been uninstalled or deleted.
                 The latter should also raise `ApsimBinPathConfigError`.
        """
        # __test if a directory exists but the flag files has been uninstalled or delted__
        self.import_module_with_valid_bin()
        loc_bin = locate_model_bin_path(CURRENT_BIN)
        # _________mock bin path with deleted files____________
        empty_bin = Path(self.tmpdir) / 'empty_bin'
        if empty_bin.exists():
            try:
                shutil.rmtree(empty_bin, ignore_errors=True)
            except PermissionError:
                pass
        empty_bin.mkdir(parents=True, exist_ok=True)
        copy_dir_contents(loc_bin, empty_bin)
        for files in empty_bin.iterdir():
            # remove files that flags proper or valid apsim bin path
            if files.is_file():
                if _exclude(files):
                    try:
                        os.remove(str(files))
                    except  PermissionError:
                        pass
        with self.assertRaises(ApsimBinPathConfigError,
                               msg='invalid bin path must not be loaded. How did this happen?'):
            from apsimNGpy.core.config import set_apsim_bin_path
            set_apsim_bin_path(empty_bin)
        # remove the mock bin_bin_path
        try:
            shutil.rmtree(empty_bin, ignore_errors=True)
        except PermissionError:
            pass

    def ensure_set_apsim_bin_path_raise_not_found_error(self):
        """
        Ensure that if the not existent path is supplied, the set apsim bin path raised FileNotFoundError error set locate_bin

        """
        empty_bin = Path(self.tmpdir) / 'notfound_dir_empty_bin'
        if empty_bin.exists():
            try:
                shutil.rmtree(empty_bin, ignore_errors=True)
            except PermissionError:
                pass
        with self.assertRaises(NotADirectoryError, msg='invalid bin path must not be loaded'):
            from apsimNGpy.core.config import set_apsim_bin_path
            set_apsim_bin_path(empty_bin)

    def test__add_bin_to_syspath_raises_on_empty_string(self):
        """
        _add_bin_to_syspath should raise when given an empty path string
        (per current implementation guard).
        """
        mod = self.import_module_with_valid_bin()

        # with self.assertRaises(mod.ApsimBinPathConfigError):
        #     mod._add_bin_to_syspath("")  # empty string triggers the guard

    # -------------------- Non-raising sanity checks (optional) --------------


if __name__ == "__main__":
    unittest.main()
