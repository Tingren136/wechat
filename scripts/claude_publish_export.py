from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import Any

import markdown
from bs4 import BeautifulSoup, NavigableString, Tag


CLAUDE_THEME = {
    "page": "margin:0 auto;padding:0;background:#f7f3ee;",
    "article": (
        "max-width:720px;margin:0 auto;"
        "background:linear-gradient(180deg,#fffdf9 0%,#fffaf4 100%);"
        "border:1px solid rgba(216,109,71,.12);border-radius:28px;"
        "padding:56px 56px 72px;box-sizing:border-box;"
    ),
    "h1": (
        "color:#d86d47;font-size:44px;line-height:1.15;letter-spacing:-0.04em;"
        "margin:0 0 20px;font-weight:800;"
    ),
    "h2": (
        "font-size:30px;margin:56px 0 20px;color:#372e28;line-height:1.3;font-weight:800;"
        "display:inline-block;padding:0 14px 8px 0;border-bottom:3px solid rgba(216,109,71,.22);"
    ),
    "h3": "font-size:22px;margin:32px 0 16px;color:#54453b;line-height:1.35;font-weight:700;",
    "p": "font-size:19px;line-height:1.95;color:#312a25;margin:0 0 20px;",
    "lead": "font-size:16px;line-height:1.8;color:#8b7d72;margin:0 0 24px;",
    "strong": (
        "color:#d86d47;background:linear-gradient(180deg,transparent 0%,transparent 58%,rgba(216,109,71,.15) 58%,rgba(216,109,71,.15) 100%);"
        "padding:0 4px;font-weight:700;"
    ),
    "blockquote": (
        "margin:30px 0;padding:20px 24px;border-left:4px solid #d86d47;"
        "background:linear-gradient(180deg,#fdf6f1 0%,#faf2ea 100%);"
        "color:#725d51;border-radius:0 16px 16px 0;"
    ),
    "hr": "border:none;height:1px;width:132px;margin:44px auto;background:linear-gradient(90deg,transparent 0%,rgba(216,109,71,.58) 50%,transparent 100%);",
    "figure": "margin:34px 0;text-align:center;",
    "image": "display:block;width:100%;border-radius:14px;box-shadow:0 16px 38px rgba(25,27,31,.08);",
    "figcaption": (
        "margin:12px auto 0;color:#75675d;font-size:14px;line-height:1.7;text-align:center;"
        "letter-spacing:.01em;background:#fbf3ec;border-radius:999px;display:inline-block;padding:6px 14px;"
    ),
    "list": "margin:0 0 22px 1.2em;padding:0;",
    "list_item": "font-size:19px;line-height:1.95;color:#312a25;margin-bottom:10px;",
    "safe_list": "margin:0 0 24px 0;",
    "safe_list_row": "display:flex;align-items:flex-start;gap:14px;margin:0 0 14px 0;",
    "safe_list_marker": "display:inline-block;min-width:22px;font-size:19px;line-height:1.95;color:#312a25;font-weight:700;",
    "safe_list_text": "flex:1;font-size:19px;line-height:1.95;color:#312a25;",
    "table": (
        "width:100%;border-collapse:collapse;margin:28px 0;border:1px solid #e7ddd1;"
        "table-layout:fixed;background:#fff;border-radius:14px;overflow:hidden;"
    ),
    "th": "padding:14px 16px;border:1px solid #e7ddd1;text-align:left;vertical-align:top;font-size:15px;line-height:1.75;background:#f7ebe3;font-weight:700;",
    "td": "padding:14px 16px;border:1px solid #e7ddd1;text-align:left;vertical-align:top;font-size:15px;line-height:1.75;",
    "pre": (
        "background:#2f3138;color:#f5f6f7;border-radius:12px;padding:18px 20px;overflow:auto;"
        "margin:28px 0;box-shadow:0 18px 36px rgba(26,28,34,.18);"
    ),
    "code_block": (
        "display:block;font-size:15px;line-height:1.8;font-family:'JetBrains Mono','Cascadia Code',monospace;"
        "white-space:pre-wrap;"
    ),
    "inline_code": "background:#f2ebe5;border-radius:6px;padding:2px 6px;font-size:.9em;font-family:'JetBrains Mono','Cascadia Code',monospace;",
    "link": "color:#b45535;text-decoration:none;border-bottom:1px solid rgba(216,109,71,.35);",
}


