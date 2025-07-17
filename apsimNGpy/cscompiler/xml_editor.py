import xml.etree.ElementTree as ET
from apsimNGpy.core.config import get_apsim_bin_path
import os

APSIM_BIN_DIR = get_apsim_bin_path()


def update_hint_paths(csproj_path, models_dll_path, apsim_shared_path):
    tree = ET.parse(csproj_path)
    root = tree.getroot()

    ns = {'msbuild': 'http://schemas.microsoft.com/developer/msbuild/2003'}

    # Make sure we use default namespace if present
    for reference in root.iter('Reference'):
        include_attr = reference.attrib.get('Include', '')
        if include_attr == 'Models':
            hint = reference.find('HintPath')
            if hint is not None:
                hint.text = models_dll_path
        elif include_attr == 'APSIM.Shared':
            hint = reference.find('HintPath')
            if hint is not None:
                hint.text = apsim_shared_path

    tree.write(csproj_path, encoding='utf-8', xml_declaration=True)
    print(f"Updated HintPaths in {csproj_path}")


# Example usage
update_hint_paths(
    csproj_path=os.path.abspath('./cast.csproj'),
    models_dll_path=os.path.join(APSIM_BIN_DIR, "Models.dll"),
    apsim_shared_path=os.path.join(APSIM_BIN_DIR, "APSIM.Shared.dll")
)

from apsimNGpy.core.pythonet_config import start_pythonnet
import clr
start_pythonnet()
clr.AddReference