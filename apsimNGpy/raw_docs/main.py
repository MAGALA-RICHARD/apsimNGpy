import os
import shutil
from pathlib import Path
from typing import Union

import apsimNGpy
import inspect
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core.core import CoreModel
from apsimNGpy.core import runner
from apsimNGpy.core import (config, base_data, apsim, load_model, structure)
from apsimNGpy.manager import soilmanager, weathermanager
from apsimNGpy.validation import evaluator

modules = list((config, base_data, apsim))
SENDTO = Path.cwd().parent.parent / 'docs/source'
SENDTO.mkdir(parents=True, exist_ok=True)
SENDTO2 = Path.cwd().parent.parent.parent/'apsimNGpy-documentations/doc'
SENDTO2.mkdir(parents=True, exist_ok=True)


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
    module_set = list(set(modules))
    modules = sort_modules(module_set)
    for i in modules:
        print(i)

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
                is_class = inspect.isclass(module)
                if is_class and func.__module__ != module.__module__:
                    continue
                if 'apsimNGpy' not in func.__module__.split("."):
                    continue
                if name.startswith("_"):
                    continue  # Skip private functions
                if not inspect.getdoc(func) and skip_undocumented:  # Skip undocumented funcs
                    continue
                sig = inspect.signature(func)
                if is_class:
                    file.write(f".. function:: {module.__module__}.{module.__name__}.{name}{sig}\n\n")
                else:
                    file.write(f".. function:: {func.__module__}.{name}{sig}\n\n")

                doc = func.__doc__ or "No documentation available."
                file.write(f"   {doc.strip()}\n\n")

            # Extract public classes and their public methods
            for name, cls in inspect.getmembers(module, inspect.isclass):
                cls_name = cls.__name__

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
                    if method.__module__ != cls.__module__:
                        continue
                    sig = inspect.signature(method)
                    file.write(f"   .. method::{method.__module__}.{cls_name}.{method_name}{sig}\n\n")
                    method_doc = method.__doc__ or "No documentation available."
                    file.write(f"      {method_doc.strip()}\n\n")

    print(f"✅ API reference documentation written to: {output_file}")


def dc():
    ...


if __name__ == '__main__':
    from apsimNGpy.core_utils import database_utils
    from apsimNGpy.parallel import process

    runs = [
        runner.collect_csv_by_model_path,
        runner.run_model_externally,
        runner.run_from_dir,
        runner.upgrade_apsim_file, ]



    from apsimNGpy.core import core

    docs([apsim.ApsimModel, process, database_utils, core.CoreModel, core.ModelTools, evaluator, runner, base_data, weathermanager, soilmanager, structure, load_model],
         output_file="api.rst")

    rsts = list(Path.cwd().rglob("*.rst")) + list(Path.cwd().rglob("*conf.py"))
    if SENDTO2.exists():
        sd2 = SENDTO2
        for rst in rsts:
            file_name = SENDTO2.joinpath(rst.name)
            if file_name.exists():
                os.remove(file_name)
            copy = shutil.copy2(rst, file_name)

            if copy.stem =='api':

                ... #os.startfile(copy)
            print(copy)
    else:
        print(f"{SENDTO2} not present")

    for rst in rsts:
        file_name = SENDTO.joinpath(rst.name)
        if file_name.exists():
            os.remove(file_name)

        copy = shutil.copy2(rst, file_name)
        print(copy)

    # sphinx-build -b html docs/source docs/build/html
