"""
trying to wean apsimNGpy from dotnet, it is very unpredictable as the APSIM undergoes continuous development
created on September 16 2025
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


from apsimNGpy.core.config import load_crop_from_disk

tree = load_apsimx_dict(load_crop_from_disk('Maize', out='out.apsimx'))
model_type = 'Models.PMF.Plant'
model_name = 'B_110'
parent = 'Models.Core.Simulation'
chid = find_child(tree, parent, model_type=model_type, model_name=model_name)
print(f"{(parent, model_type, model_name,)}: {chid}")
