from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any


def load_module(filename: str, module_name: str):
    module_path = Path(__file__).resolve().parent / filename
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _article_dir_from_state(state: dict[str, Any]) -> Path:
    draft_path = Path(state["artifacts"]["draft"])
    return draft_path.parents[1]


def get_status(state_path: Path) -> dict[str, Any]:
    state_module = load_module("workflow_state_manager.py", "workflow_state_manager")
    stage_runner = load_module("workflow_stage_runner.py", "workflow_stage_runner")
    state = state_module.load_state(state_path)
    packet = stage_runner.generate_stage_packet(state_path)
    return {"state": state, "packet": packet}


def confirm_current_stage(state_path: Path, note: str = "") -> dict[str, Any]:
    state_module = load_module("workflow_state_manager.py", "workflow_state_manager")
    stage_runner = load_module("workflow_stage_runner.py", "workflow_stage_runner")
    state = state_module.advance_stage(state_path, note=note)
    packet = stage_runner.generate_stage_packet(state_path)
    return {"state": state, "packet": packet}


def select_theme(state_path: Path, theme_name: str) -> dict[str, Any]:
    state_module = load_module("workflow_state_manager.py", "workflow_state_manager")
    stage_runner = load_module("workflow_stage_runner.py", "workflow_stage_runner")
    state = state_module.set_selected_theme(state_path, theme_name)
    packet = stage_runner.generate_stage_packet(state_path)
    return {"state": state, "packet": packet}


def refresh_layout_outputs(state_path: Path) -> dict[str, Any]:
    state_module = load_module("workflow_state_manager.py", "workflow_state_manager")
    bundle_module = load_module("workflow_bundle.py", "workflow_bundle")
    state = state_module.load_state(state_path)
    article_dir = _article_dir_from_state(state)
    with_images_path = Path(state["artifacts"]["with_images"])
    image_root = article_dir.parent
    result = bundle_module.export_article_bundle(with_images_path, image_root)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="公众号工作流执行器")
    subparsers = parser.add_subparsers(dest="command", required=True)

    status_parser = subparsers.add_parser("status", help="查看当前状态和阶段说明")
    status_parser.add_argument("--state-path", required=True)

    confirm_parser = subparsers.add_parser("confirm", help="确认当前阶段并推进")
    confirm_parser.add_argument("--state-path", required=True)
    confirm_parser.add_argument("--note", default="")

    theme_parser = subparsers.add_parser("set-theme", help="设置已选主题")
    theme_parser.add_argument("--state-path", required=True)
    theme_parser.add_argument("--theme", required=True)

    refresh_parser = subparsers.add_parser("refresh-layouts", help="按当前配图稿重导出排版")
    refresh_parser.add_argument("--state-path", required=True)

    args = parser.parse_args()
    state_path = Path(args.state_path)

    if args.command == "status":
        result = get_status(state_path)
    elif args.command == "confirm":
        result = confirm_current_stage(state_path, note=args.note)
    elif args.command == "set-theme":
        result = select_theme(state_path, theme_name=args.theme)
    else:
        result = refresh_layout_outputs(state_path)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
