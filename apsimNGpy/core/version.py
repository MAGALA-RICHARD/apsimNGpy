import sys
from functools import cache

@cache
def extract_for_lower(toml_path):
    with open(toml_path, 'r') as f:
        inside_project = False
        for line in f:
            line = line.strip()
            if line == '[project]':
                inside_project = True
            elif inside_project and line.startswith('version'):
                return line.split('=')[1].strip().strip('"').strip("'")

def extract_version(toml_path='../pyproject.toml'):
    if sys.version_info >= (3, 11):
        import tomllib
        with open(toml_path, 'rb') as f:
            data = tomllib.load(f)
        return data['project']['version']

    else:
        extract_for_lower(toml_path)
        raise RuntimeError("Version not found in [project] section.")



version = extract_version()

