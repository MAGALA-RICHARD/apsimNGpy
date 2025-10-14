import inspect
from typing import Type, Tuple
from functools import wraps


def _defining_class(cls: Type, name: str) -> Type:
    """Return the class in the MRO that actually defines `name`."""
    for base in cls.__mro__:
        if name in base.__dict__:
            return base
    return cls  # fallback

def add_outline(cls: Type, include_inherited=True, base_path=None) -> type:
    names = dir(cls) if include_inherited else list(cls.__dict__.keys())
    names = sorted(n for n in names if not n.startswith("_"))

    props = []
    meths = []

    for name in names:
        # Use getattr_static to avoid triggering descriptors
        try:
            obj = inspect.getattr_static(cls, name)
        except AttributeError:
            continue

        # Determine defining class for accurate Sphinx target
        owner = _defining_class(cls, name)
        owner_qual = f"{owner.__module__}.{owner.__name__}"

        # Classification
        if isinstance(obj, property) and obj.__doc__:
            props.append((name, owner_qual))
        elif isinstance(obj, (staticmethod, classmethod)) and obj.__doc__:
            meths.append((name, owner_qual))
        elif inspect.isfunction(obj) and obj.__doc__:
            meths.append((name, owner_qual))
        elif inspect.isroutine(obj) and obj.__doc__:
            meths.append((name, owner_qual))
        else:
            # Public non-callable attribute
            if not callable(obj):
                props.append((name, owner_qual))

    # Deduplicate while preserving order
    def _uniq(seq: list[Tuple[str, str]]):
        seen = set()
        out = []
        for item in seq:
            if item not in seen:
                seen.add(item)
                out.append(item)
        return out

    props = _uniq(props)
    meths = _uniq(meths)

    props_lines = "\n".join(
        f"- :attr:`~{base_path or owner}.{n}`" for n, owner in props
    ) or "- *(none)*"
    meths_lines = "\n".join(
        f"- :meth:`~{base_path or owner}.{n}`" for n, owner in meths
    ) or "- *(none)*"

    outline = (
        "\n\n"
         f"List of Public Attributes:\n"
        "__________________________________\n\n"
         f"{props_lines}\n"
        f"List of Public Methods\n"
        "-----------------------------\n"
        f"{meths_lines}\n"
    )
    cls.__doc__ = (cls.__doc__ or "").rstrip() + outline

