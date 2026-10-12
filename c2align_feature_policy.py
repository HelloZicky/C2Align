"""Task-level feature contracts for the C2Align model matrix.

The model matrix is built from an exact, caller-supplied allowlist. Extra numeric columns are not selected, and annotation, adjudication, outcome, post-index, split, cohort, and identifier metadata are not eligible model covariates.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import logging
import re
from typing import Iterable, Sequence

import numpy as np
import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype


LOGGER = logging.getLogger(__name__)


# Metadata fields that are not eligible model covariates.
FORBIDDEN_EXACT_COLUMNS = frozenset(
    {
        # Labels, candidate labels, and cohort-membership decisions.
        "label",
        "label_numerical",
        "label_subtype",
        "target",
        "outcome",
        "ground_truth",
        "gold_label",
        "candidate_label",
        "candidate_code_positive",
        "include_in_cohort",
        # Physician annotation and adjudication.
        "physician_1_label",
        "physician_2_label",
        "senior_expert_label",
        "physician_1_subtype",
        "physician_2_subtype",
        "senior_expert_subtype",
        "senior_evidence_status",
        "annotation_status",
        "adjudication_status",
        "review_status",
        # Split and resampling metadata.
        "split",
        "partition",
        "dataset_split",
        "cv_fold",
        "fold",
        "fold_id",
        # Outcome-derived or post-index fields.
        "readmitted_within_30_days",
        "days_to_readmission",
        "readmission_time",
        "death_time",
        "time_to_death",
        "outcome_time",
        "post_index_event",
        # Identifiers are metadata rather than model covariates.
        "subject_id",
        "patient_id",
        "hadm_id",
        "stay_id",
        "encounter_id",
        "admission_id",
    }
)


# Token-boundary matching covers common renamed variants. Branch probability names remain eligible only when explicitly allowlisted.
FORBIDDEN_NAME_PATTERNS = tuple(
    re.compile(pattern, flags=re.IGNORECASE)
    for pattern in (
        r"(?:^|_)(?:label|target|outcome|ground_truth|gold_label)(?:_|$)",
        r"(?:^|_)(?:physician|annotator|annotation)(?:_|$)",
        r"(?:^|_)(?:adjudicat(?:e|ed|ion|or|ory)?|senior_expert)(?:_|$)",
        r"(?:^|_)(?:candidate_label|candidate_code_positive|include_in_cohort)(?:_|$)",
        r"(?:^|_)(?:split|partition|cv_fold|fold_id)(?:_|$)",
        r"(?:^|_)(?:post_index|after_index|future_event)(?:_|$)",
        r"(?:^|_)(?:days_to_readmission|readmission_time|time_to_death|death_time)(?:_|$)",
    )
)


@dataclass(frozen=True)
class FeatureAudit:
    """Serializable record of one feature-selection decision."""

    selected: tuple[str, ...]
    blocked_present: tuple[str, ...]
    ignored_numeric: tuple[str, ...]

    def as_dict(self) -> dict[str, list[str]]:
        return {
            key: list(value)
            for key, value in asdict(self).items()
        }


def forbidden_reason(
    column: str,
    *,
    patient_col: str,
    label_col: str,
) -> str | None:
    """Return why *column* is forbidden, or ``None`` when it is not."""

    normalized = str(column).strip().lower()
    dynamic_metadata = {str(patient_col).strip().lower(), str(label_col).strip().lower()}
    if normalized in dynamic_metadata:
        return "patient identifier or target label"
    if normalized in FORBIDDEN_EXACT_COLUMNS:
        return "known annotation, outcome, split, post-index, or identifier field"
    for pattern in FORBIDDEN_NAME_PATTERNS:
        if pattern.search(normalized):
            return f"forbidden name pattern: {pattern.pattern}"
    return None


def validate_feature_allowlist(
    table: pd.DataFrame,
    allowed_feature_columns: Sequence[str],
    *,
    patient_col: str,
    label_col: str,
) -> tuple[str, ...]:
    """Validate and return an exact feature allowlist.

    The function is fail-closed: a missing, duplicate, non-numeric, or forbidden
    requested feature raises before a model matrix is created.
    """

    columns = tuple(str(column) for column in allowed_feature_columns)
    if not columns:
        raise ValueError("The explicit model feature allowlist is empty.")
    if len(columns) != len(set(columns)):
        duplicates = sorted({column for column in columns if columns.count(column) > 1})
        raise ValueError(f"Duplicate columns in feature allowlist: {duplicates}")

    forbidden = {
        column: reason
        for column in columns
        if (
            reason := forbidden_reason(
                column,
                patient_col=patient_col,
                label_col=label_col,
            )
        )
    }
    if forbidden:
        details = ", ".join(
            f"{column!r} ({reason})"
            for column, reason in sorted(forbidden.items())
        )
        raise ValueError(f"Forbidden columns requested as model features: {details}")

    missing = sorted(set(columns).difference(table.columns))
    if missing:
        raise KeyError(f"Configured model features are missing: {missing}")

    non_numeric = sorted(
        column
        for column in columns
        if not (
            is_numeric_dtype(table[column].dtype)
            or is_bool_dtype(table[column].dtype)
        )
    )
    if non_numeric:
        raise TypeError(
            "Configured model features must be numeric or boolean: "
            f"{non_numeric}"
        )
    return columns


def audit_feature_selection(
    table: pd.DataFrame,
    allowed_feature_columns: Sequence[str],
    *,
    patient_col: str,
    label_col: str,
) -> FeatureAudit:
    """Report selected, blocked, and ignored numeric fields."""

    selected = validate_feature_allowlist(
        table,
        allowed_feature_columns,
        patient_col=patient_col,
        label_col=label_col,
    )
    selected_set = set(selected)
    blocked_present = tuple(
        sorted(
            str(column)
            for column in table.columns
            if forbidden_reason(
                str(column),
                patient_col=patient_col,
                label_col=label_col,
            )
        )
    )
    ignored_numeric = tuple(
        sorted(
            str(column)
            for column in table.columns
            if column not in selected_set
            and (
                is_numeric_dtype(table[column].dtype)
                or is_bool_dtype(table[column].dtype)
            )
            and str(column) not in blocked_present
        )
    )
    return FeatureAudit(
        selected=selected,
        blocked_present=blocked_present,
        ignored_numeric=ignored_numeric,
    )


def numeric_feature_matrix(
    table: pd.DataFrame,
    allowed_feature_columns: Sequence[str],
    *,
    patient_col: str,
    label_col: str,
    imputation_values: pd.Series | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    """Build a numeric matrix from an exact, validated allowlist."""

    audit = audit_feature_selection(
        table,
        allowed_feature_columns,
        patient_col=patient_col,
        label_col=label_col,
    )
    feature_columns = list(audit.selected)
    features = table.loc[:, feature_columns].astype(float)
    features = features.replace([np.inf, -np.inf], np.nan)
    if imputation_values is None:
        imputation_values = features.median(numeric_only=True)
    else:
        missing_imputers = sorted(set(feature_columns).difference(imputation_values.index))
        if missing_imputers:
            raise KeyError(
                "Training imputation values are missing model features: "
                f"{missing_imputers}"
            )
        imputation_values = imputation_values.reindex(feature_columns)
    features = features.fillna(imputation_values).fillna(0.0)
    features.attrs["feature_audit"] = audit.as_dict()
    LOGGER.info("C2Align feature audit: %s", json.dumps(audit.as_dict(), sort_keys=True))
    return features, feature_columns


def assert_no_forbidden_features(
    feature_columns: Iterable[str],
    *,
    patient_col: str,
    label_col: str,
) -> None:
    """Validate a saved feature manifest."""

    forbidden = [
        column
        for column in feature_columns
        if forbidden_reason(
            str(column),
            patient_col=patient_col,
            label_col=label_col,
        )
    ]
    if forbidden:
        raise AssertionError(
            f"Forbidden columns entered the feature matrix: {sorted(forbidden)}"
        )
