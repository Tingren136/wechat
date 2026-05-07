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


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def save_state(state_path: Path, state: dict[str, Any]) -> dict[str, Any]:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    return state


def load_state(state_path: Path) -> dict[str, Any]:
    return json.loads(state_path.read_text(encoding="utf-8"))


def ensure_artifact_defaults(state_path: Path, artifacts: dict[str, str]) -> dict[str, str]:
    normalized = dict(artifacts)
    planning_dir = state_path.parent
    if "approval_dir" not in normalized:
        normalized["approval_dir"] = str(planning_dir / "人工确认")
    return normalized


def approval_receipt_path(state: dict[str, Any]) -> Path:
    approval_dir = Path(state["artifacts"]["approval_dir"])
    approval_dir.mkdir(parents=True, exist_ok=True)
    filename = APPROVAL_FILE_LABELS[state["current_stage_id"]]
    return approval_dir / filename


def initialize_state(state_path: Path, title: str, artifacts: dict[str, str]) -> dict[str, Any]:
    first_stage = STAGES[0]
    normalized_artifacts = ensure_artifact_defaults(state_path, artifacts)
    state = {
        "title": title,
        "status": "waiting_confirmation",
        "current_stage_index": 0,
        "current_stage_id": first_stage["id"],
        "current_stage_label": first_stage["label"],
        "stages": STAGES,
        "selected_theme": "",
        "artifacts": normalized_artifacts,
        "history": [],
        "last_approval": {},
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


def record_stage_approval(state_path: Path, note: str) -> dict[str, Any]:
    state = load_state(state_path)
    receipt_path = approval_receipt_path(state)
    approved_at = now_iso()
    receipt = {
        "stage_id": state["current_stage_id"],
        "stage_label": state["current_stage_label"],
        "approved_at": approved_at,
        "note": note,
        "status": "approved",
    }
    receipt_text = (
        f"阶段: {receipt['stage_id']}\n"
        f"标签: {receipt['stage_label']}\n"
        f"状态: 已确认\n"
        f"时间: {receipt['approved_at']}\n"
        f"说明: {receipt['note']}\n"
    )
    receipt_path.write_text(receipt_text, encoding="utf-8")
    state["last_approval"] = {
        **receipt,
        "receipt_file": str(receipt_path),
    }
    state["updated_at"] = approved_at
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

    approval_parser = subparsers.add_parser("record-approval", help="记录当前阶段人工确认")
    approval_parser.add_argument("--state-path", required=True)
    approval_parser.add_argument("--note", required=True)

    args = parser.parse_args()
    state_path = Path(args.state_path)

    if args.command == "init":
        artifacts = json.loads(args.artifacts_json)
        result = initialize_state(state_path=state_path, title=args.title, artifacts=artifacts)
    elif args.command == "advance":
        result = advance_stage(state_path=state_path, note=args.note)
    elif args.command == "record-approval":
        result = record_stage_approval(state_path=state_path, note=args.note)
    else:
        result = set_selected_theme(state_path=state_path, theme_name=args.theme)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
