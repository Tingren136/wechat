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
        "outputs": ["01-原稿/02-润色稿.md", "02-规划/人工确认/01-润色完成后确认.txt"],
        "checks": ["作者固定为栗子智培", "不插入签名图", "不额外追加单独作者行"],
        "next_steps": [
            "使用 khazix-writer 基于 `01-原稿/01-草稿.md` 产出润色稿。",
            "把润色结果写入 `01-原稿/02-润色稿.md`，并检查固定署名与固定结尾。",
            "先把润色稿展示给用户，得到明确同意后，再记录人工确认回执。",
            "完成后再执行 confirm 推进到 Markdown 整理阶段。",
        ],
    },
    "markdown_review": {
        "recommended_skill": "baoyu-format-markdown",
        "goal": "把润色稿整理为结构清晰的 Markdown。",
        "inputs": ["01-原稿/02-润色稿.md"],
        "outputs": ["01-原稿/03-整理稿.md", "02-规划/人工确认/02-Markdown整理后确认.txt"],
        "checks": ["标题与 frontmatter 完整", "结构清晰", "不改写核心内容"],
        "next_steps": [
            "使用 baoyu-format-markdown 整理 `01-原稿/02-润色稿.md`。",
            "把结果落到 `01-原稿/03-整理稿.md`，确认结构清晰且不改写核心内容。",
            "先把整理稿展示给用户，得到明确同意后，再记录人工确认回执。",
            "完成后再执行 confirm 进入配图数量确认阶段。",
        ],
    },
    "image_count_review": {
        "recommended_skill": "baoyu-article-illustrator",
        "goal": "先确认本篇文章适合几张图，并考虑 300 字视觉中断规则。",
        "inputs": ["01-原稿/03-整理稿.md"],
        "outputs": ["02-规划/配图数量确认.txt", "02-规划/视觉中断清单.md", "02-规划/视觉中断清单.json", "02-规划/人工确认/03-配图数量确认.txt"],
        "checks": ["已确认图片数量", "已列出所有超过 300 字的长段并规划打断方式"],
        "next_steps": [
            "先运行机器统计脚本，自动生成 `02-规划/视觉中断清单.md` 和 `02-规划/视觉中断清单.json`。",
            "以机器统计结果作为正文最少配图下限，再结合 baoyu-article-illustrator 的结构建议确认图片数量。",
            "把确认结果写入 `02-规划/配图数量确认.txt`。",
            "先把配图数量方案展示给用户，得到明确同意后，再记录人工确认回执。",
            "完成后再执行 confirm 进入配图规划阶段。",
        ],
    },
    "illustration_plan_review": {
        "recommended_skill": "baoyu-article-illustrator",
        "goal": "生成配图规划、outline 和 prompt 打包结果。",
        "inputs": ["01-原稿/03-整理稿.md", "02-规划/配图数量确认.txt", "02-规划/视觉中断清单.md", "02-规划/视觉中断清单.json"],
        "outputs": ["02-规划/outline.md", "02-规划/batch.json", "03-提示词/草稿/", "02-规划/人工确认/04-配图规划完成后确认.txt"],
        "checks": ["图位覆盖视觉中断清单", "足够打断长文本", "提示词已归档"],
        "next_steps": [
            "使用 baoyu-article-illustrator 结合整理稿、图片数量确认和视觉中断清单做图位规划。",
            "生成 `02-规划/outline.md`、`02-规划/batch.json` 和 `03-提示词/草稿/` 下的 prompt 文件。",
            "先把图位规划和 prompt 方案展示给用户，得到明确同意后，再记录人工确认回执。",
            "确认图位能打断长文本后，再执行 confirm 进入图片生成阶段。",
        ],
    },
    "image_generation_review": {
        "recommended_skill": "baoyu-imagine",
        "goal": "按确认后的提示词生成正文配图。",
        "inputs": ["03-提示词/定稿/"],
        "outputs": ["04-素材/正文配图/", "02-规划/人工确认/05-图片生成前确认.txt"],
        "checks": ["默认 4:3 横版", "风格一致", "图片进入文章目录"],
        "next_steps": [
            "确认 `03-提示词/定稿/` 下的 prompt 已定稿。",
            "使用 baoyu-imagine 按 4:3 横版生成正文图，并保存到 `04-素材/正文配图/`。",
            "先把待生成方案或已生成图片展示给用户，得到明确同意后，再记录人工确认回执。",
            "完成后再执行 confirm 进入插图回正文阶段。",
        ],
    },
    "image_insert_review": {
        "recommended_skill": "wechat-article-workflow",
        "goal": "把图片插回正文，并检查 300 字视觉中断规则。",
        "inputs": ["01-原稿/03-整理稿.md", "04-素材/正文配图/"],
        "outputs": ["01-原稿/04-配图稿.md", "02-规划/人工确认/06-插图回正文后确认.txt"],
        "checks": ["长段纯文字已打断", "图位与图注合理"],
        "next_steps": [
            "把 `04-素材/正文配图/` 下的图片插回 `01-原稿/03-整理稿.md`。",
            "输出 `01-原稿/04-配图稿.md`，并确保连续纯文字区段不超过约 300 字。",
            "先把配图稿展示给用户，得到明确同意后，再记录人工确认回执。",
            "先运行 status 看校验结果，再执行 confirm 进入排版阶段。",
        ],
    },
    "layout_review": {
        "recommended_skill": "wechat-article-workflow",
        "goal": "导出 4 套预览版和 4 套发布版 HTML。",
        "inputs": ["01-原稿/04-配图稿.md"],
        "outputs": ["05-排版/预览版/", "05-排版/发布版/", "02-规划/人工确认/07-四套排版产出后确认.txt"],
        "checks": ["四套预览齐全", "四套发布版齐全", "只允许手动选主题"],
        "next_steps": [
            "使用 workflow_bundle 或 refresh-layouts 重新导出 4 套预览版和发布版 HTML。",
            "在 `05-排版/预览版/` 手动比较四套主题效果。",
            "先把选版结果展示给用户，得到明确同意后，再记录人工确认回执。",
            "完成后选定主题，再执行 confirm 进入草稿箱发布前检查阶段。",
        ],
    },
    "draft_publish_review": {
        "recommended_skill": "wechat-draft-publisher",
        "goal": "检查已选主题的发布态 HTML，确认后再进入公众号草稿箱。",
        "inputs": ["05-排版/发布版/", "02-规划/发布检查清单.md", "06-发布/已选主题.txt"],
        "outputs": ["06-发布/草稿箱结果.md", "02-规划/人工确认/08-草稿箱投递前确认.txt"],
        "checks": ["只使用发布态 HTML", "发布检查清单已核对", "人工确认后才投递"],
        "next_steps": [
            "先把最终主题写入 `06-发布/已选主题.txt`。",
            "核对 `02-规划/发布检查清单.md` 和对应发布版 HTML。",
            "先把待发布内容展示给用户，得到明确同意后，再记录人工确认回执。",
            "确认无误后再调用 wechat-draft-publisher 或 confirm 完成最后一跳。",
        ],
    },
}


