# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

sys.path.insert(0, os.path.join("..", "src"))

site_packages = r"C:\Users\mfdal\AppData\Roaming\Python\Python310\site-packages"

if site_packages not in sys.path:
    sys.path.append(site_packages)

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "CCDA Parser"
copyright = "2024, Garron Anderson"
author = "Garron Anderson"
release = "0.0.3"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx.ext.todo", "sphinx.ext.viewcode", "sphinx.ext.autodoc"]

todo_include_todos = True

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
