import inspect
import textwrap
from pathlib import Path
from typing import Iterable, Union, List, Set, Any

# ---------- knobs ----------
INHERIT_NOTE_STYLE = "short"  # {"short","base","none"}
INDENT = "   "  # indentation for bodies
SHOW_MODULE_VARIABLES = True  # include public module-level attributes


# ---------- helpers ----------
def _dedent(s: str) -> str:
    return textwrap.dedent(s or "").strip("\n")


def _indent_block(s: str, indent: str = INDENT) -> str:
    if not s:
        return ""
    return "\n".join((indent + line) if line else "" for line in s.splitlines())


def _write_block(f, text: str, indent: str = INDENT):
    block = _indent_block(_dedent(text), indent)
    if block:
        f.write(block + "\n\n")


def _safe_signature(obj) -> str:
    try:
        return str(inspect.signature(obj))
    except Exception:
        return "()"


def _short_repr(value: Any, maxlen: int = 80) -> str:
    try:
        s = repr(value)
    except Exception:
        s = f"<{type(value).__name__}>"
    return (s if len(s) <= maxlen else s[: maxlen - 1] + "…")


# ---------- symbol collectors ----------
def _public_names_in_module(mod, *, respect_all: bool, strict_defined_only: bool) -> List[str]:
    if respect_all and hasattr(mod, "__all__") and isinstance(mod.__all__, (list, tuple)):
        return [n for n in mod.__all__ if not n.startswith("_")]

    names = []
    for name, obj in vars(mod).items():
        if name.startswith("_"):
            continue
        # skip imported modules
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


def _iter_public_module_attributes(mod, respect_all, strict_defined_only):
    for name in _public_names_in_module(mod, respect_all=respect_all, strict_defined_only=strict_defined_only):
        obj = getattr(mod, name, None)
        # exclude callables and classes (they are documented elsewhere)
        if inspect.isclass(obj) or inspect.isfunction(obj) or inspect.ismethod(obj):
            continue
        # descriptors (property at module level are rare but skip to avoid confusion)
        if inspect.ismethoddescriptor(obj):
            continue
        yield name, obj


def _unwrap_callable(member):
    """Return (callable_obj, kind) where kind in {'instance','classmethod','staticmethod'}."""
    # classmethod/staticmethod wrappers
    if isinstance(member, classmethod):
        return member.__func__, "classmethod"
    if isinstance(member, staticmethod):
        return member.__func__, "staticmethod"
    # regular function on class dict
    if inspect.isfunction(member) or inspect.ismethoddescriptor(member):
        return member, "instance"
    return None, None


def _iter_members_including_inherited(cls, skip_undocumented):
    """
    Yield dicts describing members visible on `cls`. Includes inherited.
    Kinds: method (instance/class/static), property, attribute.
    """
    seen: Set[str] = set()
    for owner in cls.__mro__:
        if owner is object:
            continue
        for name, member in owner.__dict__.items():
            if name.startswith("_"):
                continue
            if name in seen:
                continue

            # Properties
            if isinstance(member, property):
                seen.add(name)
                doc = inspect.getdoc(member.fget) or inspect.getdoc(member) or ""
                if skip_undocumented and not doc:
                    continue
                yield {
                    "kind": "property",
                    "name": name,
                    "owner": owner,
                    "doc": doc,
                }
                continue

            # Methods (instance/class/static)
            func, mkind = _unwrap_callable(member)
            if func is not None:
                seen.add(name)
                doc = inspect.getdoc(func) or ""
                if skip_undocumented and not doc:
                    continue
                yield {
                    "kind": "method",
                    "name": name,
                    "owner": owner,
                    "callable": func,
                    "method_kind": mkind,  # 'instance' | 'classmethod' | 'staticmethod'
                }
                continue

            # Data attributes (constants, annotations, etc.)
            if not callable(member) and not inspect.ismethoddescriptor(member):
                seen.add(name)
                # Read doc from annotations if present; otherwise none
                doc = ""
                if skip_undocumented and not doc:
                    # still include attributes even without doc (often useful)
                    pass
                yield {
                    "kind": "attribute",
                    "name": name,
                    "owner": owner,
                    "value": member,
                }


