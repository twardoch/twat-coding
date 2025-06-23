# Configuration file for the Sphinx documentation builder.

project = "twat-coding"
copyright = "2024, Adam Twardoch"
author = "Adam Twardoch"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_rtd_theme",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# MyST parser options
myst_enable_extensions = [
    "colon_fence",
]
