from __future__ import annotations

import argparse
import importlib.util
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup


THEME_LABELS = {
    "claude": "Claude",
    "nyt": "纽约时报",
    "deep-reading": "深度阅读",
    "medium": "Medium",
}


def load_publish_module():
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir / "publish_export_standalone.py",
        script_dir.parents[2] / "scripts" / "claude_publish_export.py",
    ]
    for module_path in candidates:
        if not module_path.exists():
            continue
        spec = importlib.util.spec_from_file_location("wechat_publish_export", module_path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module
    raise FileNotFoundError("未找到可用的发布态导出器。")


def replace_markdown_image_paths(markdown: str, rename_map: dict[str, str]) -> str:
    pattern = re.compile(r"(!\[[^\]]*\]\()([^)]+)(\))")

    def repl(match: re.Match[str]) -> str:
        source = match.group(2).strip()
        replacement = rename_map.get(source)
        if replacement is None:
            return match.group(0)
        return f"{match.group(1)}{replacement}{match.group(3)}"

    return pattern.sub(repl, markdown)


def collect_local_image_sources(markdown: str) -> list[str]:
    pattern = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
    sources: list[str] = []
    for raw_source in pattern.findall(markdown):
        source = raw_source.strip()
        if not source or re.match(r"^[a-z]+://", source, re.IGNORECASE):
            continue
        if source not in sources:
            sources.append(source)
    return sources


def safe_copy_images(markdown_path: Path, article_dir: Path, markdown: str) -> dict[str, str]:
    rename_map: dict[str, str] = {}
    used_names: set[str] = set()
    for source in collect_local_image_sources(markdown):
        source_path = (markdown_path.parent / source).resolve()
        if not source_path.exists():
            continue

        candidate_name = source_path.name
        stem = source_path.stem
        suffix = source_path.suffix
        counter = 1
        while candidate_name in used_names:
            counter += 1
            candidate_name = f"{stem}-{counter}{suffix}"

        used_names.add(candidate_name)
        rename_map[source] = candidate_name
        shutil.copy2(source_path, article_dir / candidate_name)
    return rename_map


def build_preview_html(publish_module: Any, normalized_markdown_path: Path, output_path: Path, theme_id: str, title: str) -> None:
    raw = normalized_markdown_path.read_text(encoding="utf-8")
    _, body = publish_module.parse_frontmatter(raw)
    html = publish_module.render_markdown(body)
    html = publish_module.rewrite_local_image_sources(html, normalized_markdown_path, output_path)
    full_html = publish_module.sanitize_and_style(html, title, publish_module.THEMES[theme_id])

    soup = BeautifulSoup(full_html, "html.parser")
    body_tag = soup.find("body")
    if body_tag is None:
        raise ValueError("预览 HTML 缺少 body。")

    page = body_tag.find("section")
    if page is None:
        raise ValueError("预览 HTML 缺少页面容器。")

    banner = soup.new_tag("section")
    banner["style"] = (
        "max-width:720px;margin:0 auto 18px auto;padding:12px 16px;"
        "border:1px dashed rgba(120,120,120,.35);border-radius:14px;"
        "font-size:14px;line-height:1.6;color:#555;background:rgba(255,255,255,.72);"
        "box-sizing:border-box;"
    )

    strong = soup.new_tag("strong")
    strong.string = f"{THEME_LABELS[theme_id]} 预览版"
    banner.append(strong)
    banner.append(" | 用于手动比较排版效果，正式发稿请使用对应“发布版 HTML”。")
    page.insert(0, banner)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(str(soup), encoding="utf-8")


def export_article_bundle(markdown_path: Path, image_root: Path, output_prefix: str = "最终排版") -> dict[str, Any]:
    publish_module = load_publish_module()
    markdown_path = markdown_path.resolve()
    image_root = image_root.resolve()
    if not markdown_path.exists():
        raise FileNotFoundError(f"Markdown 文件不存在: {markdown_path}")

    raw = markdown_path.read_text(encoding="utf-8")
    frontmatter, body = publish_module.parse_frontmatter(raw)
    title = publish_module.extract_title(frontmatter, body, markdown_path.stem)

    article_dir = image_root / title
    article_dir.mkdir(parents=True, exist_ok=True)

    rename_map = safe_copy_images(markdown_path, article_dir, raw)
    normalized_markdown = replace_markdown_image_paths(raw, rename_map)

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", dir=article_dir, delete=False) as temp_file:
        temp_file.write(normalized_markdown)
        normalized_markdown_path = Path(temp_file.name)

    themes_result: dict[str, dict[str, str]] = {}
    try:
        for theme_id, label in THEME_LABELS.items():
            preview_path = article_dir / f"{output_prefix}-{label}.html"
            publish_path = article_dir / f"{output_prefix}-{label}-发布版.html"

            build_preview_html(publish_module, normalized_markdown_path, preview_path, theme_id, title)
            publish_module.export_markdown_to_html(normalized_markdown_path, publish_path, theme_id=theme_id)

            themes_result[theme_id] = {
                "label": label,
                "preview": str(preview_path),
                "publish": str(publish_path),
            }
    finally:
        normalized_markdown_path.unlink(missing_ok=True)

    return {
        "title": title,
        "article_dir": str(article_dir),
        "themes": themes_result,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="导出公众号文章的 4 套预览与发布态 HTML")
    parser.add_argument("markdown", help="输入 Markdown 文件路径")
    parser.add_argument("--image-root", required=True, help="文章图片根目录，例如 H:\\3.写公众号素材\\imgs")
    parser.add_argument("--prefix", default="最终排版", help="输出文件名前缀")
    args = parser.parse_args()

    result = export_article_bundle(Path(args.markdown), Path(args.image_root), output_prefix=args.prefix)
    print(result["article_dir"])


if __name__ == "__main__":
    main()
