"""
trying to wean apsimNGpy from dotnet, it is very unpredictable as the APSIM undergoes continuous development
created on September 16, 2025
"""
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Tuple, Union
from collections.abc import Mapping, Sequence

JSON = Union[Dict[str, Any], list]


def load_apsimx_dict(path: Union[str, Path]) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


from pathlib import Path
from typing import Any, Union, Optional
from collections.abc import Mapping, Sequence


def _type_name(t: Any) -> str:
    """Return the bare type name before the first comma."""
    return t.split(",", 1)[0].strip() if isinstance(t, str) else ""


def _children(node: Any):
    return node.get("Children", []) if isinstance(node, Mapping) else []


def _all_nodes(root: Mapping):
    """Iteratively walk every Mapping node in the tree via 'Children' only."""
    stack = list(reversed(_children(root))) + [root]
    seen = set()
    while stack:
        node = stack.pop()
        if not isinstance(node, Mapping):
            continue
        nid = id(node)
        if nid in seen:
            continue
        seen.add(nid)
        yield node
        ch = _children(node)
        if isinstance(ch, Sequence):
            stack.extend(reversed([c for c in ch if isinstance(c, Mapping)]))


def find_child(model: Union[str, Path, Mapping],
               parent: str,
               model_type: str,
               model_name: str) -> Optional[Mapping]:
    """
    Find a descendant with Name==model_name and $type matching model_type
    under the first node whose $type matches parent.
    Returns the node (dict) or None if not found.
    """
    tree = load_apsimx_dict(model) if not isinstance(model, Mapping) else model

    # 1) Locate the parent node (root if parent is the Simulations container)
    if parent == "Models.Core.Simulations":
        parent_node = tree
    else:
        parent_node = None
        for node in _all_nodes(tree):
            if _type_name(node.get("$type")) == parent:
                parent_node = node
                break
        if parent_node is None:
            return None

    # 2) Search under that parent for the target child (by Name and type)
    wanted_type = model_type  # compare only the left side of $type
    for node in _all_nodes(parent_node):
        if node is parent_node:
            continue
        if node.get("Name") == model_name and _type_name(node.get("$type")) == wanted_type:
            return node

    return None


from typing import Any, Union, Optional, List
from collections.abc import Mapping, Sequence


def _short_type_name(t: Any) -> str:
    """'Models.Core.Simulation, Models, Version=...' -> 'Simulation'."""
    if not isinstance(t, str):
        return ""
    left = t.split(",", 1)[0].strip()
    return left.rsplit(".", 1)[-1]  # last token after dot


def _strip_quotes(s: str) -> str:
    s = s.strip()
    if (len(s) >= 2) and ((s[0] == s[-1]) and s[0] in "'\""):
        return s[1:-1]
    return s


def find_by_path(
        model: Union[str, Path, Mapping],
        path: str,
        return_all: bool = False,
) -> Optional[Union[Mapping, List[Mapping]]]:
    """
    Resolve an APSIM node by a dotted path like:
      '.Simulations.Simulation:MySim.Plant:Maize'
    Rules:
      - Segment format: <Type>[:<Name>]
      - <Type> is matched against the *short* type (last token in $type).
      - If :<Name> is provided, 'Name' must match exactly.
      - Leading '.' is optional and denotes the root.
      - If multiple nodes match the final segment and return_all=False,
        the first match is returned.
    """
    tree = load_apsimx_dict(model) if not isinstance(model, Mapping) else model

    # Tokenize the path
    segments = [seg for seg in path.strip().lstrip(".").split(".") if seg]
    if not segments:
        return tree if return_all else tree  # root

    current: List[Mapping] = [tree]

    for seg in segments:
        # Parse '<Type>[:<Name>]'
        if ":" in seg:
            typ, name = seg.split(":", 1)
            typ, name = typ.strip(), _strip_quotes(name)
        else:
            typ, name = seg.strip(), None

        next_nodes: List[Mapping] = []

        for node in current:
            # 1) Allow matching the node itself (important for root 'Simulations')
            if isinstance(node, Mapping):
                st = _short_type_name(node.get("$type"))
                if st == typ and (name is None or node.get("Name") == name):
                    # keep node to descend from it in the next iteration
                    next_nodes.append(node)

            # 2) Match among its children
            for child in _children(node):
                if not isinstance(child, Mapping):
                    continue
                st = _short_type_name(child.get("$type"))
                if st != typ:
                    continue
                if name is not None and child.get("Name") != name:
                    continue
                next_nodes.append(child)

        # Advance
        if not next_nodes:
            return [] if return_all else None
        current = next_nodes

    # Finished consuming segments -> return matches
    if return_all:
        return current
    return current[0] if current else None

def list_model_paths(
    model: Union[str, Path, Mapping],
    model_type: str,
    fullpath: bool = True,
) -> List[str]:
    """
    Find all nodes whose $type (before any ', Models, Version=...') equals `model_type`
    and return either:
      - full dotted path of Names from root (e.g., '.Simulations.Baseline.Report')
      - or just the node Name (e.g., 'Report'), if fullpath=False.

    Parameters
    ----------
    model : str | Path | Mapping
        .apsimx file path or already-loaded dict.
    model_type : str
        e.g., 'Models.Report' or 'Models.Core.Simulation'.
    fullpath : bool
        True -> '.Name1.Name2...'; False -> 'Name' only.

    Returns
    -------
    List[str]
    """
    tree = load_apsimx_dict(model)

    def node_name(n: Mapping) -> str:
        nm = n.get("Name")
        return nm if nm not in (None, "") else (_short_type_name(n.get("$type")) or "<unnamed>")

    out: List[str] = []
    stack: List[Tuple[Tuple[str, ...], Mapping]] = [ ((), tree) ]

    while stack:
        path, node = stack.pop()
        if not isinstance(node, Mapping):
            continue

        cur_name = node_name(node)
        cur_path = path + (cur_name,)

        if _type_name(node.get("$type")) == model_type:
            out.append("." + ".".join(cur_path) if fullpath else cur_name)

        for child in reversed(_children(node)):
            if isinstance(child, Mapping):
                stack.append((cur_path, child))

    return out

from apsimNGpy.core.config import load_crop_from_disk

tree = load_apsimx_dict(load_crop_from_disk('Maize', out='out.apsimx'))
model_type = 'Models.Core.Simulation'
model_name = 'Simulation'
parent = 'Models.Core.Simulations'
chid = find_child(tree, parent, model_type=model_type, model_name=model_name)
print(f"{(parent, model_type, model_name,)}: {chid}")
node = find_by_path(tree, ".Simulations.Simulation")
list_model_paths('out.apsimx', 'Models.Report')