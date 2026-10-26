"""
Generate the apsimNGpy API reference.

The generated ``api.rst`` uses Sphinx autodoc/autosummary directives
rather than manually reproducing Python signatures and docstrings.

Run
---
python doc/api_generator.py
"""

from __future__ import annotations

import inspect
import os
from pathlib import Path
from types import ModuleType
from typing import Iterable, Any
from dotenv import load_dotenv
from apsimNGpy.config import get_apsim_bin_path
root = Path(__file__).parent
load_dotenv(root/'apsimNGpy.env')
print(os.getenv("DOC_APSIM_BINARIES"))
# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PACKAGE_NAME = "apsimNGpy"

DOC_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = DOC_DIR / "api.rst"

SHOW_MODULE_VARIABLES = False
SHOW_INHERITED_MEMBERS = True
SKIP_UNDOCUMENTED = True
RESPECT_ALL = True
STRICT_DEFINED_ONLY = True
GLOBAL_DEDUPE = True


# ---------------------------------------------------------------------------
# APSIM binary
# ---------------------------------------------------------------------------

def _get_apsim_bin_path() -> Path:
    """
    Resolve the APSIM binary directory.

    ``TEST_APSIM_BINARY`` takes precedence when defined. Otherwise,
    apsimNGpy's configured APSIM binary path is used.
    """
    env_path = os.getenv("DOC_APSIM_BINARIES", 'tests/apsim_binaries/APSIM2026.7.8087.0/bin')

    if env_path:
        return Path(env_path).expanduser().resolve()

    configured_path = get_apsim_bin_path()

    if not configured_path:
        raise RuntimeError(
            "Could not determine the APSIM binary path. "
            "Set TEST_APSIM_BINARY or configure apsimNGpy.")

    return Path(configured_path).expanduser().resolve()


# ---------------------------------------------------------------------------
# RST helpers
# ---------------------------------------------------------------------------

def _heading(title: str, char: str = "-") -> str:
    """Return an RST heading."""
    return f"{title}\n{char * len(title)}\n\n"


def _qualified_name(obj: Any) -> str:
    """Return the fully qualified Python name of an object."""
    module = getattr(obj, "__module__", None)
    name = getattr(obj, "__qualname__", getattr(obj, "__name__", None))

    if module and name:
        return f"{module}.{name}"

    return str(name or obj)


def _write_lines(file, *lines: str) -> None:
    """Write RST lines followed by a blank line."""
    for line in lines:
        file.write(f"{line}\n")
    file.write("\n")


# ---------------------------------------------------------------------------
# Module inspection
# ---------------------------------------------------------------------------

def _public_names(
    module: ModuleType,
    *,
    respect_all: bool = RESPECT_ALL,
) -> list[str]:
    """
    Return public names exposed by a module.

    ``__all__`` is preferred when requested because it is the package's
    explicit declaration of its public API.
    """
    if respect_all:
        exported = getattr(module, "__all__", None)

        if isinstance(exported, (list, tuple, set)):
            return sorted(
                name
                for name in exported
                if isinstance(name, str) and not name.startswith("_")
            )

    return sorted(
        name
        for name in vars(module)
        if not name.startswith("_")
    )


def _defined_in_module(obj: Any, module: ModuleType) -> bool:
    """
    Return whether an object is defined by ``module``.

    Functions and classes expose ``__module__`` and can therefore be
    checked reliably. Plain values generally cannot.
    """
    owner = getattr(obj, "__module__", None)

    if owner is None:
        return True

    return owner == module.__name__


def _iter_functions(
    module: ModuleType,
    *,
    skip_undocumented: bool,
    respect_all: bool,
    strict_defined_only: bool,
):
    """Yield public functions from a module."""
    for name in _public_names(module, respect_all=respect_all):
        obj = getattr(module, name, None)

        if not inspect.isfunction(obj):
            continue

        if strict_defined_only and not _defined_in_module(obj, module):
            continue

        if skip_undocumented and not inspect.getdoc(obj):
            continue

        yield name, obj


