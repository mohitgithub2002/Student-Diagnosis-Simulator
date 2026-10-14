"""HTML and PDF rendering for reports (Jinja2 + WeasyPrint, fonts bundled for Devanagari)."""

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.reports.wording import UI

HERE = Path(__file__).parent
_env = Environment(loader=FileSystemLoader(HERE / "templates"), autoescape=select_autoescape(["html"]))


def render_html(content: dict[str, Any], name: str, for_pdf: bool = False) -> str:
    """`content` must already be personalised; `name` fills the interface strings."""
    from app.reports.generator import personalize

    lang = content.get("language", "en")
    fonts = (HERE / "fonts").as_uri() if for_pdf else "/api/static/fonts"
    ui = personalize(UI[lang], name)
    return _env.get_template("report.html").render(r=content, ui=ui, fonts=fonts)


def render_pdf(content: dict[str, Any], name: str) -> bytes:
    from weasyprint import HTML

    return HTML(string=render_html(content, name, for_pdf=True), base_url=str(HERE)).write_pdf()
