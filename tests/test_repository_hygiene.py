import json
from pathlib import Path
import re
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

IGNORED_PARTS = {".git", ".venv"}
TEXT_SUFFIXES = {".ipynb", ".md", ".py", ".txt"}
DATA_SUFFIXES = {".csv", ".feather", ".parquet", ".pickle", ".pkl", ".tsv", ".xls", ".xlsx"}
LOCAL_PATH_PATTERNS = (
    re.compile("/" + "Users" + "/"),
    re.compile("/" + "home" + "/"),
    re.compile("/" + "athena" + "/"),
    re.compile(r"[A-Za-z]:\\" + "Users" + r"\\"),
)


def repository_files():
    return tuple(path for path in REPOSITORY_ROOT.rglob("*") if path.is_file() and not IGNORED_PARTS.intersection(path.parts))


class RepositoryHygieneTests(unittest.TestCase):
    def test_ignores_operating_system_and_interpreter_artifacts(self):
        ignore_rules = (REPOSITORY_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        for required_rule in (".DS_Store", "__pycache__/", "*.py[cod]", ".ipynb_checkpoints/"):
            with self.subTest(rule=required_rule):
                self.assertIn(required_rule, ignore_rules)

        rejected_names = {".DS_Store"}
        rejected_parts = {".ipynb_checkpoints"}
        rejected = [
            path.relative_to(REPOSITORY_ROOT).as_posix()
            for path in repository_files()
            if path.name in rejected_names or rejected_parts.intersection(path.parts)
        ]
        self.assertEqual(rejected, [])

    def test_excludes_patient_level_data_files(self):
        included = [path.relative_to(REPOSITORY_ROOT).as_posix() for path in repository_files() if path.suffix.lower() in DATA_SUFFIXES]
        self.assertEqual(included, [])

    def test_notebooks_have_no_saved_outputs_or_attachments(self):
        for path in REPOSITORY_ROOT.rglob("*.ipynb"):
            with self.subTest(notebook=path.relative_to(REPOSITORY_ROOT).as_posix()):
                notebook = json.loads(path.read_text(encoding="utf-8"))
                for cell in notebook.get("cells", []):
                    self.assertFalse(cell.get("outputs"))
                    self.assertFalse(cell.get("attachments"))
                    if cell.get("cell_type") == "code":
                        self.assertIsNone(cell.get("execution_count"))

    def test_source_files_do_not_contain_machine_specific_paths(self):
        matches = []
        for path in repository_files():
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            text = path.read_text(encoding="utf-8")
            for pattern in LOCAL_PATH_PATTERNS:
                if pattern.search(text):
                    matches.append((path.relative_to(REPOSITORY_ROOT).as_posix(), pattern.pattern))
        self.assertEqual(matches, [])


if __name__ == "__main__":
    unittest.main()
