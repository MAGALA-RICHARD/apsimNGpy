import json, sys
import nbformat as nbf


def repair_ipynb(in_path, out_path=None):
    out_path = out_path or in_path
    nb = nbf.read(in_path, as_version=4)

    fixed = 0
    for cell in nb.cells:
        if cell.get("cell_type") == "code":
            # ensure outputs list
            if "outputs" not in cell or cell["outputs"] is None:
                cell["outputs"] = []
                fixed += 1
            # ensure execution_count present and valid (None or int)
            if "execution_count" not in cell or (
                    cell["execution_count"] is not None
                    and not isinstance(cell["execution_count"], int)
            ):
                cell["execution_count"] = None
                fixed += 1
    # write back
    nbf.write(nb, out_path)
    return fixed


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python repair_ipynb.py <notebook.ipynb> [out.ipynb]")
        sys.exit(1)
    changed = repair_ipynb(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print(f"Fixed fields in {changed} places.")
