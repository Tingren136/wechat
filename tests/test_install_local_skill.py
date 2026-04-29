import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "skills" / "wechat-article-workflow" / "scripts" / "install_local_skill.py"


def load_module():
    spec = importlib.util.spec_from_file_location("install_local_skill", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class InstallLocalSkillTests(unittest.TestCase):
    def test_install_local_skill_installs_publisher_skill_too(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            target_root = Path(temp_dir) / "skills"
            with patch.object(module, "_run_dependency_bootstrap", return_value=None):
                installed = module.install_local_skill(target_root=target_root)

            self.assertTrue(installed.exists())
            self.assertTrue((installed / "scripts" / "workflow_state_manager.py").exists())
            self.assertTrue((target_root / "wechat-draft-publisher").exists())
            self.assertTrue((target_root / "wechat-draft-publisher" / "SKILL.md").exists())


if __name__ == "__main__":
    unittest.main()
