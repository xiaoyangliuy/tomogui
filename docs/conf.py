# Configuration file for the Sphinx documentation builder.

# -- Project information -----------------------------------------------------
project = 'TomoGUI'
copyright = '2024, Xiaoyang Liu, Alberto Mittone'
author = 'Xiaoyang Liu, Alberto Mittone'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
    'myst_parser',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_logo = None
html_favicon = None

# Theme options
html_theme_options = {
    'navigation_depth': 4,
    'collapse_navigation': False,
    'sticky_navigation': True,
    'includehidden': True,
}

# MyST parser settings
myst_enable_extensions = [
    "colon_fence",
    "deflist",
]

# -- Extension configuration -------------------------------------------------
autodoc_member_order = 'bysource'
napoleon_google_docstring = True
napoleon_numpy_docstring = True