# ---------- ordering ----------
def sort_modules(modules):
    names = {m.__name__: m for m in modules}
    return [names[n] for n in sorted(names)]


# ---------- writer ----------
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
        ref = f".. _api_ref:"
        f.write(f"{ref}\n")
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

            # ---- module attributes (optional)
            if SHOW_MODULE_VARIABLES:
                attrs = list(_iter_public_module_attributes(mod, respect_all, strict_defined_only))
                if attrs:
                    f.write("Module attributes\n")
                    f.write("^^^^^^^^^^^^^^^^^^\n\n")
                    for name, val in attrs:
                        f.write(f".. py:attribute:: {mod.__name__}.{name}\n\n")
                        _write_block(f, f"Default value: ``{_short_repr(val)}``")

            # ---- functions
            funcs = list(_iter_public_functions(mod, skip_undocumented, respect_all, strict_defined_only))
            if funcs:
                f.write("Functions\n")
                f.write("^^^^^^^^^\n\n")
                for name, func in funcs:
                    if _maybe_skip(func):
                        continue
                    sig = _safe_signature(func)
                    f.write(f".. py:function:: {func.__module__}.{func.__name__}{sig}\n\n")
                    _write_block(f, inspect.getdoc(func) or "No documentation available.")
                    _mark_seen(func)

            # ---- classes (with nested members)
            classes = list(_iter_public_classes(mod, skip_undocumented, respect_all, strict_defined_only))
            if classes:
                f.write("Classes\n")
                f.write("^^^^^^^\n\n")
                for name, cls in classes:
                    if _maybe_skip(cls):
                        continue
                    f.write(f".. py:class:: {cls.__module__}.{cls.__name__}\n\n")
                    _write_block(f, inspect.getdoc(cls) or "No documentation available.")
                    _mark_seen(cls)

                    # Constructor (if documented)
                    init = cls.__dict__.get("__init__", None)
                    if init and (not skip_undocumented or inspect.getdoc(init)):
                        sig = _safe_signature(init)
                        f.write(_indent_block(f".. py:method:: {cls.__module__}.{cls.__name__}.__init__{sig}",
                                              INDENT) + "\n\n")
                        _write_block(f, inspect.getdoc(init) or "", indent=INDENT)

                    # Members (methods/properties/attributes), including inherited
                    for m in _iter_members_including_inherited(cls, skip_undocumented):
                        owner = m["owner"]
                        # inheritance note
                        if owner is cls or INHERIT_NOTE_STYLE == "none":
                            note = ""
                        elif INHERIT_NOTE_STYLE == "base":
                            note = f" (inherited from {owner.__name__})"
                        else:
                            note = " (inherited)"

                        if m["kind"] == "method":
                            mfunc = m["callable"]
                            sig = _safe_signature(mfunc)
                            # annotate method kind in text (class/staticmethod)
                            prefix = ""
                            if m["method_kind"] == "classmethod":
                                prefix = ".. py:classmethod::"
                            elif m["method_kind"] == "staticmethod":
                                prefix = ".. py:staticmethod::"
                            else:
                                prefix = ".. py:method::"
                            f.write(_indent_block(f"{prefix} {cls.__module__}.{cls.__name__}.{m['name']}{sig}{note}",
                                                  INDENT) + "\n\n")
                            _write_block(f, inspect.getdoc(mfunc) or "No documentation available.", indent=INDENT)

                        elif m["kind"] == "property":
                            f.write(_indent_block(f".. py:property:: {cls.__module__}.{cls.__name__}.{m['name']}{note}",
                                                  INDENT) + "\n\n")
                            _write_block(f, m["doc"] or "No documentation available.", indent=INDENT)

                        elif m["kind"] == "attribute":
                            # data attribute (constant/field)
                            f.write(
                                _indent_block(f".. py:attribute:: {cls.__module__}.{cls.__name__}.{m['name']}{note}",
                                              INDENT) + "\n\n")
                            _write_block(f, f"Default: ``{_short_repr(m['value'])}``", indent=INDENT)

    print(f"API reference written to: {output_file}")


