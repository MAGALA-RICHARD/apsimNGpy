# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'apsimNGpy'
copyright = '2025, richard magala'
author = 'richard magala'
release = '0.32'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [

]

templates_path = ['_templates']
exclude_patterns = ['sphinx.ext.duration',
'sphinx.ext.napoleon',
                    'sphinx.ext.doctest',
                    'sphinx.ext.autodoc',
                    'sphinx.ext.autosummary',
                    'sphinx.ext.githubpages',
                    "sphinx.ext.intersphinx",
                    ]

intersphinx_mapping = {
    "rtd": ("https://docs.readthedocs.io/en/stable/", None),
    "python": ("https://docs.python.org/3/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
}
intersphinx_disabled_domains = ["std"]
autodoc_mock_imports = []  # Add external modules to mock if they are not installed

autosummary_generate = True  # Automatically create stub pages for modules
# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
# -- Options for EPUB output
epub_show_urls = "footnote"

html_theme = "sphinx_rtd_theme"

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", '.apsimx', '.db']

html_static_path = ['_static']

import os, sys
sys.path.insert(0, os.path.abspath('../'))
