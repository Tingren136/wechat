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


def build_gate_packet(state_path: Path, validation: dict[str, Any]) -> dict[str, Any]:
    state_path_str = str(state_path)
    status_command = f'py .\\skills\\wechat-article-workflow\\scripts\\workflow_executor.py status --state-path "{state_path_str}"'
    confirm_command = f'py .\\skills\\wechat-article-workflow\\scripts\\workflow_executor.py confirm --state-path "{state_path_str}"'
    return {
        "must_only_operate_current_stage": True,
        "must_rerun_status_after_outputs": True,
        "must_fix_blockers_before_confirm": True,
        "must_confirm_explicitly_to_advance": True,
        "current_validation_status": validation["status"],
        "status_command": status_command,
        "confirm_command": confirm_command,
        "blocked_action": "如果 validation.status 为 blocked，先修复阶段检查报告中的 blocker，再重新运行 status。",
    }


def get_status(state_path: Path) -> dict[str, Any]:
    state_module = load_module("workflow_state_manager.py", "workflow_state_manager")
    stage_runner = load_module("workflow_stage_runner.py", "workflow_stage_runner")
    validator = load_module("workflow_validator.py", "workflow_validator")
    state = state_module.load_state(state_path)
    packet = stage_runner.generate_stage_packet(state_path)
    validation = validator.validate_stage(state_path)
    gate = build_gate_packet(state_path, validation)
    return {"state": state, "packet": packet, "validation": validation, "gate": gate}


def confirm_current_stage(state_path: Path, note: str = "", allow_issues: bool = False) -> dict[str, Any]:
    state_module = load_module("workflow_state_manager.py", "workflow_state_manager")
    stage_runner = load_module("workflow_stage_runner.py", "workflow_stage_runner")
    validator = load_module("workflow_validator.py", "workflow_validator")
    validation = validator.validate_stage(state_path)
    if validation["status"] == "blocked" and not allow_issues:
        raise RuntimeError("当前阶段仍有未处理的阻塞项，请先查看阶段检查报告或显式允许带问题推进。")
    state = state_module.advance_stage(state_path, note=note)
    packet = stage_runner.generate_stage_packet(state_path)
    return {"state": state, "packet": packet, "validation": validation}


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
    confirm_parser.add_argument("--allow-issues", action="store_true")

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
        result = confirm_current_stage(state_path, note=args.note, allow_issues=args.allow_issues)
    elif args.command == "set-theme":
        result = select_theme(state_path, theme_name=args.theme)
    else:
        result = refresh_layout_outputs(state_path)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