def _iter_classes(
    module: ModuleType,
    *,
    skip_undocumented: bool,
    respect_all: bool,
    strict_defined_only: bool,
):
    """Yield public classes from a module."""
    for name in _public_names(module, respect_all=respect_all):
        obj = getattr(module, name, None)

        if not inspect.isclass(obj):
            continue

        if strict_defined_only and not _defined_in_module(obj, module):
            continue

        if skip_undocumented and not inspect.getdoc(obj):
            continue

        yield name, obj


def _iter_module_variables(
    module: ModuleType,
    *,
    respect_all: bool,
):
    """Yield public module-level data attributes."""
    for name in _public_names(module, respect_all=respect_all):
        obj = getattr(module, name, None)

        if inspect.ismodule(obj):
            continue

        if inspect.isclass(obj):
            continue

        if inspect.isroutine(obj):
            continue

        if callable(obj):
            continue

        yield name, obj


def _unique_modules(
    modules: Iterable[ModuleType],
) -> list[ModuleType]:
    """Return modules once, sorted deterministically by module name."""
    unique = {
        module.__name__: module
        for module in modules
    }

    return [
        unique[name]
        for name in sorted(unique)
    ]


# ---------------------------------------------------------------------------
# Sphinx directive writers
# ---------------------------------------------------------------------------

def _write_module_description(
    file,
    module: ModuleType,
) -> None:
    """Write the module-level autodoc directive."""
    _write_lines(
        file,
        f".. automodule:: {module.__name__}",
    )


def _write_function_summary(
    file,
    functions: list[tuple[str, Any]],
) -> None:
    """Write an autosummary table for functions."""
    if not functions:
        return

    file.write(_heading("Functions", "^"))

    _write_lines(
        file,
        ".. autosummary::",
        "   :nosignatures:",
    )

    for _, func in functions:
        file.write(f"   {_qualified_name(func)}\n")

    file.write("\n")


def _write_function_details(
    file,
    functions: list[tuple[str, Any]],
    seen: set[int],
    *,
    global_dedupe: bool,
) -> None:
    """Write detailed function documentation."""
    for _, func in functions:
        obj_id = id(func)

        if global_dedupe and obj_id in seen:
            continue

        file.write(
            f".. autofunction:: {_qualified_name(func)}\n\n"
        )

        if global_dedupe:
            seen.add(obj_id)


def _write_class_summary(
    file,
    classes: list[tuple[str, type]],
) -> None:
    """Write an autosummary table for classes."""
    if not classes:
        return

    file.write(_heading("Classes", "^"))

    _write_lines(
        file,
        ".. autosummary::",
        "   :nosignatures:",
    )

    for _, cls in classes:
        file.write(f"   {_qualified_name(cls)}\n")

    file.write("\n")


def _write_class_details(
    file,
    classes: list[tuple[str, type]],
    seen: set[int],
    *,
    skip_undocumented: bool,
    show_inherited_members: bool,
    global_dedupe: bool,
) -> None:
    """Write detailed class documentation using Sphinx autodoc."""
    for _, cls in classes:
        obj_id = id(cls)

        if global_dedupe and obj_id in seen:
            continue

        qualified = _qualified_name(cls)

        file.write(f".. autoclass:: {qualified}\n")
        file.write("   :members:\n")
        file.write("   :show-inheritance:\n")
        file.write("   :member-order: bysource\n")

        if show_inherited_members:
            file.write("   :inherited-members:\n")

        if not skip_undocumented:
            file.write("   :undoc-members:\n")

        file.write("\n")

        if global_dedupe:
            seen.add(obj_id)


