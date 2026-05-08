from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


THEME_LABELS = ["Claude", "纽约时报", "深度阅读", "Medium"]
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
VISUAL_BREAK_PLAN_JSON = "视觉中断清单.json"
PLANNER_TRACE_FILE = "配图执行记录.txt"
APPROVAL_FILE_LABELS = {
    "polish_review": "01-润色完成后确认.txt",
    "markdown_review": "02-Markdown整理后确认.txt",
    "image_count_review": "03-配图数量确认.txt",
    "illustration_plan_review": "04-配图规划完成后确认.txt",
    "image_generation_review": "05-图片生成前确认.txt",
    "image_insert_review": "06-插图回正文后确认.txt",
    "layout_review": "07-四套排版产出后确认.txt",
    "draft_publish_review": "08-草稿箱投递前确认.txt",
}


def load_state(state_path: Path) -> dict[str, Any]:
    return json.loads(state_path.read_text(encoding="utf-8"))


def add_issue(issues: list[dict[str, str]], code: str, message: str, severity: str = "blocker") -> None:
    issues.append({"code": code, "message": message, "severity": severity})


def file_has_content(path_str: str) -> bool:
    path = Path(path_str)
    return path.exists() and bool(path.read_text(encoding="utf-8").strip())


def approval_receipt_path(state: dict[str, Any]) -> Path | None:
    approval_dir = state.get("artifacts", {}).get("approval_dir", "")
    stage_id = state.get("current_stage_id", "").strip()
    if not approval_dir or not stage_id:
        return None
    filename = APPROVAL_FILE_LABELS.get(stage_id)
    if not filename:
        return None
    return Path(approval_dir) / filename


