"""Matplotlib visualizations for PERD outputs."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def _skip(message: str) -> dict:
    return {"status": "skipped", "message": message}


def _save(output_path: str | Path) -> dict:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    return {"status": "ok", "path": str(path)}


def plot_dopant_distribution(df: pd.DataFrame, output_path="outputs/figures/dopant_distribution.png") -> dict:
    if "dopant_element_1" not in df.columns:
        return _skip("Missing dopant_element_1.")
    df["dopant_element_1"].fillna("unknown").value_counts().plot(kind="bar")
    plt.xlabel("Dopant")
    plt.ylabel("Count")
    return _save(output_path)


def plot_conductivity_distribution(df: pd.DataFrame, output_path="outputs/figures/conductivity_distribution.png") -> dict:
    if "total_conductivity_25c_s_cm" not in df.columns:
        return _skip("Missing total_conductivity_25c_s_cm.")
    pd.to_numeric(df["total_conductivity_25c_s_cm"], errors="coerce").dropna().plot(kind="hist", bins=20)
    plt.xlabel("Total conductivity at 25 C (S/cm)")
    return _save(output_path)


def plot_conductivity_vs_lifetime(df: pd.DataFrame, output_path="outputs/figures/conductivity_vs_lifetime.png") -> dict:
    required = {"total_conductivity_25c_s_cm", "li_symmetric_lifetime_h"}
    if not required.issubset(df.columns):
        return _skip(f"Missing fields: {sorted(required - set(df.columns))}")
    plt.scatter(pd.to_numeric(df["total_conductivity_25c_s_cm"], errors="coerce"), pd.to_numeric(df["li_symmetric_lifetime_h"], errors="coerce"))
    plt.xlabel("Total conductivity at 25 C (S/cm)")
    plt.ylabel("Li symmetric lifetime (h)")
    return _save(output_path)


def plot_bprs_vs_conductivity(df: pd.DataFrame, output_path="outputs/figures/bprs_vs_conductivity.png") -> dict:
    required = {"bprs_score", "total_conductivity_25c_s_cm"}
    if not required.issubset(df.columns):
        return _skip(f"Missing fields: {sorted(required - set(df.columns))}")
    plt.scatter(pd.to_numeric(df["total_conductivity_25c_s_cm"], errors="coerce"), pd.to_numeric(df["bprs_score"], errors="coerce"))
    plt.xlabel("Total conductivity at 25 C (S/cm)")
    plt.ylabel("BPRS score")
    return _save(output_path)


def plot_model_comparison(metrics_df: pd.DataFrame, output_path="outputs/figures/model_comparison.png") -> dict:
    if not {"model", "f1"}.issubset(metrics_df.columns):
        return _skip("Missing model or f1 columns.")
    metrics_df.plot(x="model", y="f1", kind="bar", legend=False)
    plt.ylabel("F1")
    return _save(output_path)


def plot_candidate_map(df: pd.DataFrame, output_path="outputs/figures/candidate_map.png") -> dict:
    required = {"bprs_score", "capacity_retention_percent"}
    if not required.issubset(df.columns):
        return _skip(f"Missing fields: {sorted(required - set(df.columns))}")
    plt.scatter(pd.to_numeric(df["bprs_score"], errors="coerce"), pd.to_numeric(df["capacity_retention_percent"], errors="coerce"))
    plt.xlabel("BPRS score")
    plt.ylabel("Capacity retention (%)")
    return _save(output_path)