def load_state_module():
    module_path = Path(__file__).resolve().parent / "workflow_state_manager.py"
    spec = importlib.util.spec_from_file_location("workflow_state_manager", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def derive_article_dir(state: dict[str, Any]) -> Path | None:
    draft_path = state.get("artifacts", {}).get("draft")
    if not draft_path:
        return None
    return Path(draft_path).parents[1]


def build_suggested_commands(stage_id: str, state_path: Path, state: dict[str, Any]) -> list[str]:
    article_dir = derive_article_dir(state)
    commands: list[str] = []
    if article_dir is None:
        return commands

    source_dir = article_dir / "01-原稿"
    planning_dir = article_dir / "02-规划"
    prompts_dir = article_dir / "03-提示词"
    state_path_str = str(state_path)

    if stage_id == "polish_review":
        commands.append(f'打开 `{source_dir / "01-草稿.md"}` 并使用 `khazix-writer` 完成润色。')
        commands.append(f'py .\\skills\\wechat-article-workflow\\scripts\\workflow_executor.py status --state-path "{state_path_str}"')
        commands.append(f'py .\\skills\\wechat-article-workflow\\scripts\\workflow_executor.py record-approval --state-path "{state_path_str}" --note "这里写用户确认原话"')
    elif stage_id == "markdown_review":
        commands.append(f'powershell -File C:\\Users\\86156\\.codex\\skills\\baoyu-format-markdown\\scripts\\run-formatter.ps1 "{source_dir / "02-润色稿.md"}"')
        commands.append(f'py .\\skills\\wechat-article-workflow\\scripts\\workflow_executor.py status --state-path "{state_path_str}"')
        commands.append(f'py .\\skills\\wechat-article-workflow\\scripts\\workflow_executor.py record-approval --state-path "{state_path_str}" --note "这里写用户确认原话"')
    elif stage_id == "image_count_review":
        commands.append(
            f'py .\\skills\\wechat-article-workflow\\scripts\\workflow_visual_break_planner.py --markdown-path "{source_dir / "03-整理稿.md"}" --planning-dir "{planning_dir}" --max-chars 300'
        )
        commands.append(f'再在 `{planning_dir / "配图数量确认.txt"}` 写入建议图片数量（不得小于 `视觉中断清单.json` 的 required_body_images）。')
        commands.append(f'py .\\skills\\wechat-article-workflow\\scripts\\workflow_executor.py status --state-path "{state_path_str}"')
        commands.append(f'py .\\skills\\wechat-article-workflow\\scripts\\workflow_executor.py record-approval --state-path "{state_path_str}" --note "这里写用户确认原话"')
    elif stage_id == "illustration_plan_review":
        commands.append(f'根据 `{planning_dir / "视觉中断清单.md"}` 生成覆盖这些区段的图位规划。')
        commands.append(f'把 outline 与 batch 产物写入 `{planning_dir}`，把 prompt 草稿写入 `{prompts_dir / "草稿"}`。')
        commands.append(f'py .\\skills\\wechat-article-workflow\\scripts\\workflow_executor.py status --state-path "{state_path_str}"')
        commands.append(f'py .\\skills\\wechat-article-workflow\\scripts\\workflow_executor.py record-approval --state-path "{state_path_str}" --note "这里写用户确认原话"')
    elif stage_id == "image_generation_review":
        commands.append(f'使用 `baoyu-imagine` 按 4:3 生成图片并保存到 `{article_dir / "04-素材" / "正文配图"}`。')
        commands.append(f'py .\\skills\\wechat-article-workflow\\scripts\\workflow_executor.py status --state-path "{state_path_str}"')
        commands.append(f'py .\\skills\\wechat-article-workflow\\scripts\\workflow_executor.py record-approval --state-path "{state_path_str}" --note "这里写用户确认原话"')
    elif stage_id == "image_insert_review":
        commands.append(f'编辑 `{source_dir / "04-配图稿.md"}`，把图片插回正文并控制每段纯文字不超过约 300 字。')
        commands.append(f'py .\\skills\\wechat-article-workflow\\scripts\\workflow_executor.py status --state-path "{state_path_str}"')
        commands.append(f'py .\\skills\\wechat-article-workflow\\scripts\\workflow_executor.py record-approval --state-path "{state_path_str}" --note "这里写用户确认原话"')
    elif stage_id == "layout_review":
        commands.append(f'py .\\skills\\wechat-article-workflow\\scripts\\workflow_executor.py refresh-layouts --state-path "{state_path_str}"')
        commands.append(f'打开 `{article_dir / "05-排版" / "预览版"}` 比较四套主题后，再设置最终主题。')
        commands.append(f'py .\\skills\\wechat-article-workflow\\scripts\\workflow_executor.py record-approval --state-path "{state_path_str}" --note "这里写用户确认原话"')
    elif stage_id == "draft_publish_review":
        commands.append(f'py .\\skills\\wechat-article-workflow\\scripts\\workflow_executor.py set-theme --state-path "{state_path_str}" --theme "Claude"')
        commands.append(f'核对 `{planning_dir / "发布检查清单.md"}` 与 `{article_dir / "05-排版" / "发布版"}` 后再进入发布 skill。')
        commands.append(f'py .\\skills\\wechat-article-workflow\\scripts\\workflow_executor.py record-approval --state-path "{state_path_str}" --note "这里写用户确认原话"')
    return commands


def build_gate_requirements(state_path: Path) -> list[str]:
    state_path_str = str(state_path)
    return [
        "只允许处理当前阶段，不允许凭记忆直接跳到下一个子 skill。",
        f"用户明确同意当前阶段结果后，必须先记录人工确认：`py .\\skills\\wechat-article-workflow\\scripts\\workflow_executor.py record-approval --state-path \"{state_path_str}\" --note \"这里写用户确认原话\"`。",
        f"当前阶段产物写完后，必须重新运行 `status`：`py .\\skills\\wechat-article-workflow\\scripts\\workflow_executor.py status --state-path \"{state_path_str}\"`。",
        "只有当 `validation.status` 等于 `ok` 时，才能继续执行 `confirm`。",
        f"推进阶段前，必须显式运行 `confirm`：`py .\\skills\\wechat-article-workflow\\scripts\\workflow_executor.py confirm --state-path \"{state_path_str}\"`。",
        "如果 `validation.status` 等于 `blocked`，必须先修复 `阶段检查报告.md` 里的 blocker，再重新运行 `status`。",
    ]


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
    if stage_meta.get("next_steps"):
        lines.append("")
        lines.append("## 下一步操作")
        lines.extend([f"- {item}" for item in stage_meta["next_steps"]])
    if stage_meta.get("suggested_commands"):
        lines.append("")
        lines.append("## 建议命令")
        lines.extend([f"- `{item}`" for item in stage_meta["suggested_commands"]])
    if stage_meta.get("gate_requirements"):
        lines.append("")
        lines.append("## 强制门协议")
        lines.extend([f"- {item}" for item in stage_meta["gate_requirements"]])
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
    stage_meta = {
        **stage_meta,
        "suggested_commands": build_suggested_commands(stage_id, state_path, state),
        "gate_requirements": build_gate_requirements(state_path),
    }
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
        "next_steps": stage_meta.get("next_steps", []),
        "suggested_commands": stage_meta.get("suggested_commands", []),
        "gate_requirements": stage_meta.get("gate_requirements", []),
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
