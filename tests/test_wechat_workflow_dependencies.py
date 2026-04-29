import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "skills" / "wechat-article-workflow" / "scripts" / "ensure_dependencies.py"


def load_module():
    spec = importlib.util.spec_from_file_location("ensure_dependencies", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class WorkflowDependenciesTests(unittest.TestCase):
    def test_grouped_missing_dependencies_reports_missing_skills_by_repo(self):
        module = load_module()
        manifest = {
            "repositories": [
                {"id": "repo-a", "url": "https://example.com/a", "skills": ["skill-a", "skill-b"]},
                {"id": "repo-b", "url": "https://example.com/b", "skills": ["skill-c"]},
            ]
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "skill-a").mkdir()

            with patch.object(module, "load_manifest", return_value=manifest), patch.object(module, "skills_root", return_value=root):
                missing = module.grouped_missing_dependencies()

        self.assertEqual(len(missing), 2)
        self.assertEqual(missing[0]["id"], "repo-a")
        self.assertEqual(missing[0]["missing_skills"], ["skill-b"])
        self.assertEqual(missing[1]["id"], "repo-b")
        self.assertEqual(missing[1]["missing_skills"], ["skill-c"])


if __name__ == "__main__":
    unittest.main()
