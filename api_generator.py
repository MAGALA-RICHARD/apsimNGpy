import os
import ast


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

                    doc = docstring.replace('FunctionDef', 'Function: ')
                    docstrings[key] = doc.strip('"').strip("'''").strip("```")
        return docstrings

    except (PermissionError, FileNotFoundError, OSError) as e:
        print(f"Error reading file {file_path}: {e}")
        return {}


def extract_docstrings_recursive(directory):
    """
    Recursively extracts docstrings from Python files in a directory and its subdirectories.

    Args:
        directory (str): Path to the root directory.

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
        print(f"Error processing directory {directory}: {e}")

    return docstrings_by_dir


def main(title, in_dir, out):
    docstrings = extract_docstrings_recursive(in_dir)
    with open(out, "w", encoding="utf-8") as md_file:
        md_file.write(f"# {title}\n\n")
        for directory, files in docstrings.items():
            # md_file.write(f"## Directory: {directory}\n\n")
            for file, docs in files.items():
                md_file.write(f"# Module: {file.strip('.py')}\n\n")

                for key, doc in docs.items():
                    if 'Arguments' in doc:
                        md_file.write(f"**Arguments:** {', '.join(doc)}\n\n")
                    md_file.write(f"## {key}\n\n")
                    md_file.write(f"```\n{doc}\n```\n\n")

    print(f"Docstrings have been written to {out}.")


def _main(title, in_dir, output):
    docstrings = extract_docstrings_recursive(in_dir)
    with open(output, "w", encoding="utf-8") as md_file:
        md_file.write("# Docstrings Documentation\n\n")
        for key, value in docstrings.items():
            md_file.write(f"## {key}\n\n")
            md_file.write(f"**Docstring:**\n\n{value['docstring']}\n\n")
            if value["Arguments"]:
                md_file.write(f"**Arguments:** {', '.join(value['Arguments'])}\n\n")


if __name__ == "__main__":
    root_directory = r'apsimNGpy'
    output_file = 'api.md'
    main('apsimNGpy API documentation', root_directory, output_file)
