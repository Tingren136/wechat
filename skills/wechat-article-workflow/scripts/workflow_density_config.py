from __future__ import annotations

import argparse
import json
from pathlib import Path


DENSITY_PRESETS = {
    "high": 200,
    "medium_high": 300,
    "medium": 400,
    "low": 500,
}


def resolve_max_chars(profile: str, custom_max_chars: int | None) -> int:
    if profile == "custom":
        if custom_max_chars is None or custom_max_chars <= 0:
            raise ValueError("custom 模式必须提供正整数 --custom-max-chars。")
        return custom_max_chars
    return DENSITY_PRESETS[profile]


def main() -> None:
    parser = argparse.ArgumentParser(description="写入配图密度配置（每多少字至少一次视觉中断）")
    parser.add_argument("--planning-dir", required=True, help="02-规划目录")
    parser.add_argument("--profile", choices=["high", "medium_high", "medium", "low", "custom"], required=True)
    parser.add_argument("--custom-max-chars", type=int, default=None, help="仅 custom 模式下必填")
    args = parser.parse_args()

    planning_dir = Path(args.planning_dir)
    planning_dir.mkdir(parents=True, exist_ok=True)
    max_chars = resolve_max_chars(args.profile, args.custom_max_chars)

    config = {
        "density_profile": args.profile,
        "max_chars_per_break": max_chars,
        "count_tool": "workflow_visual_break_planner.py",
        "count_method": "count_text_units: 移除所有空白字符后统计字符数（含中文、英文、数字、标点）",
    }
    config_path = planning_dir / "配图密度配置.json"
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({"config_file": str(config_path), **config}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
