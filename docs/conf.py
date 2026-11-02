"""Sphinx configuration: builds the GitHub wiki pages as Markdown (``-b markdown``)."""

import tomllib
from pathlib import Path

from sphinx_markdown_builder.translator import MarkdownTranslator

ROOT = Path(__file__).resolve().parent.parent
_project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]

project = "pytui"
author = "gdamms"
copyright = "gdamms"
release = _project["version"]

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_markdown_builder",
]

root_doc = "Home"
source_suffix = {".md": "markdown", ".rst": "restructuredtext"}
exclude_patterns = ["_build", "_Sidebar.md"]

myst_enable_extensions = ["colon_fence", "deflist"]
myst_heading_anchors = 3

autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_typehints_format = "short"
autodoc_class_signature = "separated"
autodoc_default_options = {"members": True, "show-inheritance": True}

# Wiki links are page names without extension; anchors let cross-references land on members.
markdown_uri_doc_suffix = ""
markdown_anchor_signatures = True


class WikiTranslator(MarkdownTranslator):
    # The keyword-only `*` in signatures is an abbreviation node the builder doesn't know.
    def visit_abbreviation(self, node):
        pass

    def depart_abbreviation(self, node):
        pass


def setup(app):
    app.set_translator("markdown", WikiTranslator)
