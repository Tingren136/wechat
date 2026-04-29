from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


def load_manifest() -> dict[str, Any]:
    manifest_path = Path(__file__).resolve().parents[1] / "references" / "dependencies.json"
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def skills_root() -> Path:
    return Path.home() / ".codex" / "skills"


def skill_exists(name: str) -> bool:
    return (skills_root() / name).exists()


def grouped_missing_dependencies() -> list[dict[str, Any]]:
    manifest = load_manifest()
    missing_groups: list[dict[str, Any]] = []
    for repo in manifest["repositories"]:
        missing = [skill for skill in repo["skills"] if not skill_exists(skill)]
        if missing:
            missing_groups.append(
                {
                    "id": repo["id"],
                    "url": repo["url"],
                    "missing_skills": missing,
                }
            )
    return missing_groups


def install_repo(url: str) -> tuple[bool, str]:
    npx = shutil.which("npx.cmd") or shutil.which("npx")
    if npx is None:
        return False, "未找到 npx，无法自动安装依赖 skill。"

    command = [npx, "skills", "add", url, "-g", "-y"]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "未知安装失败"
        return False, message
    return True, result.stdout.strip() or "installed"


def ensure_dependencies(auto_install: bool = True) -> dict[str, Any]:
    before = grouped_missing_dependencies()
    attempted: list[dict[str, Any]] = []

    if auto_install:
        for repo in before:
            success, message = install_repo(repo["url"])
            attempted.append(
                {
                    "id": repo["id"],
                    "url": repo["url"],
                    "missing_skills": repo["missing_skills"],
                    "success": success,
                    "message": message,
                }
            )

    after = grouped_missing_dependencies()
    return {
        "ok": len(after) == 0,
        "missing_before": before,
        "attempted": attempted,
        "missing_after": after,
    }


def main() -> None:
    result = ensure_dependencies(auto_install=True)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
