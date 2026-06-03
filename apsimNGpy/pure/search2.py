import json
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Tuple, Union

JSON = Union[Dict[str, Any], list]


def load_apsimx_dict(path: Union[str, Path]) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------- internals ----------
def _type_matches(node: Dict[str, Any], type_like: str | None) -> bool:
    if not type_like:
        return True
    t = node.get("$type", "")
    full = t.split(",")[0]  # e.g. "Models.Clock"
    short = full.split(".")[-1]  # e.g. "Clock"
    return (type_like in full) or (type_like == short)


def _name_matches(node: Dict[str, Any], name: str | None) -> bool:
    return (name is None) or (node.get("Name") == name)


def _walk(node: JSON, path: Tuple[str, ...] = ()) -> Iterator[Tuple[Tuple[str, ...], Dict[str, Any]]]:
    if isinstance(node, dict):
        yield path, node
        for idx, ch in enumerate(node.get("Children") or []):
            label = node.get("Name", f"#{idx}")
            yield from _walk(ch, path + (label,))
    elif isinstance(node, list):
        for idx, ch in enumerate(node):
            yield from _walk(ch, path + (f"[{idx}]",))


# ---------- public API ----------
def find_first(root: JSON, *, type_like: str | None = None,
               name: str | None = None,
               predicate=None) -> Dict[str, Any] | None:
    """
    Return the first node matching criteria.
    type_like: "Models.Clock", "Clock", or any substring of $type.
    name: exact match on 'Name'.
    predicate: optional callable(node) -> bool for extra filtering.
    """
    for _, node in _walk(root):
        if _type_matches(node, type_like) and _name_matches(node, name) and (not predicate or predicate(node)):
            return node
    return None


def find_all(root: JSON, *, type_like: str | None = None,
             name: str | None = None,
             predicate=None, with_path: bool = False) -> Iterable:
    """
    Yield all nodes matching criteria. Set with_path=True to also get their paths.
    """
    for path, node in _walk(root):
        if _type_matches(node, type_like) and _name_matches(node, name) and (not predicate or predicate(node)):
            yield (path, node) if with_path else node


def path_to_str(path: Tuple[str, ...]) -> str:
    return "/".join(path)

from apsimNGpy.core.config import load_crop_from_disk
path2 = load_crop_from_disk('Maize', out = 'out.apsimx')
tree = load_apsimx_dict(path2)

# 1) First Simulation by name
sim = find_first(tree, type_like="Models.Core.Simulation", name="Simulation")

# 2) The Clock under that Simulation
clk = find_first(sim, type_like="Models.Clock")   # or add name="Clock"

# 3) All Reports (with their paths)
for p, rpt in find_all(sim, type_like="Models.Report", with_path=True):
    print(path_to_str(p), "->", rpt.get("Name"))

# 4) Tweak something (e.g., Clock start date) and save back
if clk:
    clk["Start"] = "1984-01-01T00:00:00"
    with open("/path/to/edited.apsimx", "w", encoding="utf-8") as f:
        json.dump(tree, f, ensure_ascii=False, indent=2)
