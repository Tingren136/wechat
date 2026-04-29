from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


STAGES = [
    {"id": "polish_review", "label": "润色完成后确认"},
    {"id": "markdown_review", "label": "Markdown 整理后确认"},
    {"id": "image_count_review", "label": "配图数量确认"},
    {"id": "illustration_plan_review", "label": "配图规划完成后确认"},
    {"id": "image_generation_review", "label": "图片生成前确认"},
    {"id": "image_insert_review", "label": "插图回正文后确认"},
    {"id": "layout_review", "label": "四套排版产出后确认"},
    {"id": "draft_publish_review", "label": "草稿箱投递前确认"},
]


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def save_state(state_path: Path, state: dict[str, Any]) -> dict[str, Any]:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    return state


def load_state(state_path: Path) -> dict[str, Any]:
    return json.loads(state_path.read_text(encoding="utf-8"))


def initialize_state(state_path: Path, title: str, artifacts: dict[str, str]) -> dict[str, Any]:
    first_stage = STAGES[0]
    state = {
        "title": title,
        "status": "waiting_confirmation",
        "current_stage_index": 0,
        "current_stage_id": first_stage["id"],
        "current_stage_label": first_stage["label"],
        "stages": STAGES,
        "selected_theme": "",
        "artifacts": artifacts,
        "history": [],
        "updated_at": now_iso(),
    }
    return save_state(state_path, state)


def advance_stage(state_path: Path, note: str = "") -> dict[str, Any]:
    state = load_state(state_path)
    if state["status"] == "completed":
        return state

    history_entry = {
        "stage_id": state["current_stage_id"],
        "stage_label": state["current_stage_label"],
        "confirmed_at": now_iso(),
        "note": note,
    }
    state.setdefault("history", []).append(history_entry)

    next_index = state["current_stage_index"] + 1
    if next_index >= len(state["stages"]):
        state["status"] = "completed"
        state["current_stage_index"] = len(state["stages"])
        state["current_stage_id"] = "completed"
        state["current_stage_label"] = "已完成"
        state["updated_at"] = now_iso()
        return save_state(state_path, state)

    next_stage = state["stages"][next_index]
    state["current_stage_index"] = next_index
    state["current_stage_id"] = next_stage["id"]
    state["current_stage_label"] = next_stage["label"]
    state["status"] = "waiting_confirmation"
    state["updated_at"] = now_iso()
    return save_state(state_path, state)


def set_selected_theme(state_path: Path, theme_name: str) -> dict[str, Any]:
    state = load_state(state_path)
    state["selected_theme"] = theme_name
    selected_theme_path = state.get("artifacts", {}).get("selected_theme")
    if selected_theme_path:
        Path(selected_theme_path).write_text(theme_name, encoding="utf-8")
    state["updated_at"] = now_iso()
    return save_state(state_path, state)


def main() -> None:
    parser = argparse.ArgumentParser(description="管理公众号文章工作流状态")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="初始化状态文件")
    init_parser.add_argument("--state-path", required=True)
    init_parser.add_argument("--title", required=True)
    init_parser.add_argument("--artifacts-json", required=True)

    advance_parser = subparsers.add_parser("advance", help="推进到下一确认阶段")
    advance_parser.add_argument("--state-path", required=True)
    advance_parser.add_argument("--note", default="")

    theme_parser = subparsers.add_parser("set-theme", help="记录已选主题")
    theme_parser.add_argument("--state-path", required=True)
    theme_parser.add_argument("--theme", required=True)

    args = parser.parse_args()
    state_path = Path(args.state_path)

    if args.command == "init":
        artifacts = json.loads(args.artifacts_json)
        result = initialize_state(state_path=state_path, title=args.title, artifacts=artifacts)
    elif args.command == "advance":
        result = advance_stage(state_path=state_path, note=args.note)
    else:
        result = set_selected_theme(state_path=state_path, theme_name=args.theme)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
