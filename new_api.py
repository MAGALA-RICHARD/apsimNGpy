import os
import ast
from pathlib import Path


def format_type(annotation):
    """Converts AST child annotation into a human-readable format."""

    # Handle 'os.PathLike' explicitly
    if isinstance(annotation, ast.Name) and annotation.id == "PathLike":
        return "os.PathLike"

    # Handle 'Path' from pathlib explicitly
    elif isinstance(annotation, ast.Attribute) and annotation.attr == "Path":
        return "pathlib.Path"
    elif isinstance(annotation, ast.Attribute) and annotation.attr == "pd.DataFrame":
        return "pd.DataFrame"
    elif isinstance(annotation, ast.Attribute) and annotation.attr == "np.ndarray":
        return "numpy.ndarray"
    # Handle basic name types like 'bool', 'str', etc.
    elif isinstance(annotation, ast.Name):
        return annotation.id

    # Handle subscript types like List[Type] or Union[Type1, Type2]
    elif isinstance(annotation, ast.Subscript):
        value = format_type(annotation.value)  # the base child (like 'List', 'Union', etc.)
        slice_ = format_type(annotation.slice)  # the argument inside the brackets

        # Handle special cases like Union, List, Dict
        if value == "Union":
            # Handle Union[Type1, Type2]
            elements = [format_type(e) for e in annotation.slice.elts]
            return f"Union[{', '.join(elements)}]"
        elif value == "List":
            # Handle List[Type]
            return f"List[{slice_}]"
        elif value == "Dict":
            # Handle Dict[KeyType, ValueType]
            return f"Dict[{slice_[0]}, {slice_[1]}]"
        else:
            return f"{value}[{slice_}]"

    # Handle tuple child annotations
    elif isinstance(annotation, ast.Tuple):
        elements = [format_type(e) for e in annotation.elts]
        return f"tuple[{', '.join(elements)}]"

    # If the child is unknown, return 'unknown'
    else:
        return " "


def extract_docstrings(file_path):
    """
    Extracts all docstrings from a Python script.

    Args:
        file_path (str): The path to the Python script.

    Returns:
        dict: A dictionary containing the docstrings categorized by module, class, or function.
    """
    if not file_path.endswith(".py") or "__init__" in file_path:
        return {}

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            tree = ast.parse(file.read())

        docstrings = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                docstring = ast.get_docstring(node)
                if docstring:
                    name = node.__class__.__name__.strip("Def")
                    key = f"{name}: {node.name if hasattr(node, 'name') else 'Module'}"

                    # Extracting arguments (if available)
                    arguments = []
                    if isinstance(node, ast.FunctionDef):
                        for arg in node.args.args:
                            # Check if there's a child annotation, otherwise set it to 'unknown'
                            arg_type = 'unknown'
                            if arg.annotation:
                                arg_type = format_type(arg.annotation)

                            arguments.append(f"{arg.arg}: {arg_type}")

                    # Formatting the docstring to include function signature
                    if arguments:
                        docstrings[key] = f"{node.name}({', '.join(arguments)})\n\n{docstring.strip('\"\'')}"
                    else:
                        docstrings[key] = docstring.strip('\"\'')
        return docstrings

    except (PermissionError, FileNotFoundError, OSError) as e:
        print(f"Error reading file {file_path}: {e}")
        return {}


def extract_docstrings_recursive(directory):
    """
    Recursively extracts docstrings from Python files in a dir_path and its subdirectories.

    Args:
        directory (str): Path to the root dir_path.

    Returns:
        dict: A nested dictionary of directories and their respective Python files with extracted docstrings.
    """
    docstrings_by_dir = {}

    try:
        for root, _, files in os.walk(directory):
            docstrings_by_file = {}
            for file in files:
                if file.endswith(".py") and "__init__" not in file:
                    file_path = os.path.join(root, file)
                    file_docstrings = extract_docstrings(file_path)
                    if file_docstrings:
                        docstrings_by_file[file] = file_docstrings
            if docstrings_by_file:
                relative_path = os.path.relpath(root, directory)
                docstrings_by_dir[relative_path] = docstrings_by_file
    except Exception as e:
        print(f"Error processing dir_path {directory}: {e}")

    return docstrings_by_dir


def main(title, in_dir, out):
    docstrings = extract_docstrings_recursive(in_dir)
    with open(out, "w", encoding="utf-8") as md_file:
        md_file.write(f"# {title}\n\n")
        for directory, files in docstrings.items():
            # md_file.write(f"## Directory: {dir_path}\n\n")
            for file, docs in files.items():
                md_file.write(f"# Module: {file.strip('.py')}\n\n")

                for key, doc in docs.items():
                    md_file.write(f"## {key}\n\n")
                    md_file.write(f"```\n{doc}\n```\n\n")

    print(f"Docstrings have been written to {out}.")


if __name__ == "__main__":
    root_directory = r'apsimNGpy'
    doc = Path('docs')
    output_file = doc / 'api_documentation.md'
    main('apsimNGpy API documentation', root_directory, output_file)
