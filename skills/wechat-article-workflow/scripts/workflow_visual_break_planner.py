from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

DENSITY_CONFIG_FILE = "配图密度配置.json"


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


def scan_long_plain_text_blocks(markdown: str, max_chars: int) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    current_lines: list[str] = []
    current_count = 0
    start_line = 1
    lines = markdown.splitlines()

    def flush(end_line: int) -> None:
        nonlocal current_lines, current_count, start_line
        if current_count > max_chars:
            snippet = "".join(current_lines)[:40]
            # 需要的“视觉中断次数”应保证切分后每段都不超过 max_chars。
            # 对于长度 n，最少中断次数 = ceil(n / max_chars) - 1 = floor((n - 1) / max_chars)。
            required_breaks = (current_count - 1) // max_chars
            blocks.append(
                {
                    "start_line": start_line,
                    "end_line": end_line,
                    "char_count": current_count,
                    "snippet": snippet,
                    "required_breaks": required_breaks,
                }
            )
        current_lines = []
        current_count = 0
        start_line = end_line + 1

    for line_number, raw_line in enumerate(lines, start=1):
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

    flush(len(lines))
    return blocks


def build_plan(markdown_path: Path, max_chars: int) -> dict[str, Any]:
    markdown = markdown_path.read_text(encoding="utf-8")
    blocks = scan_long_plain_text_blocks(markdown, max_chars=max_chars)
    required_body_images = sum(int(block.get("required_breaks", 0)) for block in blocks)
    return {
        "count_method": "count_text_units: 移除所有空白字符后统计字符数（含中文、英文、数字、标点）",
        "rule_max_chars": max_chars,
        "required_body_images": required_body_images,
        "long_plain_text_blocks": blocks,
    }


def load_density_max_chars(planning_dir: Path) -> int | None:
    config_path = planning_dir / DENSITY_CONFIG_FILE
    if not config_path.exists():
        return None
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    value = data.get("max_chars_per_break")
    if isinstance(value, int) and value > 0:
        return value
    return None


def render_plan_markdown(plan: dict[str, Any]) -> str:
    lines = [
        "# 视觉中断清单",
        "",
        f"- 规则：连续纯文字区段不超过约 {plan['rule_max_chars']} 中文字",
        f"- 检测到超限区段：{len(plan['long_plain_text_blocks'])} 处",
        f"- 正文最少配图建议：{plan['required_body_images']} 张",
        "",
        "## 超限区段",
    ]
    if not plan["long_plain_text_blocks"]:
        lines.append("- 未检测到超限区段。")
        lines.append("")
        return "\n".join(lines)

    for idx, block in enumerate(plan["long_plain_text_blocks"], start=1):
        lines.append(
            f"- 区段 {idx}：第 {block['start_line']}-{block['end_line']} 行，约 {block['char_count']} 字，建议至少插入 {block['required_breaks']} 次视觉中断。"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="生成视觉中断统计清单（机器统计）")
    parser.add_argument("--markdown-path", required=True, help="整理稿路径")
    parser.add_argument("--planning-dir", required=True, help="02-规划目录")
    parser.add_argument("--max-chars", type=int, default=None, help="连续纯文字上限；如未传入，则优先读取 02-规划/配图密度配置.json")
    args = parser.parse_args()

    markdown_path = Path(args.markdown_path)
    planning_dir = Path(args.planning_dir)
    planning_dir.mkdir(parents=True, exist_ok=True)

    max_chars = args.max_chars
    if max_chars is None:
        max_chars = load_density_max_chars(planning_dir) or 300

    plan = build_plan(markdown_path=markdown_path, max_chars=max_chars)
    md_path = planning_dir / "视觉中断清单.md"
    json_path = planning_dir / "视觉中断清单.json"

    md_path.write_text(render_plan_markdown(plan), encoding="utf-8")
    json_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")

    result = {
        "markdown_file": str(md_path),
        "json_file": str(json_path),
        "required_body_images": plan["required_body_images"],
        "long_block_count": len(plan["long_plain_text_blocks"]),
        "max_chars_per_break": max_chars,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
