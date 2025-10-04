import inspect
import textwrap
from pathlib import Path
from typing import Iterable, Union, List, Set, Any

# ---------- knobs to tweak ----------
INHERIT_NOTE_STYLE = "short"   # {"short","base","none"}
INDENT = "   "  # body indent under directives


# ---------- helpers ----------
def _dedent(s: str) -> str:
    return textwrap.dedent(s or "").strip("\n")


def _indent_block(s: str, indent: str = INDENT) -> str:
    """Indent every line of s for directive bodies."""
    if not s:
        return ""
    return "\n".join(f"{indent}{line}" if line else "" for line in s.splitlines())


def _write_block(f, text: str, indent: str = INDENT):
    """Write dedented + indented block followed by a blank line."""
    block = _indent_block(_dedent(text), indent=indent)
    if block:
        f.write(block + "\n\n")


def _safe_signature(obj) -> str:
    """Get a printable signature; fall back to () when inspect fails."""
    try:
        return str(inspect.signature(obj))
    except Exception:
        return "()"


# ---------- symbol collectors ----------
def _public_names_in_module(mod, *, respect_all: bool, strict_defined_only: bool) -> List[str]:
    if respect_all and hasattr(mod, "__all__") and isinstance(mod.__all__, (list, tuple)):
        return [n for n in mod.__all__ if not n.startswith("_")]

    names = []
    for name, obj in vars(mod).items():
        if name.startswith("_"):
            continue
        if inspect.ismodule(obj):
            continue
        if strict_defined_only and getattr(obj, "__module__", None) != mod.__name__:
            continue
        names.append(name)
    return sorted(set(names))


def _iter_public_functions(mod, skip_undocumented, respect_all, strict_defined_only):
    for name in _public_names_in_module(mod, respect_all=respect_all, strict_defined_only=strict_defined_only):
        obj = getattr(mod, name, None)
        if inspect.isfunction(obj):
            if skip_undocumented and not inspect.getdoc(obj):
                continue
            yield name, obj


def _iter_public_classes(mod, skip_undocumented, respect_all, strict_defined_only):
    for name in _public_names_in_module(mod, respect_all=respect_all, strict_defined_only=strict_defined_only):
        obj = getattr(mod, name, None)
        if inspect.isclass(obj):
            if skip_undocumented and not inspect.getdoc(obj):
                continue
            yield name, obj


def _iter_methods_including_inherited(cls, skip_undocumented):
    seen: Set[str] = set()
    for owner in cls.__mro__:
        if owner is object:
            continue
        for name, member in owner.__dict__.items():
            if name.startswith("_"):
                continue
            if not (inspect.isfunction(member) or inspect.ismethoddescriptor(member)):
                continue
            if name in seen:
                continue
            seen.add(name)
            func = member if inspect.isfunction(member) else getattr(cls, name, None)
            if func is None:
                continue
            if skip_undocumented and not inspect.getdoc(func):
                continue
            yield name, func, owner


def sort_modules(modules):
    names = {m.__name__: m for m in modules}
    return [names[n] for n in sorted(names)]


