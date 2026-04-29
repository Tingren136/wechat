from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import Any

import markdown
from bs4 import BeautifulSoup, NavigableString, Tag


def build_theme(
    page: str,
    article: str,
    h1: str,
    h2: str,
    h3: str,
    p: str,
    lead: str,
    strong: str,
    blockquote: str,
    blockquote_p: str,
    hr: str,
    figure: str,
    image: str,
    figcaption: str,
    safe_list_marker: str,
    safe_list_text: str,
    table: str,
    th: str,
    td: str,
    striped_td: str,
    pre: str,
    code_block: str,
    inline_code: str,
    link: str,
) -> dict[str, str]:
    return {
        "page": page,
        "article": article,
        "h1": h1,
        "h2": h2,
        "h3": h3,
        "p": p,
        "lead": lead,
        "strong": strong,
        "blockquote": blockquote,
        "blockquote_p": blockquote_p,
        "hr": hr,
        "figure": figure,
        "image": image,
        "figcaption": figcaption,
        "safe_list": "margin:0 0 24px 0;",
        "safe_list_row": "display:flex;align-items:flex-start;gap:14px;margin:0 0 14px 0;",
        "safe_list_marker": safe_list_marker,
        "safe_list_text": safe_list_text,
        "table": table,
        "th": th,
        "td": td,
        "striped_td": striped_td,
        "pre": pre,
        "code_block": code_block,
        "inline_code": inline_code,
        "link": link,
    }


