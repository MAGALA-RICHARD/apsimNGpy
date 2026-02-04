# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'apsimNGpy'
copyright = '2025, Richard Magala'
author = 'Richard Magala'
release = '0.39.10.17'
html_title = "apsimNGpy Documentation"
# -------------------- General configuration ---------------------------------------------------
extensions = [
    # Core / common
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.napoleon',
    'sphinx.ext.doctest',
    'sphinx.ext.duration',
    'sphinx.ext.intersphinx',
    'sphinx.ext.mathjax',
    'sphinx.ext.githubpages',
    # Utility
    'sphinx_copybutton',

]

mermaid_params = [
    "--theme", "forest"
]
# autosummary: generate stub pages automatically
autosummary_generate = True

# InterSphinx
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
    "rtd": ("https://docs.readthedocs.io/en/stable/", None),
}
intersphinx_disabled_domains = ["std"]

# Mock any heavy/optional deps here if needed during docs build
autodoc_mock_imports = []

# Copybutton options (show >>> and $ prompts, strip on copy)
copybutton_prompt_text = r">>> |\$ "
copybutton_prompt_is_regexp = True

# Auto-section labels: prefix labels with the document path to avoid collisions
autosectionlabel_prefix_document = True

# RST prolog (optional defaults)
rst_prolog = """
.. default-role:: literal
"""

# What to ignore when looking for source files
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    ".apsimx",
    ".db",
]

# -- Options for HTML output -------------------------------------------------
html_theme = "sphinx_rtd_theme"
html_static_path = ['_static']

# -- Options for EPUB output -------------------------------------------------
epub_show_urls = "footnote"

# -- Path setup --------------------------------------------------------------
import sys, pathlib, os

# ROOT = pathlib.Path(__file__).resolve().parents[1]  # project root
# sys.path.insert(0, str(ROOT))

sys.path.insert(0, os.path.abspath('../'))

html_css_files = [
    'custom.css',
]