def validate_human_approval(state: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    receipt_path = approval_receipt_path(state)
    if receipt_path is None or not file_has_content(str(receipt_path)):
        add_issue(
            issues,
            "missing_human_approval_receipt",
            "当前阶段还没有人工确认回执，请先记录用户确认，再继续推进。",
        )
        return
    receipt_text = receipt_path.read_text(encoding="utf-8")
    if "状态: 已确认" not in receipt_text:
        add_issue(
            issues,
            "invalid_human_approval_receipt",
            "人工确认回执缺少“状态: 已确认”标记，请重新记录确认。",
        )


def count_text_units(text: str) -> int:
    normalized = re.sub(r"\s+", "", text)
    return len(normalized)


def is_visual_break_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith(("#", "![", ">", "|", "```", "<table", "<img", "<figure", "<blockquote")):
        return True
    if re.match(r"^(\d+\.|[-*+])\s+", stripped):
        return True
    return False


def scan_markdown_visual_breaks(markdown: str, max_chars: int = 300) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    current_lines: list[str] = []
    current_count = 0
    start_line = 1

    def flush(end_line: int) -> None:
        nonlocal current_lines, current_count, start_line
        if current_count > max_chars:
            snippet = "".join(current_lines)[:40]
            issues.append(
                {
                    "code": "long_plain_text_block",
                    "message": f"第 {start_line}-{end_line} 行存在约 {current_count} 字连续纯文字，超过 {max_chars} 字。",
                    "severity": "blocker",
                    "count": current_count,
                    "start_line": start_line,
                    "end_line": end_line,
                    "snippet": snippet,
                }
            )
        current_lines = []
        current_count = 0
        start_line = end_line + 1

    for line_number, raw_line in enumerate(markdown.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped:
            continue
        if is_visual_break_line(raw_line):
            flush(line_number - 1)
            start_line = line_number + 1
            continue
        if not current_lines:
            start_line = line_number
        current_lines.append(stripped)
        current_count += count_text_units(stripped)

    flush(len(markdown.splitlines()))
    return issues


def validate_polish_review(state: dict[str, Any], issues: list[dict[str, str]]) -> None:
    polished = state.get("artifacts", {}).get("polished", "")
    if not file_has_content(polished):
        add_issue(issues, "missing_polished_markdown", "润色稿不存在或仍为空，请先完成 02-润色稿.md。")
        return
    validate_human_approval(state, issues)


def validate_markdown_review(state: dict[str, Any], issues: list[dict[str, str]]) -> None:
    formatted_path = Path(state.get("artifacts", {}).get("formatted", ""))
    if not file_has_content(str(formatted_path)):
        add_issue(issues, "missing_formatted_markdown", "整理稿不存在或仍为空，请先完成 03-整理稿.md。")
        return
    text = formatted_path.read_text(encoding="utf-8")
    if "title:" not in text and not re.search(r"^#\s+\S+", text, re.MULTILINE):
        add_issue(issues, "missing_title_structure", "整理稿缺少标题或 frontmatter title。")
    validate_human_approval(state, issues)


def validate_visual_break_plan(
    markdown_path: Path,
    plan_path: Path,
    issues: list[dict[str, Any]],
    require_plan: bool,
) -> None:
    if not file_has_content(str(markdown_path)):
        return
    markdown = markdown_path.read_text(encoding="utf-8")
    long_block_issues = scan_markdown_visual_breaks(markdown)
    plan_exists = file_has_content(str(plan_path))
    if long_block_issues and (not require_plan or not plan_exists):
        issues.extend(long_block_issues)
    if require_plan and long_block_issues and not plan_exists:
        add_issue(
            issues,
            "missing_visual_break_plan",
            "存在超过 300 字的纯文字区段，但还没有补 `02-规划/视觉中断清单.md`。",
        )


def load_visual_break_plan_json(plan_json_path: Path) -> dict[str, Any] | None:
    if not file_has_content(str(plan_json_path)):
        return None
    try:
        data = json.loads(plan_json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    return data


def parse_required_body_images_from_plan(plan_data: dict[str, Any]) -> int:
    required = plan_data.get("required_body_images", 0)
    if isinstance(required, int):
        return max(required, 0)
    return 0


def parse_body_image_count_from_confirmation(confirm_path: Path) -> int | None:
    if not file_has_content(str(confirm_path)):
        return None
    text = confirm_path.read_text(encoding="utf-8")
    match = re.search(r"正文(?:配图)?\s*(\d+)\s*张?", text)
    if match:
        return int(match.group(1))
    match = re.search(r"(\d+)\s*张?\s*(?:正文|正文图|正文配图)", text)
    if match:
        return int(match.group(1))
    fallback = re.search(r"(\d+)", text)
    if fallback:
        return int(fallback.group(1))
    return None


def validate_visual_break_quota(plan_json_path: Path, confirm_path: Path, issues: list[dict[str, Any]]) -> None:
    plan_data = load_visual_break_plan_json(plan_json_path)
    if plan_data is None:
        add_issue(
            issues,
            "missing_visual_break_plan_json",
            "缺少或无法读取 `02-规划/视觉中断清单.json`，请先用统计脚本重新生成视觉中断清单。",
        )
        return
    required_body_images = parse_required_body_images_from_plan(plan_data)
    if required_body_images <= 0:
        add_issue(
            issues,
            "invalid_visual_break_plan_json",
            "`视觉中断清单.json` 缺少有效的 required_body_images，无法校验最少配图数量。",
        )
        return
    confirmed_body_images = parse_body_image_count_from_confirmation(confirm_path)
    if confirmed_body_images is None:
        add_issue(
            issues,
            "invalid_image_count_confirmation",
            "无法从 `配图数量确认.txt` 解析正文配图数量，请写明“正文配图 X 张”。",
        )
        return
    if confirmed_body_images < required_body_images:
        add_issue(
            issues,
            "insufficient_image_count_for_visual_breaks",
            f"正文配图数量不足：当前确认 {confirmed_body_images} 张，视觉中断至少需要 {required_body_images} 张。",
        )


def validate_planner_skill_trace(planning_dir: Path, issues: list[dict[str, Any]]) -> None:
    trace_path = planning_dir / PLANNER_TRACE_FILE
    if not file_has_content(str(trace_path)):
        add_issue(
            issues,
            "missing_planner_skill_trace",
            "缺少 `02-规划/配图执行记录.txt`，请记录 `planner_skill: baoyu-article-illustrator-plus` 后再继续。",
        )
        return
    text = trace_path.read_text(encoding="utf-8")
    if "planner_skill: baoyu-article-illustrator-plus" not in text:
        add_issue(
            issues,
            "invalid_planner_skill_trace",
            "检测到配图规划未明确使用增强版 skill，请改为 `baoyu-article-illustrator-plus` 并更新执行记录。",
        )


def validate_image_count_review(state_path: Path, issues: list[dict[str, str]]) -> None:
    state = load_state(state_path)
    formatted_path = Path(state.get("artifacts", {}).get("formatted", ""))
    confirm_path = state_path.parent / "配图数量确认.txt"
    visual_break_plan_path = state_path.parent / "视觉中断清单.md"
    visual_break_plan_json_path = state_path.parent / VISUAL_BREAK_PLAN_JSON
    validate_visual_break_plan(formatted_path, visual_break_plan_path, issues, require_plan=True)
    if not file_has_content(str(confirm_path)):
        add_issue(issues, "missing_image_count_confirmation", "尚未确认本篇文章需要几张图，请先补 02-规划/配图数量确认.txt。")
    validate_visual_break_quota(visual_break_plan_json_path, confirm_path, issues)
    validate_human_approval(state, issues)


def validate_illustration_plan_review(state_path: Path, issues: list[dict[str, str]]) -> None:
    state = load_state(state_path)
    planning_dir = state_path.parent
    prompts_dir = state_path.parent.parent / "03-提示词" / "草稿"
    formatted_path = Path(state.get("artifacts", {}).get("formatted", ""))
    visual_break_plan_path = planning_dir / "视觉中断清单.md"
    visual_break_plan_json_path = planning_dir / VISUAL_BREAK_PLAN_JSON
    confirm_path = planning_dir / "配图数量确认.txt"
    validate_visual_break_plan(formatted_path, visual_break_plan_path, issues, require_plan=True)
    validate_visual_break_quota(visual_break_plan_json_path, confirm_path, issues)
    validate_planner_skill_trace(planning_dir, issues)
    if not file_has_content(str(planning_dir / "outline.md")):
        add_issue(issues, "missing_outline", "缺少 02-规划/outline.md。")
    if not file_has_content(str(planning_dir / "batch.json")):
        add_issue(issues, "missing_batch_json", "缺少 02-规划/batch.json。")
    prompt_files = [path for path in prompts_dir.glob("*") if path.is_file()]
    if not prompt_files:
        add_issue(issues, "missing_prompt_drafts", "03-提示词/草稿 目录下还没有 prompt 文件。")
    validate_human_approval(state, issues)


def validate_image_generation_review(state_path: Path, issues: list[dict[str, str]]) -> None:
    state = load_state(state_path)
    body_images_dir = state_path.parent.parent / "04-素材" / "正文配图"
    image_files = [path for path in body_images_dir.glob("*") if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS]
    if not image_files:
        add_issue(issues, "missing_body_images", "正文配图目录为空，请先完成图片生成。")
    validate_human_approval(state, issues)


def validate_image_insert_review(state: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    with_images_path = Path(state.get("artifacts", {}).get("with_images", ""))
    if not file_has_content(str(with_images_path)):
        add_issue(issues, "missing_with_images_markdown", "配图稿不存在或仍为空，请先完成 04-配图稿.md。")
        return
    markdown = with_images_path.read_text(encoding="utf-8")
    issues.extend(scan_markdown_visual_breaks(markdown))
    validate_human_approval(state, issues)


def validate_layout_review(state_path: Path, issues: list[dict[str, str]]) -> None:
    state = load_state(state_path)
    article_dir = state_path.parent.parent
    preview_dir = article_dir / "05-排版" / "预览版"
    publish_dir = article_dir / "05-排版" / "发布版"
    missing_themes: list[str] = []
    for label in THEME_LABELS:
        preview_path = preview_dir / f"最终排版-{label}.html"
        publish_path = publish_dir / f"最终排版-{label}-发布版.html"
        if not preview_path.exists() or not publish_path.exists():
            missing_themes.append(label)
    if missing_themes:
        add_issue(
            issues,
            "missing_theme_outputs",
            f"以下主题的预览版或发布版 HTML 缺失：{', '.join(missing_themes)}。",
        )
    validate_human_approval(state, issues)


def validate_draft_publish_review(state: dict[str, Any], state_path: Path, issues: list[dict[str, str]]) -> None:
    article_dir = state_path.parent.parent
    selected_theme_path = Path(state.get("artifacts", {}).get("selected_theme", ""))
    publish_checklist_path = Path(state.get("artifacts", {}).get("publish_checklist", ""))
    if not file_has_content(str(selected_theme_path)):
        add_issue(issues, "missing_selected_theme", "还没有最终选定主题，请先写入 06-发布/已选主题.txt。")
        return
    theme_name = selected_theme_path.read_text(encoding="utf-8").strip()
    publish_path = article_dir / "05-排版" / "发布版" / f"最终排版-{theme_name}-发布版.html"
    if not publish_path.exists():
        add_issue(issues, "missing_selected_publish_html", f"缺少已选主题的发布版 HTML：{publish_path.name}。")
    if not file_has_content(str(publish_checklist_path)):
        add_issue(issues, "missing_publish_checklist", "发布检查清单不存在或仍为空。")
    validate_human_approval(state, issues)


def render_report(state: dict[str, Any], result: dict[str, Any]) -> str:
    lines = [
        "# 阶段检查报告",
        "",
        f"- 文章：{state.get('title', '')}",
        f"- 阶段：{state.get('current_stage_label', '')}",
        f"- 结果：{result['status']}",
        "",
    ]
    if not result["issues"]:
        lines.append("- 未发现阻塞项。")
        lines.append("")
        return "\n".join(lines)

    lines.append("## 问题列表")
    for item in result["issues"]:
        lines.append(f"- [{item['severity']}] `{item['code']}` {item['message']}")
    lines.append("")
    return "\n".join(lines)


def validate_stage(state_path: Path) -> dict[str, Any]:
    state = load_state(state_path)
    stage_id = state.get("current_stage_id", "")
    issues: list[dict[str, Any]] = []

    if stage_id == "polish_review":
        validate_polish_review(state, issues)
    elif stage_id == "markdown_review":
        validate_markdown_review(state, issues)
    elif stage_id == "image_count_review":
        validate_image_count_review(state_path, issues)
    elif stage_id == "illustration_plan_review":
        validate_illustration_plan_review(state_path, issues)
    elif stage_id == "image_generation_review":
        validate_image_generation_review(state_path, issues)
    elif stage_id == "image_insert_review":
        validate_image_insert_review(state, issues)
    elif stage_id == "layout_review":
        validate_layout_review(state_path, issues)
    elif stage_id == "draft_publish_review":
        validate_draft_publish_review(state, state_path, issues)

    result = {
        "stage_id": stage_id,
        "stage_label": state.get("current_stage_label", ""),
        "status": "blocked" if any(item["severity"] == "blocker" for item in issues) else "ok",
        "issues": issues,
    }
    report_path = state_path.parent / "阶段检查报告.md"
    report_path.write_text(render_report(state, result), encoding="utf-8")
    result["report_file"] = str(report_path)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="校验公众号文章工作流当前阶段")
    parser.add_argument("--state-path", required=True, help="工作流状态文件路径")
    args = parser.parse_args()
    result = validate_stage(Path(args.state_path))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
