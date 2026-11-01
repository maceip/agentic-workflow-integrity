"""Build website storybook and reading copy from story/pages.json.

pages.json is the canonical story source. This builder validates every
atomic page unit (image exists, alt text present, story text present,
Twitter distillation within character limit when a distillation exists)
and renders:
  story/PAGES.md        human reading / editing review copy
  story/storybook.html  static website page, one screen per story page
  story/distillations/TWITTER_DRAFTS.md  distillation status ledger

Distillations are secondary derivatives. The builder never invents
distillation text; empty distillation slots render as explicit pending
entries.
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

STORY_DIR = Path(__file__).resolve().parent
TWITTER_LIMIT = 280


def load_pages() -> dict:
    data = json.loads((STORY_DIR / "pages.json").read_text(encoding="utf-8"))
    pages = data["pages"]
    numbers = [page["page"] for page in pages]
    if numbers != sorted(numbers) or len(set(numbers)) != len(numbers):
        raise ValueError("page numbers must be unique and ascending")
    for page in pages:
        if not (STORY_DIR / page["image"]).is_file():
            raise ValueError(f"page {page['page']}: missing image {page['image']}")
        if not page.get("alt"):
            raise ValueError(f"page {page['page']}: alt text required")
        if not page.get("text"):
            raise ValueError(f"page {page['page']}: story text required")
        twitter = page["distillation"]["twitter"]
        if twitter["text"] is not None and len(twitter["text"]) > TWITTER_LIMIT:
            raise ValueError(
                f"page {page['page']}: twitter distillation "
                f"{len(twitter['text'])} chars exceeds {TWITTER_LIMIT}")
    return data


def render_markdown(data: dict) -> str:
    lines = [f"# {data['working_title']}", "",
             f"Status: {data['status']}", ""]
    for page in data["pages"]:
        lines += ["", "---", "",
                  f"## Page {page['page']} — {page['slug']}", "",
                  f"![{page['alt']}]({page['image']})", ""]
        lines += [paragraph + "\n" for paragraph in page["text"]]
        refs = ", ".join(f"`{ref}`" for ref in page["research_refs"])
        lines += [f"Research references: {refs}", ""]
    return "\n".join(lines)


def render_html(data: dict) -> str:
    title = html.escape(data["working_title"])
    sections = []
    for page in data["pages"]:
        paragraphs = "\n".join(
            f"      <p>{html.escape(text)}</p>" for text in page["text"])
        refs = ", ".join(html.escape(ref) for ref in page["research_refs"])
        sections.append(
            f'    <section class="page" id="page-{page["page"]}">\n'
            f'      <img src="{html.escape(page["image"])}" '
            f'alt="{html.escape(page["alt"])}">\n'
            f'      <div class="text">\n{paragraphs}\n      </div>\n'
            f'      <p class="refs">Page {page["page"]} · '
            f'Research references: {refs}</p>\n'
            f"    </section>")
    body = "\n".join(sections)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  body {{ margin: 0; background: #ffffff; color: #232323;
         font-family: Georgia, 'Times New Roman', serif; }}
  header {{ min-height: 70vh; display: flex; flex-direction: column;
            justify-content: flex-end; padding: 8vw 12vw; }}
  header h1 {{ font-size: 2.6rem; font-weight: 500; margin: 0 0 1rem; }}
  header p {{ max-width: 34rem; line-height: 1.7; color: #44403a; }}
  .page {{ min-height: 100vh; padding: 10vh 10vw; display: flex;
           flex-direction: column; justify-content: center; gap: 4vh; }}
  .page img {{ width: 100%; max-height: 68vh; object-fit: contain; }}
  .text {{ max-width: 36rem; }}
  .text p {{ font-size: 1.2rem; line-height: 1.85; margin: 0 0 1.1rem; }}
  .refs {{ font-family: ui-monospace, Menlo, monospace; font-size: 0.72rem;
           color: #6d675e; }}
</style>
</head>
<body>
  <header>
    <h1>{title}</h1>
    <p>A picture-book research log for agentic workflow integrity: the
    problem, the idea, and the testing of the idea, one page per step.
    Story pages make no measurements; every measurement lives in the
    linked research outputs.</p>
  </header>
{body}
</body>
</html>
"""


def render_ledger(data: dict) -> str:
    lines = ["# Twitter distillation ledger", "",
             "One atomic unit per story page. A distillation is written "
             "only after the story text for the page is approved as "
             "correct. `not_yet_distilled` is a deliberate state, not "
             "missing work.", ""]
    for page in data["pages"]:
        twitter = page["distillation"]["twitter"]
        text = twitter["text"] if twitter["text"] is not None else "(empty)"
        lines += [f"## Page {page['page']} — {page['slug']}", "",
                  f"- Status: {twitter['status']}",
                  f"- Image: `{twitter['image']}`",
                  f"- Text: {text}", ""]
    return "\n".join(lines)


def main() -> int:
    data = load_pages()
    (STORY_DIR / "PAGES.md").write_text(render_markdown(data), encoding="utf-8")
    (STORY_DIR / "storybook.html").write_text(render_html(data), encoding="utf-8")
    ledger = STORY_DIR / "distillations" / "TWITTER_DRAFTS.md"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text(render_ledger(data), encoding="utf-8")
    print(f"built {len(data['pages'])} pages: PAGES.md, storybook.html, "
          f"distillations/TWITTER_DRAFTS.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
