# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------

project = "Pishahang"
copyright = "2017, Pishahang"
author = "Pishahang"

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "recommonmark",
    "sphinx.ext.extlinks",
    "sphinxcontrib.plantuml",
    "sphinx_copybutton",
    "sphinxcontrib.redoc",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "package", "Thumbs.db", ".DS_Store", ".venv"]

extlinks = {"sourcefile": ("https://github.com/CN-UPB/Pishahang/blob/master/%s", "")}

plantuml_output_format = "svg_img"

highlight_language = "none"

redoc = [
    {
        "name": "Pishahang Gatekeeper API",
        "page": "developers/apis/gatekeeper",
        "spec": "../src/gatekeeper/openapi.yml",
        "opts": {
            "required-props-first": True,
            "expand-responses": ["200", "201", "204"],
        },
    },
]
redoc_uri = "https://cdn.jsdelivr.net/npm/redoc@2.0.0-rc.40/bundles/redoc.standalone.js"


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "canonical_url": "",
    "logo_only": True,
    "display_version": True,
    "prev_next_buttons_location": "bottom",
    "style_external_links": False,
    "style_nav_header_background": "white",
    # Toc options
    "collapse_navigation": True,
    "sticky_navigation": True,
    "navigation_depth": 4,
    "includehidden": True,
    "titles_only": False,
}

html_logo = "./figures/pishahang-logo.svg"


# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

html_css_files = ["css/custom.css"]
