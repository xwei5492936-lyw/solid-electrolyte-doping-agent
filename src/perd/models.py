"""Baseline machine-learning models for PERD."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split

from perd.features import build_feature_matrix


def _friendly(message: str) -> dict:
    return {"status": "skipped", "message": message}


def train_random_forest_classifier(X, y):
    model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight="balanced")
    return model.fit(X, y)


def train_logistic_regression_classifier(X, y):
    model = LogisticRegression(max_iter=1000, class_weight="balanced")
    return model.fit(X, y)


def evaluate_classifier(model, X_test, y_test) -> dict:
    if len(y_test) == 0:
        return _friendly("No test samples available.")
    predictions = model.predict(X_test)
    metrics = {
        "accuracy": float(accuracy_score(y_test, predictions)),
        "precision": float(precision_score(y_test, predictions, zero_division=0)),
        "recall": float(recall_score(y_test, predictions, zero_division=0)),
        "f1": float(f1_score(y_test, predictions, zero_division=0)),
    }
    if hasattr(model, "predict_proba") and len(set(y_test)) > 1:
        metrics["roc_auc"] = float(roc_auc_score(y_test, model.predict_proba(X_test)[:, 1]))
    else:
        metrics["roc_auc"] = None
    return metrics


def top_k_hit_rate(y_true, scores, k: int = 10) -> float:
    if len(y_true) == 0:
        return 0.0
    y = np.asarray(y_true)
    s = np.asarray(scores)
    k = min(k, len(y))
    order = np.argsort(s)[::-1][:k]
    return float(y[order].sum() / max(1, min(k, y.sum() if y.sum() > 0 else k)))


def _fit_and_eval(df: pd.DataFrame, label_column: str, feature_set: str, model_name: str) -> dict:
    if len(df) < 4:
        return _friendly("Not enough data for train/test split; add verified real records.")
    if label_column not in df.columns:
        return _friendly(f"Missing label column: {label_column}")
    y = pd.to_numeric(df[label_column], errors="coerce").fillna(0).astype(int)
    if y.nunique() < 2:
        return _friendly("Need at least two label classes for classifier training.")
    X, feature_names = build_feature_matrix(df, feature_set)
    stratify = y if y.value_counts().min() >= 2 else None
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=stratify)
    if model_name == "random_forest":
        model = train_random_forest_classifier(X_train, y_train)
    else:
        model = train_logistic_regression_classifier(X_train, y_train)
    metrics = evaluate_classifier(model, X_test, y_test)
    Path("outputs/models").mkdir(parents=True, exist_ok=True)
    joblib.dump(model, f"outputs/models/{feature_set}_{model_name}.joblib")
    return {"status": "ok", "feature_set": feature_set, "model": model_name, "feature_count": len(feature_names), "metrics": metrics}


def compare_baseline_models(df: pd.DataFrame, label_column: str) -> dict:
    results: dict[str, object] = {}
    if label_column not in df.columns:
        return _friendly(f"Missing label column: {label_column}")
    if "total_conductivity_25c_s_cm" in df.columns:
        y = pd.to_numeric(df[label_column], errors="coerce").fillna(0).astype(int)
        scores = pd.to_numeric(df["total_conductivity_25c_s_cm"], errors="coerce").fillna(0)
        results["conductivity_only_ranking"] = {"top_k_hit_rate": top_k_hit_rate(y, scores, k=min(10, len(df)))}
    else:
        results["conductivity_only_ranking"] = _friendly("Missing total_conductivity_25c_s_cm.")
    for feature_set in ["composition_only", "descriptor_only", "processing_aware", "full_perd"]:
        results[feature_set] = _fit_and_eval(df, label_column, feature_set, "random_forest")
    Path("outputs/reports").mkdir(parents=True, exist_ok=True)
    Path("outputs/reports/baseline_metrics.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results
