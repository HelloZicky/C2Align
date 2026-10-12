import json
from pathlib import Path
import sys
import unittest

import numpy as np
import pandas as pd


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from c2align_feature_policy import (  # noqa: E402
    FORBIDDEN_EXACT_COLUMNS,
    assert_no_forbidden_features,
    audit_feature_selection,
    numeric_feature_matrix,
)


class FeaturePolicyTests(unittest.TestCase):
    def setUp(self):
        self.table = pd.DataFrame(
            {
                "subject_id": [1, 2, 3],
                "label_numerical": [0, 1, 0],
                "anchor_age": [65, 81, 72],
                "feat_symptom_is_warm_wet": [True, False, True],
                "mas_hf_conf": [20.0, 90.0, 40.0],
                "parallel_mas_hf_conf": [25.0, 85.0, 35.0],
                "candidate_code_positive": [0, 1, 0],
                "physician_1_label": [0, 1, 0],
                "physician_2_label": [0, 1, 0],
                "senior_expert_label": [0, 1, 0],
                "include_in_cohort": [True, True, True],
                "split": [0, 0, 1],
                "cv_fold": [0, 1, 2],
                "future_event_flag": [0, 1, 0],
                "unregistered_numeric": [999, 999, 999],
            }
        )
        self.allowlist = (
            "anchor_age",
            "feat_symptom_is_warm_wet",
            "mas_hf_conf",
            "parallel_mas_hf_conf",
        )

    def test_only_exact_allowlist_enters_matrix(self):
        matrix, columns = numeric_feature_matrix(
            self.table,
            self.allowlist,
            patient_col="subject_id",
            label_col="label_numerical",
        )
        self.assertEqual(columns, list(self.allowlist))
        self.assertEqual(list(matrix.columns), list(self.allowlist))
        self.assertNotIn("unregistered_numeric", matrix.columns)
        self.assertTrue(np.issubdtype(matrix.values.dtype, np.number))

    def test_forbidden_columns_do_not_change_allowed_matrix(self):
        clean_table = self.table.loc[:, self.allowlist].copy()
        clean_matrix, _ = numeric_feature_matrix(
            clean_table,
            self.allowlist,
            patient_col="subject_id",
            label_col="label_numerical",
        )
        contaminated_matrix, _ = numeric_feature_matrix(
            self.table,
            self.allowlist,
            patient_col="subject_id",
            label_col="label_numerical",
        )
        pd.testing.assert_frame_equal(clean_matrix, contaminated_matrix)

    def test_every_known_forbidden_column_is_rejected(self):
        for forbidden in sorted(FORBIDDEN_EXACT_COLUMNS):
            table = self.table.copy()
            if forbidden not in table.columns:
                table[forbidden] = 0
            with self.subTest(forbidden=forbidden):
                with self.assertRaises(ValueError):
                    numeric_feature_matrix(
                        table,
                        ("anchor_age", forbidden),
                        patient_col="subject_id",
                        label_col="label_numerical",
                    )

    def test_renamed_annotation_and_post_index_variants_are_rejected(self):
        variants = (
            "annotator_3_label",
            "adjudicated_diagnosis",
            "site_partition",
            "post_index_lab_value",
            "after_index_event_count",
            "future_event_flag",
        )
        for forbidden in variants:
            with self.subTest(forbidden=forbidden):
                with self.assertRaises(ValueError):
                    numeric_feature_matrix(
                        self.table,
                        ("anchor_age", forbidden),
                        patient_col="subject_id",
                        label_col="label_numerical",
                    )

    def test_audit_reports_blocked_and_ignored_numeric_columns(self):
        audit = audit_feature_selection(
            self.table,
            self.allowlist,
            patient_col="subject_id",
            label_col="label_numerical",
        )
        self.assertIn("candidate_code_positive", audit.blocked_present)
        self.assertIn("physician_1_label", audit.blocked_present)
        self.assertIn("unregistered_numeric", audit.ignored_numeric)
        self.assertEqual(audit.selected, self.allowlist)

    def test_saved_manifest_assertion_fails_on_forbidden_column(self):
        with self.assertRaises(AssertionError):
            assert_no_forbidden_features(
                ("anchor_age", "senior_expert_label"),
                patient_col="subject_id",
                label_col="label_numerical",
            )


class NotebookIntegrationTests(unittest.TestCase):
    def test_all_main_notebooks_use_shared_fail_closed_selector(self):
        notebooks = sorted((REPOSITORY_ROOT / "C2Align").glob("*/*.ipynb"))
        self.assertEqual(len(notebooks), 4)
        for notebook_path in notebooks:
            with self.subTest(notebook=str(notebook_path)):
                notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
                source = "\n".join(
                    "".join(cell.get("source", []))
                    for cell in notebook["cells"]
                    if cell.get("cell_type") == "code"
                )
                self.assertIn(
                    "from c2align_feature_policy import numeric_feature_matrix",
                    source,
                )
                self.assertIn("MODEL_FEATURE_COLUMNS", source)
                self.assertNotIn("table.select_dtypes", source)


if __name__ == "__main__":
    unittest.main()
