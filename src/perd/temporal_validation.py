"""Temporal extrapolation validation for PERD models."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from perd.features import build_feature_matrix
from perd.models import evaluate_classifier, top_k_hit_rate, train_random_forest_classifier


def split_by_year(df: pd.DataFrame, train_end_year: int = 2021, test_start_year: int = 2022):
    years = pd.to_numeric(df.get("year"), errors="coerce")
    train = df[years <= train_end_year].copy()
    test = df[years >= test_start_year].copy()
    return train, test


def run_temporal_validation(
    df: pd.DataFrame,
    feature_set: str,
    label_column: str,
    train_end_year: int = 2021,
    test_start_year: int = 2022,
) -> dict:
    train, test = split_by_year(df, train_end_year, test_start_year)
    if train.empty or test.empty:
        return {
            "status": "skipped",
            "message": "Temporal train or test set is empty; add records spanning both time periods.",
            "feature_set": feature_set,
        }
    if label_column not in df.columns:
        return {"status": "skipped", "message": f"Missing label column: {label_column}", "feature_set": feature_set}
    y_train = pd.to_numeric(train[label_column], errors="coerce").fillna(0).astype(int)
    y_test = pd.to_numeric(test[label_column], errors="coerce").fillna(0).astype(int)
    if y_train.nunique() < 2:
        return {"status": "skipped", "message": "Training period needs at least two classes.", "feature_set": feature_set}
    X_train, feature_names = build_feature_matrix(train, feature_set)
    X_test, _ = build_feature_matrix(test, feature_set)
    X_test = X_test.reindex(columns=feature_names, fill_value=0)
    model = train_random_forest_classifier(X_train, y_train)
    metrics = evaluate_classifier(model, X_test, y_test)
    if hasattr(model, "predict_proba"):
        metrics["top_k_hit_rate"] = top_k_hit_rate(y_test, model.predict_proba(X_test)[:, 1], k=min(10, len(y_test)))
    return {"status": "ok", "feature_set": feature_set, "metrics": metrics}


def compare_models_temporal(df: pd.DataFrame, feature_sets: list[str], label_column: str) -> dict:
    results = {feature_set: run_temporal_validation(df, feature_set, label_column) for feature_set in feature_sets}
    Path("outputs/reports").mkdir(parents=True, exist_ok=True)
    Path("outputs/reports/temporal_validation_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results