THEMES = {
    "claude": build_theme(
        page="margin:0 auto;padding:0;background:#f7f3ee;",
        article="max-width:720px;margin:0 auto;background:linear-gradient(180deg,#fffdf9 0%,#fffaf4 100%);border:1px solid rgba(216,109,71,.12);border-radius:28px;padding:56px 56px 72px;box-sizing:border-box;",
        h1="color:#d86d47;font-size:44px;line-height:1.15;letter-spacing:-0.04em;margin:0 0 20px;font-weight:800;",
        h2="font-size:30px;margin:56px 0 20px;color:#372e28;line-height:1.3;font-weight:800;display:inline-block;padding:0 14px 8px 0;border-bottom:3px solid rgba(216,109,71,.22);",
        h3="font-size:22px;margin:32px 0 16px;color:#54453b;line-height:1.35;font-weight:700;",
        p="font-size:19px;line-height:1.95;color:#312a25;margin:0 0 20px;",
        lead="font-size:16px;line-height:1.8;color:#8b7d72;margin:0 0 24px;",
        strong="color:#d86d47;background:linear-gradient(180deg,transparent 0%,transparent 58%,rgba(216,109,71,.15) 58%,rgba(216,109,71,.15) 100%);padding:0 4px;font-weight:700;",
        blockquote="margin:30px 0;padding:20px 24px;border-left:4px solid #d86d47;background:linear-gradient(180deg,#fdf6f1 0%,#faf2ea 100%);color:#725d51;border-radius:0 16px 16px 0;",
        blockquote_p="font-size:19px;line-height:1.95;color:#725d51;margin:0 0 12px;",
        hr="border:none;height:1px;width:132px;margin:44px auto;background:linear-gradient(90deg,transparent 0%,rgba(216,109,71,.58) 50%,transparent 100%);",
        figure="margin:34px 0;text-align:center;border-radius:18px;overflow:hidden;",
        image="display:block;width:100%;border-radius:14px;box-shadow:0 16px 38px rgba(25,27,31,.08);",
        figcaption="margin:12px auto 0;color:#75675d;font-size:14px;line-height:1.7;text-align:center;letter-spacing:.01em;background:#fbf3ec;border-radius:999px;display:inline-block;padding:6px 14px;",
        safe_list_marker="display:inline-block;min-width:22px;font-size:19px;line-height:1.95;color:#312a25;font-weight:700;",
        safe_list_text="flex:1;font-size:19px;line-height:1.95;color:#312a25;",
        table="width:100%;border-collapse:collapse;margin:28px 0;border:1px solid #e7ddd1;table-layout:fixed;background:#fff;border-radius:14px;overflow:hidden;",
        th="padding:14px 16px;border:1px solid #e7ddd1;text-align:left;vertical-align:top;font-size:15px;line-height:1.75;background:#f7ebe3;font-weight:700;",
        td="padding:14px 16px;border:1px solid #e7ddd1;text-align:left;vertical-align:top;font-size:15px;line-height:1.75;",
        striped_td="background:#fdf7f2;",
        pre="background:#2f3138;color:#f5f6f7;border-radius:12px;padding:18px 20px;overflow:auto;margin:28px 0;box-shadow:0 18px 36px rgba(26,28,34,.18);",
        code_block="display:block;font-size:15px;line-height:1.8;font-family:'JetBrains Mono','Cascadia Code',monospace;white-space:pre-wrap;",
        inline_code="background:#f2ebe5;border-radius:6px;padding:2px 6px;font-size:.9em;font-family:'JetBrains Mono','Cascadia Code',monospace;",
        link="color:#b45535;text-decoration:none;border-bottom:1px solid rgba(216,109,71,.35);",
    ),
    "nyt": build_theme(
        page="margin:0 auto;padding:0;background:#f6f4ef;font-family:Georgia,'Noto Serif SC','Songti SC','STSong',serif;",
        article="max-width:720px;margin:0 auto;background:#fffdfa;padding:54px 56px 78px;border:1px solid #ece6dd;box-sizing:border-box;",
        h1="font-size:45px;line-height:1.14;color:#111;margin:0 0 16px;font-weight:700;letter-spacing:-0.03em;padding-bottom:18px;border-bottom:1px solid #1d1b18;",
        h2="font-size:31px;margin:60px 0 22px;color:#151312;line-height:1.26;font-weight:700;text-align:center;",
        h3="font-size:22px;margin:34px 0 16px;color:#222;font-weight:700;",
        p="font-size:19px;line-height:1.96;color:#1f1c18;margin:0 0 20px;",
        lead="font-size:16px;line-height:1.8;color:#615a54;margin:0 0 24px;font-style:italic;",
        strong="color:#111;font-weight:700;",
        blockquote="margin:30px 0;padding:20px 26px;border-left:3px solid #202020;background:#f4f2ee;color:#3a3530;",
        blockquote_p="font-size:19px;line-height:1.96;color:#3a3530;margin:0 0 12px;font-style:italic;",
        hr="border:none;height:1px;width:126px;margin:42px auto;background:#d4ccc2;",
        figure="margin:34px 0;text-align:center;border-radius:18px;overflow:hidden;",
        image="display:block;width:100%;border-radius:0;box-shadow:none;",
        figcaption="margin:12px auto 0;color:#615a54;font-size:13px;line-height:1.7;text-align:center;background:#f4efe8;display:inline-block;padding:6px 14px;",
        safe_list_marker="display:inline-block;min-width:22px;font-size:19px;line-height:1.96;color:#1f1c18;font-weight:700;",
        safe_list_text="flex:1;font-size:19px;line-height:1.96;color:#1f1c18;",
        table="width:100%;border-collapse:collapse;margin:28px 0;border:1px solid #d8d1c7;table-layout:fixed;background:#fffdfa;",
        th="padding:14px 16px;border:1px solid #d8d1c7;text-align:left;vertical-align:top;font-size:15px;line-height:1.75;background:#f1ece4;font-weight:700;",
        td="padding:14px 16px;border:1px solid #d8d1c7;text-align:left;vertical-align:top;font-size:15px;line-height:1.75;",
        striped_td="background:#faf7f2;",
        pre="background:#30333a;color:#f4f4f6;border-radius:8px;padding:18px 20px;overflow:auto;margin:28px 0;box-shadow:0 12px 30px rgba(23,25,31,.18);",
        code_block="display:block;font-size:15px;line-height:1.8;font-family:'JetBrains Mono','Cascadia Code',monospace;white-space:pre-wrap;",
        inline_code="background:#efebe4;border-radius:4px;padding:2px 6px;font-size:.9em;font-family:'JetBrains Mono','Cascadia Code',monospace;",
        link="color:#111;text-decoration:none;border-bottom:1px solid rgba(17,17,17,.35);",
    ),
    "deep-reading": build_theme(
        page="margin:0 auto;padding:0;background:#f4f5f7;",
        article="max-width:720px;margin:0 auto;background:#ffffff;padding:48px 54px 70px;border-radius:22px;border:1px solid #e8ecf2;box-sizing:border-box;",
        h1="font-size:42px;line-height:1.18;color:#121821;margin:0 0 18px;font-weight:800;letter-spacing:-0.03em;",
        h2="font-size:30px;margin:58px 0 20px;color:#111827;line-height:1.3;font-weight:800;padding-left:18px;border-left:5px solid #c9d4e5;",
        h3="font-size:22px;margin:34px 0 14px;color:#303846;font-weight:700;",
        p="font-size:18px;line-height:1.95;color:#22252b;margin:0 0 18px;",
        lead="font-size:15px;line-height:1.8;color:#6f7683;margin:0 0 24px;font-weight:500;",
        strong="font-weight:800;color:#111827;",
        blockquote="margin:28px 0;padding:20px 24px;border:1px solid #e5eaf2;background:#f7f9fc;color:#4b5563;border-left:4px solid #1f2937;border-radius:16px;",
        blockquote_p="font-size:18px;line-height:1.95;color:#4b5563;margin:0 0 12px;",
        hr="border:none;height:1px;width:134px;margin:40px auto;background:linear-gradient(90deg,transparent 0%,rgba(148,163,184,.72) 50%,transparent 100%);",
        figure="margin:34px 0;text-align:center;border-radius:18px;overflow:hidden;",
        image="display:block;width:100%;border-radius:14px;box-shadow:0 16px 38px rgba(34,44,66,.08);",
        figcaption="margin:12px auto 0;color:#6f7683;font-size:13px;line-height:1.7;text-align:center;background:#f4f7fb;border-radius:999px;display:inline-block;padding:6px 14px;",
        safe_list_marker="display:inline-block;min-width:22px;font-size:18px;line-height:1.95;color:#22252b;font-weight:700;",
        safe_list_text="flex:1;font-size:18px;line-height:1.95;color:#22252b;",
        table="width:100%;border-collapse:collapse;margin:28px 0;border:1px solid #dbe1ea;table-layout:fixed;background:#fff;",
        th="padding:14px 16px;border:1px solid #dbe1ea;text-align:left;vertical-align:top;font-size:15px;line-height:1.75;background:#eef2f7;font-weight:700;",
        td="padding:14px 16px;border:1px solid #dbe1ea;text-align:left;vertical-align:top;font-size:15px;line-height:1.75;",
        striped_td="background:#f8fafc;",
        pre="background:#2f3440;color:#f5f7fa;border-radius:10px;padding:18px 20px;overflow:auto;margin:28px 0;box-shadow:0 14px 34px rgba(28,33,43,.18);",
        code_block="display:block;font-size:15px;line-height:1.8;font-family:'JetBrains Mono','Cascadia Code',monospace;white-space:pre-wrap;",
        inline_code="background:#edf2f7;border-radius:6px;padding:2px 6px;font-size:.9em;font-family:'JetBrains Mono','Cascadia Code',monospace;",
        link="color:#1f2937;text-decoration:none;border-bottom:1px solid rgba(31,41,55,.28);",
    ),
    "medium": build_theme(
        page="margin:0 auto;padding:0;background:#f8f7f4;",
        article="max-width:720px;margin:0 auto;background:#ffffff;padding:42px 44px 68px;border-radius:18px;box-sizing:border-box;",
        h1="font-size:44px;line-height:1.12;color:#111111;margin:0 0 16px;font-weight:800;letter-spacing:-0.035em;",
        h2="font-size:31px;margin:56px 0 18px;color:#151515;line-height:1.28;font-weight:800;letter-spacing:-0.03em;",
        h3="font-size:23px;margin:34px 0 14px;color:#333;font-weight:700;",
        p="font-size:20px;line-height:1.92;color:#242424;margin:0 0 18px;",
        lead="font-size:15px;line-height:1.8;color:#6b6b6b;margin:0 0 24px;",
        strong="font-weight:800;color:#151515;",
        blockquote="margin:28px 0;padding:8px 0 8px 18px;border-left:3px solid #181818;background:transparent;color:#4b4b4b;",
        blockquote_p="font-size:20px;line-height:1.92;color:#4b4b4b;margin:0 0 12px;font-style:italic;",
        hr="border:none;height:1px;width:132px;margin:40px auto;background:#ddd8cf;",
        figure="margin:34px 0;text-align:center;border-radius:18px;overflow:hidden;",
        image="display:block;width:100%;border-radius:14px;box-shadow:0 12px 28px rgba(0,0,0,.05);",
        figcaption="margin:12px auto 0;color:#6b6b6b;font-size:13px;line-height:1.7;text-align:center;background:#f6f5f2;border-radius:999px;display:inline-block;padding:6px 14px;",
        safe_list_marker="display:inline-block;min-width:22px;font-size:20px;line-height:1.92;color:#242424;font-weight:700;",
        safe_list_text="flex:1;font-size:20px;line-height:1.92;color:#242424;",
        table="width:100%;border-collapse:collapse;margin:28px 0;border:1px solid #e6e3dd;table-layout:fixed;background:#fff;",
        th="padding:14px 16px;border:1px solid #e6e3dd;text-align:left;vertical-align:top;font-size:15px;line-height:1.75;background:#f2f1ed;font-weight:700;",
        td="padding:14px 16px;border:1px solid #e6e3dd;text-align:left;vertical-align:top;font-size:15px;line-height:1.75;",
        striped_td="background:#faf9f6;",
        pre="background:#2f3136;color:#f8f8f8;border-radius:10px;padding:18px 20px;overflow:auto;margin:28px 0;box-shadow:0 12px 28px rgba(32,34,38,.18);",
        code_block="display:block;font-size:15px;line-height:1.8;font-family:'JetBrains Mono','Cascadia Code',monospace;white-space:pre-wrap;",
        inline_code="background:#f2f1ed;border-radius:6px;padding:2px 6px;font-size:.9em;font-family:'JetBrains Mono','Cascadia Code',monospace;",
        link="color:#151515;text-decoration:none;border-bottom:1px solid rgba(21,21,21,.28);",
    ),
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


def build_caption_text(alt_text: str) -> str:
    text = re.sub(r"\s+", " ", alt_text).strip()
    if not text:
        return ""
    if len(text) <= 22:
        return text

    if "，而是" in text:
        _, tail = text.split("，而是", 1)
        tail = tail.strip()
        if text.startswith("AI") and "AI" not in tail[:4]:
            tail = re.sub(r"^它", "", tail).strip()
            tail = f"AI {tail}"
        text = tail
    elif "：" in text:
        text = text.split("：", 1)[1].strip()
    elif "，" in text:
        text = text.split("，")[-1].strip()

    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > 26:
        text = f"{text[:26].rstrip('，。；：、 ')}..."
    return text


def style_table_rows(table: Tag, theme: dict[str, str]) -> None:
    tbody = table.find("tbody")
    if not tbody:
        return
    rows = tbody.find_all("tr", recursive=False)
    for index, row in enumerate(rows):
        if index % 2 == 1:
            for cell in row.find_all("td", recursive=False):
                existing = cell.get("style", "")
                cell["style"] = f"{existing}{theme['striped_td']}".strip()


def normalize_figure(paragraph: Tag, theme: dict[str, str]) -> Tag:
    image = paragraph.find("img")
    assert image is not None
    figure = paragraph.parent.new_tag("figure")
    figure["style"] = theme["figure"]
    image["style"] = theme["image"]
    alt = image.get("alt", "").strip()
    caption_text = build_caption_text(alt)
    figure.append(image.extract())
    if caption_text:
        caption = paragraph.parent.new_tag("figcaption")
        caption["style"] = theme["figcaption"]
        caption.string = caption_text
        figure.append(caption)
    return figure


def build_safe_list(soup: BeautifulSoup, list_tag: Tag, ordered: bool, theme: dict[str, str]) -> Tag:
    wrapper = soup.new_tag("section")
    wrapper["style"] = theme["safe_list"]
    wrapper["data-wechat-list"] = "ordered" if ordered else "unordered"

    items = list_tag.find_all("li", recursive=False)
    for index, item in enumerate(items, start=1):
        row = soup.new_tag("section")
        row["style"] = theme["safe_list_row"]

        marker = soup.new_tag("span")
        marker["style"] = theme["safe_list_marker"]
        marker.string = f"{index}." if ordered else "•"

        text = soup.new_tag("section")
        text["style"] = theme["safe_list_text"]
        for child in list(item.contents):
            text.append(child.extract())

        row.append(marker)
        row.append(text)
        wrapper.append(row)

    return wrapper


def replace_native_lists(soup: BeautifulSoup, theme: dict[str, str]) -> None:
    list_tags = soup.find_all(["ol", "ul"])
    for list_tag in list_tags:
        safe_list = build_safe_list(soup, list_tag, ordered=list_tag.name == "ol", theme=theme)
        list_tag.replace_with(safe_list)


def append_style(tag: Tag, style: str) -> None:
    current = tag.get("style", "")
    tag["style"] = f"{current}{style}" if current else style


def sanitize_and_style(html: str, title: str, theme: dict[str, str]) -> str:
    soup = BeautifulSoup(html, "html.parser")
    replace_native_lists(soup, theme)

    for paragraph in soup.find_all("p"):
        if is_image_only_paragraph(paragraph):
            paragraph.replace_with(normalize_figure(paragraph, theme))

    for tag in soup.find_all(True):
        tag.attrs.pop("class", None)
        if tag.name == "h1":
            tag["style"] = theme["h1"]
        elif tag.name == "h2":
            tag["style"] = theme["h2"]
        elif tag.name == "h3":
            tag["style"] = theme["h3"]
        elif tag.name == "p":
            tag["style"] = theme["p"]
        elif tag.name == "strong":
            tag["style"] = theme["strong"]
        elif tag.name == "blockquote":
            tag["style"] = theme["blockquote"]
            for nested in tag.find_all("p"):
                nested["style"] = theme["blockquote_p"]
        elif tag.name == "hr":
            tag["style"] = theme["hr"]
        elif tag.name == "figure":
            tag["style"] = theme["figure"]
        elif tag.name == "img":
            tag["style"] = theme["image"]
        elif tag.name == "figcaption":
            tag["style"] = theme["figcaption"]
        elif tag.name == "table":
            tag["style"] = theme["table"]
            style_table_rows(tag, theme)
        elif tag.name == "th":
            tag["style"] = theme["th"]
        elif tag.name == "td":
            append_style(tag, theme["td"])
        elif tag.name == "pre":
            tag["style"] = theme["pre"]
        elif tag.name == "code":
            if tag.parent and tag.parent.name == "pre":
                tag["style"] = theme["code_block"]
            else:
                tag["style"] = theme["inline_code"]
        elif tag.name == "a":
            tag["style"] = theme["link"]

    first_paragraph = soup.find("p")
    if first_paragraph and first_paragraph.find("em") and first_paragraph.get_text(strip=True) == first_paragraph.find("em").get_text(strip=True):
        first_paragraph["style"] = theme["lead"]
        em_tag = first_paragraph.find("em")
        if em_tag:
            em_tag.unwrap()

    wrapper = BeautifulSoup("", "html.parser")
    page = wrapper.new_tag("section")
    page["style"] = theme["page"]
    article = wrapper.new_tag("section")
    article["style"] = theme["article"]
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


def export_markdown_to_html(input_path: Path, output_path: Path, theme_id: str = "claude") -> dict[str, Any]:
    raw = input_path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(raw)
    title = extract_title(frontmatter, body, input_path.stem)
    html = render_markdown(body)
    html = rewrite_local_image_sources(html, input_path, output_path)
    theme = THEMES.get(theme_id)
    if theme is None:
        available = ", ".join(THEMES.keys())
        raise ValueError(f"未知主题: {theme_id}。可用主题: {available}")
    full_html = sanitize_and_style(html, title, theme)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(full_html, encoding="utf-8")
    return {
        "title": title,
        "author": frontmatter.get("author", ""),
        "summary": frontmatter.get("summary", frontmatter.get("digest", "")),
        "output_path": str(output_path),
        "theme_id": theme_id,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="导出微信发布态 HTML")
    parser.add_argument("input", help="输入 Markdown 文件")
    parser.add_argument("-o", "--output", help="输出 HTML 文件")
    parser.add_argument("--theme", default="claude", choices=sorted(THEMES.keys()), help="发布主题")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        raise SystemExit(f"文件不存在: {input_path}")

    suffix = f".{args.theme}.publish.html"
    output_path = Path(args.output).resolve() if args.output else input_path.with_name(f"{input_path.stem}{suffix}")
    result = export_markdown_to_html(input_path, output_path, theme_id=args.theme)
    print(result["output_path"])


if __name__ == "__main__":
    main()
