from __future__ import annotations

import shutil
from pathlib import Path
import subprocess


def copy_tree(source: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(
        source,
        target,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )


def install_local_skill(target_root: Path | None = None) -> Path:
    script_path = Path(__file__).resolve()
    skill_dir = script_path.parents[1]
    repo_root = script_path.parents[3]
    exporter_path = repo_root / "scripts" / "claude_publish_export.py"

    if target_root is None:
        target_root = Path.home() / ".codex" / "skills"

    target_skill_dir = target_root / skill_dir.name
    copy_tree(skill_dir, target_skill_dir)

    target_scripts_dir = target_skill_dir / "scripts"
    target_scripts_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(exporter_path, target_scripts_dir / "publish_export_standalone.py")
    _run_dependency_bootstrap(target_scripts_dir / "ensure_dependencies.py")
    return target_skill_dir


def _run_dependency_bootstrap(ensure_script: Path) -> None:
    try:
        subprocess.run(
            ["py", str(ensure_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except OSError:
        pass


def main() -> None:
    target = install_local_skill()
    print(target)


if __name__ == "__main__":
    main()