def _write_module_variables(
    file,
    module: ModuleType,
    variables: list[tuple[str, Any]],
) -> None:
    """Write module-level variables with ``autodata``."""
    if not variables:
        return

    file.write(_heading("Module attributes", "^"))

    for name, _ in variables:
        qualified = f"{module.__name__}.{name}"

        file.write(f".. autodata:: {qualified}\n")
        file.write("   :annotation:\n\n")


# ---------------------------------------------------------------------------
# API generator
# ---------------------------------------------------------------------------

def docs(
    modules: Iterable[ModuleType] | ModuleType,
    output_file: str | Path = OUTPUT_FILE,
    *,
    skip_undocumented: bool = SKIP_UNDOCUMENTED,
    main_package: str = PACKAGE_NAME,
    respect_all: bool = RESPECT_ALL,
    strict_defined_only: bool = STRICT_DEFINED_ONLY,
    global_dedupe: bool = GLOBAL_DEDUPE,
    show_module_variables: bool = SHOW_MODULE_VARIABLES,
    show_inherited_members: bool = SHOW_INHERITED_MEMBERS,
) -> Path:
    """
    Generate a Sphinx API reference.

    Parameters
    ----------
    modules
        Module or iterable of modules to document.

    output_file
        Destination ``.rst`` file.

    skip_undocumented
        Exclude undocumented public functions and classes.

    main_package
        Package name displayed in the API title.

    respect_all
        Use a module's ``__all__`` when available.

    strict_defined_only
        Exclude imported functions/classes from a module section.

    global_dedupe
        Document identical objects only once across modules.

    show_module_variables
        Include public module-level data attributes.

    show_inherited_members
        Include inherited class members.

    Returns
    -------
    pathlib.Path
        Path to the generated API file.
    """
    if isinstance(modules, ModuleType):
        modules = [modules]
    else:
        modules = list(modules)

    modules = _unique_modules(modules)

    output_file = Path(output_file)
    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    seen_objects: set[int] = set()

    with output_file.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as file:

        # --------------------------------------------------------------
        # Header
        # --------------------------------------------------------------

        file.write(".. _api_ref:\n\n")

        title = f"{main_package}: API Reference"
        file.write(_heading(title, "="))

        file.write(
            "This page provides the public Python API for "
            f"``{main_package}``.\n\n"
        )

        # --------------------------------------------------------------
        # Modules
        # --------------------------------------------------------------

        for module in modules:

            file.write(
                _heading(module.__name__, "-")
            )

            _write_module_description(
                file,
                module,
            )

            # ----------------------------------------------------------
            # Functions
            # ----------------------------------------------------------

            functions = list(
                _iter_functions(
                    module,
                    skip_undocumented=skip_undocumented,
                    respect_all=respect_all,
                    strict_defined_only=strict_defined_only,
                )
            )

            if functions:
                _write_function_summary(
                    file,
                    functions,
                )

                _write_function_details(
                    file,
                    functions,
                    seen_objects,
                    global_dedupe=global_dedupe,
                )

            # ----------------------------------------------------------
            # Classes
            # ----------------------------------------------------------

            classes = list(
                _iter_classes(
                    module,
                    skip_undocumented=skip_undocumented,
                    respect_all=respect_all,
                    strict_defined_only=strict_defined_only,
                )
            )

            if classes:
                _write_class_summary(
                    file,
                    classes,
                )

                _write_class_details(
                    file,
                    classes,
                    seen_objects,
                    skip_undocumented=skip_undocumented,
                    show_inherited_members=show_inherited_members,
                    global_dedupe=global_dedupe,
                )

            # ----------------------------------------------------------
            # Module variables
            # ----------------------------------------------------------

            if show_module_variables:
                variables = list(
                    _iter_module_variables(
                        module,
                        respect_all=respect_all,
                    )
                )

                _write_module_variables(
                    file,
                    module,
                    variables,
                )

    print(
        f"API reference written to: {output_file}"
    )

    return output_file


# ---------------------------------------------------------------------------
# apsimNGpy API configuration
# ---------------------------------------------------------------------------