# ---------------- CLI demo driver ----------------
if __name__ == "__main__":
    SENDTO = Path.cwd().parent.parent / 'docs/source'
    SENDTO.mkdir(parents=True, exist_ok=True)
    SENDTO2 = Path.cwd().parent.parent.parent / 'apsimNGpy-documentations/doc'
    SENDTO2.mkdir(parents=True, exist_ok=True)
    from apsimNGpy.core_utils.deco import add_outline

    import shutil, os
    from apsimNGpy.core import config, base_data, apsim, mult_cores, pythonet_config, experimentmanager, runner
    # from apsimNGpy.optimizer import moo, single
    from apsimNGpy.core_utils import database_utils
    from apsimNGpy.parallel import process
    from apsimNGpy import exceptions
    from apsimNGpy.validation import evaluator
    from apsimNGpy.optimizer.minimize import single_mixed
    from apsimNGpy.optimizer.problems import smp, back_end
    from apsimNGpy.core import senstivitymanager
    from apsimNGpy.senstivity import sensitivity
    from apsimNGpy.senstivity.sensitivity import ConfigProblem, run_sensitivity

    # ________________________________________________________________________________
    # add outline!!
    # ----------------------------------------------------------------------------------
    add_outline(sensitivity.ConfigProblem, include_inherited=True,
                base_path='apsimNGpy.senstivity.sensitivity.ConfigProblem')
    add_outline(senstivitymanager.SensitivityManager, include_inherited=True,
                base_path='apsimNGpy.core.senstivitymanager.SensitivityManager')
    add_outline(single_mixed.MixedVariableOptimizer, include_inherited=True,
                base_path='apsimNGpy.optimizer.minimize.single_mixed.MixedVariableOptimizer')
    add_outline(smp.MixedProblem, include_inherited=True,
                base_path='apsimNGpy.optimizer.problems.smp.MixedProblem')
    add_outline(experimentmanager.ExperimentManager, include_inherited=True,
                base_path='apsimNGpy.core.experimentmanager.ExperimentManager')
    add_outline(apsim.ApsimModel, include_inherited=True, base_path='apsimNGpy.core.apsim.ApsimModel')
    # add_outline(moo.MultiObjectiveProblem, include_inherited=True,
    #             base_path='apsimNGpy.optimizer.moo.MultiObjectiveProblem')
    # add_outline(single.MixedVariable, include_inherited=True,
    #             base_path='apsimNGpy.optimizer.single.MixedVariableProblem')
    add_outline(mult_cores.MultiCoreManager, include_inherited=True,
                )
    modules = (sensitivity,
               process, apsim, mult_cores, experimentmanager,  smp, single_mixed, senstivitymanager,
               evaluator, exceptions, database_utils, pythonet_config, config, runner, back_end,
               )

    OUT = Path("docs/source/api.rst").resolve()
    doc_folder = Path(__file__).parent.parent.parent / 'doc'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    docs(modules, output_file=OUT, skip_undocumented=True, main_package="apsimNGpy")
    shutil.copy2(OUT, doc_folder / 'api.rst')
    rsts = list(Path.cwd().rglob("*pi.rst"))
    if SENDTO2.exists():
        for rst in rsts:
            if str(rst).endswith("dex.rst") or str(rst).endswith("inspection.rst"):
                continue
            dst = SENDTO2 / rst.name
            if dst.exists():
                os.remove(dst)
            shutil.copy2(rst, dst)
            print(dst)
    else:
        print(f"{SENDTO2} not present")

    for rst in rsts:
        if str(rst).endswith("index.rst") or str(rst).endswith("inspection.rst"):
            continue
        dst = SENDTO / rst.name
        if dst.exists():
            os.remove(dst)
        shutil.copy2(rst, dst)
        print(dst)
