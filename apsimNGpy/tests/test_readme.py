import re
from pathlib import Path


def execute_rst_code(rst_file, verbose=False):
    with open(rst_file, 'r', encoding='utf-8') as file:
        content = file.read()

    # Extract Python code blocks
    code_blocks = re.findall(r".. code-block:: python\n\n((?:\s{4}.+\n)+)", content)

    for i, block in enumerate(code_blocks, 1):
        # Remove indentation and skip standalone comment lines
        code_lines = [
            line[4:] for line in block.split("\n")
            if line.strip() and not line.strip().startswith("#")
        ]
        code = "\n".join(code_lines)

        if verbose:
            print(f"\nExecuting Code Block {i}:\n{code}\n")

        try:
            exec(code)  # Execute the extracted Python code
            print(f"Success:::: {code}")
        except Exception as e:
            print(f"Code '{code}' failed with error: {e}")


if __name__ == "__main__":
    # Example usage
    cwd = Path.cwd()
    rdm = cwd.parent.parent.joinpath("README.rst")
    # D:\package\apsimNGpy\README.rst
    execute_rst_code(str(rdm))
