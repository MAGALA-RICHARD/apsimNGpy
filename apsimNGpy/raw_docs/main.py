import shutil
from pathlib import Path
from typing import Union

import apsimNGpy
import inspect
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core import runner

SENDTO = Path.cwd().parent.parent / 'docs/source'


def docs(modules: Union[list, object], output_file: Union[str, Path] = "api.rst", skip_undocumented: bool = True):
    """
    Extracts the docstrings of all public functions and classes in a module and writes them to an .rst file.

    Args:
        modules (list[module] or module): The Python modules or classes to extract documentation from.
        output_file (str): The path to the output .rst file.
    """
    if not isinstance(modules, list):
        modules = [modules]

    with open(output_file, "w", encoding="utf-8") as file:
        for module in modules:
            module_name = module.__name__ if hasattr(module, '__name__') else module.__class__.__name__
            class_name = 'Class' if hasattr(module, '__class__') else ''
            if inspect.isclass(module):
                file.write(f"{module_name} {class_name}: API Reference\n")
                file.write("-" * (len(module_name) + 15) + "\n\n")
                sig = inspect.signature(module)
                file.write(f".. function:: {module.__name__}{sig}\n\n")
                doc = module.__doc__ or "No documentation available."
                file.write(f"   {doc.strip()}\n\n")
            if inspect.isfunction(module):
                if not module.__name__.startswith('_'):
                    sig = inspect.signature(module)
                    file.write(f".. function:: {module.__name__}{sig}\n\n")
                    doc = module.__doc__ or "No documentation available."
                    file.write(f"   {doc.strip()}\n\n")

            # if inspect.getdoc(module) is not None and hasattr(module, '__class__'):
            #     file.write(f"{inspect.getdoc(module)}\n")

            # Extract public functions
            for name, func in inspect.getmembers(module, inspect.isfunction):
                if name.startswith("_"):
                    continue  # Skip private functions
                if not inspect.getdoc(func) and skip_undocumented:  # Skip undocumented funcs
                    continue
                sig = inspect.signature(func)
                file.write(f".. function:: {name}{sig}\n\n")
                doc = func.__doc__ or "No documentation available."
                file.write(f"   {doc.strip()}\n\n")

            # Extract public classes and their public methods
            for name, cls in inspect.getmembers(module, inspect.isclass):
                if name.startswith("_"):
                    continue  # Skip private classes
                if not inspect.getdoc(cls) and skip_undocumented:
                    continue  # Skip writing undocumented
                file.write(f".. class:: {name}\n\n")
                class_doc = cls.__doc__ or "No documentation available."
                file.write(f"   {class_doc.strip()}\n\n")

                for method_name, method in inspect.getmembers(cls, inspect.isfunction):
                    if method_name.startswith("_"):
                        continue  # Skip private methods
                    if not inspect.getdoc(method) and skip_undocumented:
                        continue
                    sig = inspect.signature(method)
                    file.write(f"   .. method:: {method_name}{sig}\n\n")
                    method_doc = method.__doc__ or "No documentation available."
                    file.write(f"      {method_doc.strip()}\n\n")

    print(f"✅ API reference documentation written to: {output_file}")


if __name__ == '__main__':
    runs = [runner.upgrade_apsim_file, runner.collect_csv_by_model_path, runner.run_model_externally,
            runner.run_from_dir]
    docs([ApsimModel, *runs], output_file="api.rst")
    rsts = list(Path.cwd().rglob("*.rst")) + list(Path.cwd().rglob("*conf.py"))
    for rst in rsts:
        copy = shutil.copy2(rst, SENDTO.joinpath(rst.name))
        print(copy)
