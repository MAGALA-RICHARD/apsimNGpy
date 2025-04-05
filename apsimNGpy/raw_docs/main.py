import shutil
from pathlib import Path
from typing import Union

import apsimNGpy
import inspect
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core import runner
from apsimNGpy.core import (config, base_data, apsim)
from apsimNGpy.manager import soilmanager, weathermanager

modules = list((config, base_data, apsim))
SENDTO = Path.cwd().parent.parent / 'docs/source'


def sort_modules(modules):
    """
    Sorts a list of modules alphabetically by their name.

    Args:
        modules (list): A list of module objects.

    Returns:
        list: A list of modules sorted by their names.
    """
    names = {i.__name__: i for i in modules}  # Create a dictionary mapping names to modules
    sorted_names = sorted(names.keys())  # Sort module names alphabetically
    return [names[name] for name in sorted_names]  # Return modules in sorted order


def docs(modules: Union[list, object], output_file: Union[str, Path] = "api.rst", skip_undocumented: bool = True,
         main_package="apsimNGpy"):
    """
    Extracts the docstrings of all public functions and classes in a module and writes them to an .rst file.

    Args:
        modules (list[module] or module): The Python modules or classes to extract documentation from.
        output_file (str): The path to the output .rst file.
        main_package (str): The name of the main package for writing the main title
    """
    if not isinstance(modules, list):
        modules = [modules]
    modules = sort_modules(modules)
    with open(output_file, "w", encoding="utf-8") as file:
        title = ''
        file.write(f"{main_package}: API Reference\n")
        file.write("-" * (len(main_package) + 15) + "\n\n")
        for module in modules:
            module_name = module.__name__
            file.write(f"{module.__name__} \n")
            file.write("-" * (len(module.__name__) + 15) + "\n\n")
            module_name = module.__name__ if hasattr(module, '__name__') else module.__class__.__name__
            class_name = 'Class' if hasattr(module, '__class__') else ''
            if inspect.isclass(module):
                sig = inspect.signature(module)
                file.write(f".. function:: {module.__module__}.{module.__name__}{sig}\n\n")
                doc = module.__doc__ or "No documentation available."
                file.write(f"   {doc.strip()}\n\n")
            if inspect.isfunction(module):
                if module_name not in module.__module__:
                    continue
                if not module.__name__.startswith('_'):
                    sig = inspect.signature(module)
                    file.write(f".. function:: {module.__module__}.{module.__name__}{sig}\n\n")
                    doc = module.__doc__ or "No documentation available."
                    file.write(f"   {doc.strip()}\n\n")

            # if inspect.getdoc(module) is not None and hasattr(module, '__class__'):
            #     file.write(f"{inspect.getdoc(module)}\n")

            # Extract public functions
            for name, func in inspect.getmembers(module, inspect.isfunction):
                if 'apsimNGpy' not in func.__module__.split("."):
                    continue
                if name.startswith("_"):
                    continue  # Skip private functions
                if not inspect.getdoc(func) and skip_undocumented:  # Skip undocumented funcs
                    continue
                sig = inspect.signature(func)
                file.write(f".. function:: {func.__module__}.{name}{sig}\n\n")

                doc = func.__doc__ or "No documentation available."
                file.write(f"   {doc.strip()}\n\n")

            # Extract public classes and their public methods
            for name, cls in inspect.getmembers(module, inspect.isclass):
                if 'apsimNGpy' not in cls.__module__.split("."):
                    continue
                if name.startswith("_"):
                    continue  # Skip private classes
                if not inspect.getdoc(cls) and skip_undocumented:
                    continue  # Skip writing undocumented
                file.write(f".. class:: {cls.__module__}{name}\n\n")
                class_doc = cls.__doc__ or "No documentation available."
                file.write(f"   {class_doc.strip()}\n\n")

                for method_name, method in inspect.getmembers(cls, inspect.isfunction):
                    if method_name.startswith("_"):
                        continue  # Skip private methods
                    if not inspect.getdoc(method) and skip_undocumented:
                        continue
                    sig = inspect.signature(method)
                    file.write(f"   .. method::{method.__module__}.{method_name}{sig}\n\n")
                    method_doc = method.__doc__ or "No documentation available."
                    file.write(f"      {method_doc.strip()}\n\n")

    print(f"✅ API reference documentation written to: {output_file}")


def dc():
    ...


if __name__ == '__main__':
    runs = [
        runner.collect_csv_by_model_path,
        runner.run_model_externally,
        runner.run_from_dir,
        runner.upgrade_apsim_file, ]
    docs([ApsimModel, runner, base_data, weathermanager, soilmanager], output_file="api.rst")

    rsts = list(Path.cwd().rglob("*.rst")) + list(Path.cwd().rglob("*conf.py"))
    for rst in rsts:
        copy = shutil.copy2(rst, SENDTO.joinpath(rst.name))
        print(copy)