# ---------- main ----------
def docs(
    modules: Union[Iterable[object], object],
    output_file: Union[str, Path] = "api.rst",
    *,
    skip_undocumented: bool = True,
    main_package: str = "apsimNGpy",
    respect_all: bool = False,
    strict_defined_only: bool = True,
    global_dedupe: bool = True,
):
    if not isinstance(modules, (list, tuple, set)):
        modules = [modules]
    modules = sort_modules(list(set(modules)))

    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    seen_objects: Set[int] = set()

    def _maybe_skip(obj: Any) -> bool:
        return global_dedupe and (id(obj) in seen_objects)

    def _mark_seen(obj: Any):
        if global_dedupe:
            seen_objects.add(id(obj))

    with output_file.open("w", encoding="utf-8") as f:
        title = f"{main_package}: API Reference"
        f.write(title + "\n")
        f.write("=" * len(title) + "\n\n")

        for mod in modules:
            mod_title = f"{mod.__name__}"
            f.write(mod_title + "\n")
            f.write("-" * len(mod_title) + "\n\n")

            mod_doc = inspect.getdoc(mod)
            if mod_doc:
                _write_block(f, mod_doc, indent="")

            # ---- functions
            for name, func in _iter_public_functions(mod, skip_undocumented, respect_all, strict_defined_only):
                if _maybe_skip(func):
                    continue
                sig = _safe_signature(func)
                f.write(f".. py:function:: {func.__module__}.{func.__name__}{sig}\n\n")
                _write_block(f, inspect.getdoc(func) or "No documentation available.")
                _mark_seen(func)

            # ---- classes
            for name, cls in _iter_public_classes(mod, skip_undocumented, respect_all, strict_defined_only):
                if _maybe_skip(cls):
                    continue

                f.write(f".. py:class:: {cls.__module__}.{cls.__name__}\n\n")
                _write_block(f, inspect.getdoc(cls) or "No documentation available.")
                _mark_seen(cls)

                for mname, mfunc, owner in _iter_methods_including_inherited(cls, skip_undocumented):
                    sig = _safe_signature(mfunc)
                    if owner is cls or INHERIT_NOTE_STYLE == "none":
                        note = ""
                    elif INHERIT_NOTE_STYLE == "base":
                        note = f" (inherited from {owner.__name__})"
                    else:
                        note = " (inherited)"
                    f.write(f".. py:method:: {cls.__module__}.{cls.__name__}.{mname}{sig}{note}\n\n")
                    _write_block(f, inspect.getdoc(mfunc) or "No documentation available.")

    print(f"✅ API reference written to: {output_file}")


if __name__ == "__main__":
    SENDTO = Path.cwd().parent.parent / 'docs/source'
    SENDTO.mkdir(parents=True, exist_ok=True)
    SENDTO2 = Path.cwd().parent.parent.parent / 'apsimNGpy-documentations/doc'
    SENDTO2.mkdir(parents=True, exist_ok=True)
    import shutil, os

    # docs_build.py
    from pathlib import Path
    from apsimNGpy.core import config, base_data, apsim, mult_cores, pythonet_config
    from apsimNGpy.optimizer import moo
    from apsimNGpy.core import experimentmanager
    from apsimNGpy.core_utils import database_utils
    from apsimNGpy.parallel import process
    from apsimNGpy import exceptions
    from apsimNGpy.validation import evaluator
    from apsimNGpy.optimizer import single
    from apsimNGpy.manager import soilmanager, weathermanager

    OUT = Path("docs/source/api.rst")
    OUT.parent.mkdir(parents=True, exist_ok=True)

    modules = (process,apsim, mult_cores,experimentmanager,moo,
               evaluator,
               exceptions, single,soilmanager,weathermanager,
               database_utils, pythonet_config, config) # modules to document
    docs(modules, output_file=OUT, skip_undocumented=True, main_package="apsimNGpy")
    rsts = list(Path.cwd().rglob("*pi.rst"))  # + list(Path.cwd().rglob("*conf.py"))
    if SENDTO2.exists():
        sd2 = SENDTO2
        for rst in rsts:
            # turn off index
            if str(rst).endswith("dex.rst") or str(rst).endswith("inspection.rst"):
                continue
            file_name = SENDTO2.joinpath(rst.name)
            if file_name.exists():
                os.remove(file_name)
            copy = shutil.copy2(rst, file_name)

            if copy.stem == 'api':
                ...  # os.startfile(copy)
            print(copy)
    else:
        print(f"{SENDTO2} not present")

    for rst in rsts:
        if str(rst).endswith("index.rst") or str(rst).endswith("inspection.rst"):
            continue
        file_name = SENDTO.joinpath(rst.name)
        if file_name.exists():
            os.remove(file_name)

        copy = shutil.copy2(rst, file_name)
        print(copy)