def parse_frontmatter(content: str) -> tuple[dict[str, str], str]:
    match = re.match(r"^\s*---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$", content)
    if not match:
        return {}, content
    frontmatter: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip().strip('"').strip("'")
    return frontmatter, match.group(2)


def extract_title(frontmatter: dict[str, str], body: str, fallback: str) -> str:
    if frontmatter.get("title"):
        return frontmatter["title"]
    match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return fallback


def render_markdown(body: str) -> str:
    return markdown.markdown(
        body,
        extensions=["extra", "tables", "fenced_code", "sane_lists"],
        output_format="html5",
    )


def is_image_only_paragraph(tag: Tag) -> bool:
    meaningful_children = []
    for child in tag.children:
        if isinstance(child, NavigableString):
            if child.strip():
                meaningful_children.append(child)
            continue
        if isinstance(child, Tag):
            meaningful_children.append(child)
    return len(meaningful_children) == 1 and isinstance(meaningful_children[0], Tag) and meaningful_children[0].name == "img"


def style_table_rows(table: Tag) -> None:
    tbody = table.find("tbody")
    if not tbody:
        return
    rows = tbody.find_all("tr", recursive=False)
    for index, row in enumerate(rows):
        if index % 2 == 1:
            for cell in row.find_all("td", recursive=False):
                existing = cell.get("style", "")
                cell["style"] = f"{existing}background:#fdf7f2;".strip()


def normalize_figure(paragraph: Tag) -> Tag:
    image = paragraph.find("img")
    assert image is not None
    figure = paragraph.parent.new_tag("figure")
    figure["style"] = CLAUDE_THEME["figure"]
    image["style"] = CLAUDE_THEME["image"]
    alt = image.get("alt", "").strip()
    figure.append(image.extract())
    if alt:
        caption = paragraph.parent.new_tag("figcaption")
        caption["style"] = CLAUDE_THEME["figcaption"]
        caption.string = alt
        figure.append(caption)
    return figure


def build_safe_list(soup: BeautifulSoup, list_tag: Tag, ordered: bool) -> Tag:
    wrapper = soup.new_tag("section")
    wrapper["style"] = CLAUDE_THEME["safe_list"]
    wrapper["data-wechat-list"] = "ordered" if ordered else "unordered"

    items = list_tag.find_all("li", recursive=False)
    for index, item in enumerate(items, start=1):
        row = soup.new_tag("section")
        row["style"] = CLAUDE_THEME["safe_list_row"]

        marker = soup.new_tag("span")
        marker["style"] = CLAUDE_THEME["safe_list_marker"]
        marker.string = f"{index}." if ordered else "•"

        text = soup.new_tag("section")
        text["style"] = CLAUDE_THEME["safe_list_text"]
        for child in list(item.contents):
            text.append(child.extract())

        row.append(marker)
        row.append(text)
        wrapper.append(row)

    return wrapper


def replace_native_lists(soup: BeautifulSoup) -> None:
    list_tags = soup.find_all(["ol", "ul"])
    for list_tag in list_tags:
        safe_list = build_safe_list(soup, list_tag, ordered=list_tag.name == "ol")
        list_tag.replace_with(safe_list)


def append_style(tag: Tag, style: str) -> None:
    current = tag.get("style", "")
    tag["style"] = f"{current}{style}" if current else style


