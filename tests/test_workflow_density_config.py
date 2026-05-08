import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "skills" / "wechat-article-workflow" / "scripts" / "workflow_density_config.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class WorkflowDensityConfigTests(unittest.TestCase):
    def test_resolve_preset_and_custom(self):
        module = load_module(MODULE_PATH, "workflow_density_config")
        self.assertEqual(module.resolve_max_chars("high", None), 200)
        self.assertEqual(module.resolve_max_chars("medium_high", None), 300)
        self.assertEqual(module.resolve_max_chars("medium", None), 400)
        self.assertEqual(module.resolve_max_chars("low", None), 500)
        self.assertEqual(module.resolve_max_chars("custom", 260), 260)

    def test_custom_requires_positive_value(self):
        module = load_module(MODULE_PATH, "workflow_density_config")
        with self.assertRaises(ValueError):
            module.resolve_max_chars("custom", None)
        with self.assertRaises(ValueError):
            module.resolve_max_chars("custom", 0)


if __name__ == "__main__":
    unittest.main()
