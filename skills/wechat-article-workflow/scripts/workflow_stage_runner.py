from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any


STAGE_DEFINITIONS = {
    "polish_review": {
        "recommended_skill": "khazix-writer",
        "goal": "基于原稿产出润色稿，并检查固定署名与固定结尾规则。",
        "inputs": ["01-原稿/01-草稿.md"],
        "outputs": ["01-原稿/02-润色稿.md"],
        "checks": ["作者固定为栗子智培", "不插入签名图", "不额外追加单独作者行"],
    },
    "markdown_review": {
        "recommended_skill": "baoyu-format-markdown",
        "goal": "把润色稿整理为结构清晰的 Markdown。",
        "inputs": ["01-原稿/02-润色稿.md"],
        "outputs": ["01-原稿/03-整理稿.md"],
        "checks": ["标题与 frontmatter 完整", "结构清晰", "不改写核心内容"],
    },
    "image_count_review": {
        "recommended_skill": "baoyu-article-illustrator",
        "goal": "先确认本篇文章适合几张图，并考虑 300 字视觉中断规则。",
        "inputs": ["01-原稿/03-整理稿.md"],
        "outputs": ["02-规划/配图数量确认.txt"],
        "checks": ["已确认图片数量", "考虑长段纯文字打断"],
    },
    "illustration_plan_review": {
        "recommended_skill": "baoyu-article-illustrator",
        "goal": "生成配图规划、outline 和 prompt 打包结果。",
        "inputs": ["01-原稿/03-整理稿.md", "02-规划/配图数量确认.txt"],
        "outputs": ["02-规划/outline.md", "02-规划/batch.json", "03-提示词/草稿/"],
        "checks": ["图位自然", "足够打断长文本", "提示词已归档"],
    },
    "image_generation_review": {
        "recommended_skill": "baoyu-imagine",
        "goal": "按确认后的提示词生成正文配图。",
        "inputs": ["03-提示词/定稿/"],
        "outputs": ["04-素材/正文配图/"],
        "checks": ["默认 4:3 横版", "风格一致", "图片进入文章目录"],
    },
    "image_insert_review": {
        "recommended_skill": "wechat-article-workflow",
        "goal": "把图片插回正文，并检查 300 字视觉中断规则。",
        "inputs": ["01-原稿/03-整理稿.md", "04-素材/正文配图/"],
        "outputs": ["01-原稿/04-配图稿.md"],
        "checks": ["长段纯文字已打断", "图位与图注合理"],
    },
    "layout_review": {
        "recommended_skill": "wechat-article-workflow",
        "goal": "导出 4 套预览版和 4 套发布版 HTML。",
        "inputs": ["01-原稿/04-配图稿.md"],
        "outputs": ["05-排版/预览版/", "05-排版/发布版/"],
        "checks": ["四套预览齐全", "四套发布版齐全", "只允许手动选主题"],
    },
    "draft_publish_review": {
        "recommended_skill": "wechat-draft-publisher",
        "goal": "检查已选主题的发布态 HTML，确认后再进入公众号草稿箱。",
        "inputs": ["05-排版/发布版/", "02-规划/发布检查清单.md", "06-发布/已选主题.txt"],
        "outputs": ["06-发布/草稿箱结果.md"],
        "checks": ["只使用发布态 HTML", "发布检查清单已核对", "人工确认后才投递"],
    },
}


def load_state_module():
    module_path = Path(__file__).resolve().parent / "workflow_state_manager.py"
    spec = importlib.util.spec_from_file_location("workflow_state_manager", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def stage_instruction_markdown(state: dict[str, Any], stage_meta: dict[str, Any]) -> str:
    lines = [
        f"# 当前阶段说明",
        "",
        f"- 阶段：{state['current_stage_label']}",
        f"- 推荐 skill：`{stage_meta['recommended_skill']}`",
        f"- 目标：{stage_meta['goal']}",
        "",
        "## 输入",
    ]
    lines.extend([f"- `{item}`" for item in stage_meta["inputs"]])
    lines.append("")
    lines.append("## 预期输出")
    lines.extend([f"- `{item}`" for item in stage_meta["outputs"]])
    lines.append("")
    lines.append("## 检查项")
    lines.extend([f"- {item}" for item in stage_meta["checks"]])
    lines.append("")
    lines.append("## 说明")
    lines.append("- 确认后才能进入下一阶段。")
    lines.append("- 不允许跳过该阶段对应子 skill 的原始确认流程。")
    return "\n".join(lines) + "\n"


def generate_stage_packet(state_path: Path) -> dict[str, Any]:
    state_module = load_state_module()
    state = state_module.load_state(state_path)
    stage_id = state["current_stage_id"]
    if stage_id == "completed":
        packet = {
            "stage_id": "completed",
            "stage_label": "已完成",
            "recommended_skill": "",
            "goal": "全部阶段已完成。",
        }
        return packet

    stage_meta = STAGE_DEFINITIONS[stage_id]
    planning_dir = state_path.parent
    instruction_path = planning_dir / "当前阶段说明.md"
    instruction_path.write_text(stage_instruction_markdown(state, stage_meta), encoding="utf-8")

    packet = {
        "stage_id": stage_id,
        "stage_label": state["current_stage_label"],
        "recommended_skill": stage_meta["recommended_skill"],
        "goal": stage_meta["goal"],
        "inputs": stage_meta["inputs"],
        "outputs": stage_meta["outputs"],
        "checks": stage_meta["checks"],
        "instruction_file": str(instruction_path),
    }
    return packet


def main() -> None:
    parser = argparse.ArgumentParser(description="生成当前阶段执行说明")
    parser.add_argument("--state-path", required=True, help="工作流状态文件路径")
    args = parser.parse_args()

    packet = generate_stage_packet(Path(args.state_path))
    print(json.dumps(packet, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