def sanitize_and_style(html: str, title: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    replace_native_lists(soup)

    for paragraph in soup.find_all("p"):
        if is_image_only_paragraph(paragraph):
            paragraph.replace_with(normalize_figure(paragraph))

    for tag in soup.find_all(True):
        tag.attrs.pop("class", None)
        if tag.name == "h1":
            tag["style"] = CLAUDE_THEME["h1"]
        elif tag.name == "h2":
            tag["style"] = CLAUDE_THEME["h2"]
        elif tag.name == "h3":
            tag["style"] = CLAUDE_THEME["h3"]
        elif tag.name == "p":
            tag["style"] = CLAUDE_THEME["p"]
        elif tag.name == "strong":
            tag["style"] = CLAUDE_THEME["strong"]
        elif tag.name == "blockquote":
            tag["style"] = CLAUDE_THEME["blockquote"]
            for nested in tag.find_all("p"):
                nested["style"] = "font-size:19px;line-height:1.95;color:#725d51;margin:0 0 12px;"
        elif tag.name == "hr":
            tag["style"] = CLAUDE_THEME["hr"]
        elif tag.name == "figure":
            tag["style"] = CLAUDE_THEME["figure"]
        elif tag.name == "img":
            tag["style"] = CLAUDE_THEME["image"]
        elif tag.name == "figcaption":
            tag["style"] = CLAUDE_THEME["figcaption"]
        elif tag.name == "table":
            tag["style"] = CLAUDE_THEME["table"]
            style_table_rows(tag)
        elif tag.name == "th":
            tag["style"] = CLAUDE_THEME["th"]
        elif tag.name == "td":
            append_style(tag, CLAUDE_THEME["td"])
        elif tag.name == "pre":
            tag["style"] = CLAUDE_THEME["pre"]
        elif tag.name == "code":
            if tag.parent and tag.parent.name == "pre":
                tag["style"] = CLAUDE_THEME["code_block"]
            else:
                tag["style"] = CLAUDE_THEME["inline_code"]
        elif tag.name == "a":
            tag["style"] = CLAUDE_THEME["link"]

    first_paragraph = soup.find("p")
    if first_paragraph and first_paragraph.find("em") and first_paragraph.get_text(strip=True) == first_paragraph.find("em").get_text(strip=True):
        first_paragraph["style"] = CLAUDE_THEME["lead"]
        em_tag = first_paragraph.find("em")
        if em_tag:
            em_tag.unwrap()

    wrapper = BeautifulSoup("", "html.parser")
    page = wrapper.new_tag("section")
    page["style"] = CLAUDE_THEME["page"]
    article = wrapper.new_tag("section")
    article["style"] = CLAUDE_THEME["article"]
    for node in list(soup.contents):
        article.append(node)
    page.append(article)
    wrapper.append(page)

    return (
        "<!DOCTYPE html>\n"
        "<html lang=\"zh-CN\">\n"
        "<head>\n"
        "  <meta charset=\"UTF-8\" />\n"
        f"  <title>{title}</title>\n"
        "</head>\n"
        f"<body>{wrapper.decode()}</body>\n"
        "</html>\n"
    )


def rewrite_local_image_sources(html: str, input_path: Path, output_path: Path) -> str:
    soup = BeautifulSoup(html, "html.parser")
    output_dir = output_path.parent
    for image in soup.find_all("img"):
        src = image.get("src", "").strip()
        if not src or re.match(r"^[a-z]+://", src, re.IGNORECASE):
            continue
        source_path = (input_path.parent / src).resolve()
        if not source_path.exists():
            continue
        image["src"] = Path(os.path.relpath(source_path, output_dir)).as_posix()
    return str(soup)


def export_markdown_to_html(input_path: Path, output_path: Path) -> dict[str, Any]:
    raw = input_path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(raw)
    title = extract_title(frontmatter, body, input_path.stem)
    html = render_markdown(body)
    html = rewrite_local_image_sources(html, input_path, output_path)
    full_html = sanitize_and_style(html, title)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(full_html, encoding="utf-8")
    return {
        "title": title,
        "author": frontmatter.get("author", ""),
        "summary": frontmatter.get("summary", frontmatter.get("digest", "")),
        "output_path": str(output_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="导出 Claude 风格的微信发布态 HTML")
    parser.add_argument("input", help="输入 Markdown 文件")
    parser.add_argument("-o", "--output", help="输出 HTML 文件")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        raise SystemExit(f"文件不存在: {input_path}")

    output_path = Path(args.output).resolve() if args.output else input_path.with_name(f"{input_path.stem}.claude.publish.html")
    result = export_markdown_to_html(input_path, output_path)
    print(result["output_path"])


if __name__ == "__main__":
    main()