def _add_api_outlines() -> None:
    """
    Add inheritance outlines used by selected apsimNGpy classes.
    """
    from apsimNGpy.core_utils.deco import add_outline

    from apsimNGpy.core import (
        apsim,
        experiment,
        mult_cores,
        sensitivity_manager,
    )

    from apsimNGpy.optimizer.minimize import single_mixed
    from apsimNGpy.optimizer.problems import smp

    from apsimNGpy.sensitivity import (
        sens_file,
        sensitivity,
    )

    outlines = (
        (
            sensitivity.ConfigProblem,
            "apsimNGpy.sensitivity.sensitivity.ConfigProblem",
        ),
        (
            sens_file.ConfigProblem,
            "apsimNGpy.sensitivity.sens_file.ConfigProblem",
        ),
        (
            sens_file.Results,
            "apsimNGpy.sensitivity.sens_file.Results",
        ),
        (
            sensitivity_manager.SensitivityManager,
            "apsimNGpy.core.sensitivity_manager.SensitivityManager",
        ),
        (
            single_mixed.MixedVariableOptimizer,
            "apsimNGpy.optimizer.minimize.single_mixed.MixedVariableOptimizer",
        ),
        (
            smp.MixedProblem,
            "apsimNGpy.optimizer.problems.smp.MixedProblem",
        ),
        (
            experiment.ExperimentManager,
            "apsimNGpy.core.experiment.ExperimentManager",
        ),
        (
            apsim.ApsimModel,
            "apsimNGpy.core.apsim.ApsimModel",
        ),
        (
            mult_cores.MultiCoreManager,
            "apsimNGpy.core.mult_cores.MultiCoreManager",
        ),
    )

    for cls, base_path in outlines:
        add_outline(
            cls,
            include_inherited=True,
            base_path=base_path,
        )


def _api_modules() -> tuple[ModuleType, ...]:
    """Return modules included in the apsimNGpy API reference."""
    import apsimNGpy

    from apsimNGpy import (
        config,
        exceptions,
    )

    from apsimNGpy.core import (
        apsim,
        experiment,
        mult_cores,
        runner,
        sensitivity_manager,
    )

    from apsimNGpy.core_utils import database_utils

    from apsimNGpy.optimizer.minimize import single_mixed

    from apsimNGpy.optimizer.problems import (
        back_end,
        smp,
    )

    from apsimNGpy.parallel import process

    from apsimNGpy.sensitivity import (
        sens_file,
        sensitivity,
    )

    from apsimNGpy.validation import evaluator

    return (
        apsimNGpy,
        config,
        exceptions,
        apsim,
        experiment,
        mult_cores,
        runner,
        sensitivity_manager,
        database_utils,
        single_mixed,
        back_end,
        smp,
        process,
        sens_file,
        sensitivity,
        evaluator,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(
    apsim_bin_path: str | Path | None = None,) -> Path:
    """
    Generate ``doc/api.rst`` for apsimNGpy.

    Parameters
    ----------
    apsim_bin_path
        Optional APSIM binary directory. If omitted, the value is
        resolved from ``TEST_APSIM_BINARY`` or apsimNGpy configuration.

    Returns
    -------
    pathlib.Path
        Generated ``api.rst`` path.
    """
    from apsimNGpy.config import apsim_bin_context

    if apsim_bin_path is None:
        apsim_bin_path = _get_apsim_bin_path()

    apsim_bin_path = Path(
        apsim_bin_path).expanduser().resolve()

    with apsim_bin_context(apsim_bin_path):

        _add_api_outlines()

        modules = _api_modules()

        return docs(
            modules,
            output_file=OUTPUT_FILE,
            skip_undocumented=True,
            main_package=PACKAGE_NAME,
            respect_all=True,
            strict_defined_only=True,
            global_dedupe=True,
            show_module_variables=False,
            show_inherited_members=True,
        )


if __name__ == "__main__":
    main()