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

WORKSPACE_DIRS = {
    "source": "01-原稿",
    "planning": "02-规划",
    "prompts_root": "03-提示词",
    "prompts_draft": "03-提示词/草稿",
    "prompts_final": "03-提示词/定稿",
    "assets_root": "04-素材",
    "body_images": "04-素材/正文配图",
    "cover_images": "04-素材/封面配图",
    "output_root": "05-排版",
    "previews": "05-排版/预览版",
    "publish": "05-排版/发布版",
    "delivery": "06-发布",
}

RULE_SUMMARY = """# Workflow Rules

- 这是半自动工作流，不是一键全自动发文。
- 每个关键阶段都必须停下来等待人工确认。
- 调用子 skill 时必须完整遵循其原始流程，不能跳过分析、确认或中间产物。
- 固定保留 4 套主题：Claude、纽约时报、深度阅读、Medium。
- 正文图片默认 4:3 横版。
- 连续纯文字不应超过约 300 中文字，必要时必须补充视觉中断。
- 视觉中断可以是图片、表格、引用块、对比卡、流程图、信息图。
- 正文、prompt、图片、预览 HTML、发布态 HTML 都必须归档到文章标题目录内。
- 发布公众号时只能使用发布态 HTML，不能直接使用预览页 HTML。
- 图注正文显示应优先使用短版，不直接照搬完整 alt。
- 图片圆角通过显示层裁切，不修改原图本身。
- 固定结尾不插入签名图，不额外追加单独作者行。
"""


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


def load_state_module():
    script_dir = Path(__file__).resolve().parent
    module_path = script_dir / "workflow_state_manager.py"
    spec = importlib.util.spec_from_file_location("workflow_state_manager", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_stage_runner_module():
    module_path = Path(__file__).resolve().parent / "workflow_stage_runner.py"
    spec = importlib.util.spec_from_file_location("workflow_stage_runner", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


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


def safe_copy_images(markdown_path: Path, target_images_dir: Path, source_dir: Path, markdown: str) -> dict[str, str]:
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
        target_path = target_images_dir / candidate_name
        rename_map[source] = Path(os.path.relpath(target_path, source_dir)).as_posix()
        shutil.copy2(source_path, target_path)
    return rename_map


def ensure_workspace(article_dir: Path) -> dict[str, Path]:
    workspace_paths: dict[str, Path] = {}
    for key, relative in WORKSPACE_DIRS.items():
        path = article_dir / Path(relative)
        path.mkdir(parents=True, exist_ok=True)
        workspace_paths[key] = path
    return workspace_paths


def write_workspace_files(
    article_dir: Path,
    workspace_paths: dict[str, Path],
    raw_markdown: str,
    title: str,
) -> None:
    draft_path = workspace_paths["source"] / "01-草稿.md"
    if not draft_path.exists():
        draft_path.write_text(raw_markdown, encoding="utf-8")
    for name in ["02-润色稿.md", "03-整理稿.md", "04-配图稿.md"]:
        placeholder = workspace_paths["source"] / name
        if not placeholder.exists():
            placeholder.write_text("", encoding="utf-8")

    rules_path = workspace_paths["planning"] / "规则摘要.md"
    rules_path.write_text(RULE_SUMMARY, encoding="utf-8")

    publish_checklist_path = workspace_paths["planning"] / "发布检查清单.md"
    publish_checklist_path.write_text(
        """# 发布检查清单

- [ ] 已选择最终主题
- [ ] 当前文件为发布态 HTML，而不是预览 HTML
- [ ] 没有 `<style>`、`<script>`、复杂 class
- [ ] 没有原生 `ol/ul/li`
- [ ] 图注为短版显示图注
- [ ] 无签名图
- [ ] 无额外单独作者行
- [ ] 长段纯文字已被视觉中断打断
- [ ] 图片路径指向当前文章目录
- [ ] 已完成草稿箱投递前人工确认
""",
        encoding="utf-8",
    )

    selected_theme_path = workspace_paths["delivery"] / "已选主题.txt"
    if not selected_theme_path.exists():
        selected_theme_path.write_text("", encoding="utf-8")

    state_module = load_state_module()
    stage_runner_module = load_stage_runner_module()
    state_path = workspace_paths["planning"] / "工作流状态.json"
    artifacts = {
        "draft": str(workspace_paths["source"] / "01-草稿.md"),
        "polished": str(workspace_paths["source"] / "02-润色稿.md"),
        "formatted": str(workspace_paths["source"] / "03-整理稿.md"),
        "with_images": str(workspace_paths["source"] / "04-配图稿.md"),
        "publish_checklist": str(publish_checklist_path),
        "selected_theme": str(selected_theme_path),
    }
    state_module.initialize_state(state_path=state_path, title=title, artifacts=artifacts)
    stage_runner_module.generate_stage_packet(state_path)


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
    workspace_paths = ensure_workspace(article_dir)
    write_workspace_files(article_dir, workspace_paths, raw, title)

    rename_map = safe_copy_images(markdown_path, workspace_paths["body_images"], workspace_paths["source"], raw)
    normalized_markdown = replace_markdown_image_paths(raw, rename_map)

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", dir=workspace_paths["source"], delete=False) as temp_file:
        temp_file.write(normalized_markdown)
        normalized_markdown_path = Path(temp_file.name)

    themes_result: dict[str, dict[str, str]] = {}
    try:
        for theme_id, label in THEME_LABELS.items():
            preview_path = workspace_paths["previews"] / f"{output_prefix}-{label}.html"
            publish_path = workspace_paths["publish"] / f"{output_prefix}-{label}-发布版.html"

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
        "workspace": {key: str(path) for key, path in workspace_paths.items()},
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
