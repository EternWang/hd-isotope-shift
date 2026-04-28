#!/usr/bin/env python3
"""Recompute the Day 4 isotope-shift tables and summary plots.

This script reproduces the published Day 4 values from:
- the four recorded trial shifts for H alpha and H beta,
- the reduced-mass theory values quoted in the report,
- the calibration term included in the report's uncertainty budget.

Outputs are written into ../results/ as CSV, JSON, and PNG files.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


DAY4_TRIALS = {
    "Halpha": np.array([1.7973, 1.8170, 1.8071, 1.8062], dtype=float),
    "Hbeta": np.array([1.2656, 1.2945, 1.2667, 1.2552], dtype=float),
}

THEORY = {
    "Halpha": 1.7858,
    "Hbeta": 1.3228,
}

CAL_TERM = {
    "Halpha": 0.051,
    "Hbeta": 0.038,
}

FINAL_REPORTED = {
    "Halpha": (1.801, 0.052),
    "Hbeta": (1.263, 0.039),
}

LINE_LABELS = {
    "Halpha": "H alpha",
    "Hbeta": "H beta",
}

OUTDIR = Path(__file__).resolve().parents[1] / "results"
OUTDIR.mkdir(parents=True, exist_ok=True)
BLUE = "#2F6B9A"
ORANGE = "#D97935"
GREEN = "#5B8C5A"
RED = "#B4554B"
GRAY = "#4A5568"
LIGHT = "#EEF2F6"


def set_plot_style() -> None:
    plt.rcParams.update(
        {
            "figure.dpi": 140,
            "savefig.dpi": 240,
            "font.family": "DejaVu Sans",
            "font.size": 10.5,
            "axes.titlesize": 14,
            "axes.labelsize": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": "#D9DEE7",
            "grid.linewidth": 0.8,
            "grid.alpha": 0.75,
            "legend.frameon": False,
        }
    )


def save_figure(fig: plt.Figure, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def mean_sem(values: np.ndarray) -> tuple[float, float, float]:
    """Return mean, sample standard deviation, and SEM."""
    mean = float(np.mean(values))
    sample_std = float(np.std(values, ddof=1))
    sem = sample_std / np.sqrt(len(values))
    return mean, sample_std, float(sem)


def percent_diff(exp_value: float, theory_value: float) -> float:
    return 100.0 * (exp_value - theory_value) / theory_value


def plot_shift_summary(df_compare: pd.DataFrame) -> None:
    set_plot_style()
    labels = df_compare["Line"].tolist()
    y = np.arange(len(labels))
    exp_values = df_compare["Delta_lambda_exp_A"].to_numpy(dtype=float)
    exp_sigma = df_compare["Sigma_total_A"].to_numpy(dtype=float)
    theory_values = df_compare["Delta_lambda_th_A"].to_numpy(dtype=float)
    percent_offsets = df_compare["Percent_difference_%"].to_numpy(dtype=float)

    fig, ax = plt.subplots(figsize=(7.4, 3.8))
    ax.errorbar(
        exp_values,
        y,
        xerr=exp_sigma,
        fmt="o",
        color=BLUE,
        ecolor="#7FA7C7",
        capsize=5,
        markersize=8,
        label="Experiment",
    )
    ax.scatter(
        theory_values,
        y,
        marker="s",
        s=55,
        color=ORANGE,
        label="Theory",
        zorder=3,
    )
    for idx, pct in enumerate(percent_offsets):
        x_text = max(exp_values[idx] + exp_sigma[idx], theory_values[idx]) + 0.01
        ax.text(x_text, y[idx], f"{pct:+.2f}%", va="center", fontsize=9.5, color=GRAY)
        y_offset = 0.18 if idx == 0 else -0.22
        ax.text(
            exp_values[idx],
            y[idx] + y_offset,
            f"{exp_values[idx]:.3f} +/- {exp_sigma[idx]:.3f}",
            ha="center",
            fontsize=9,
            color=BLUE,
        )

    ax.set_yticks(y, labels)
    ax.set_xlabel("Isotope shift Delta lambda (Angstrom)")
    ax.set_title("Day 4 H-D isotope shifts vs reduced-mass theory")
    ax.set_xlim(1.18, 1.88)
    ax.set_ylim(-0.55, 1.55)
    ax.legend(loc="center right")
    save_figure(fig, OUTDIR / "day4_shift_summary.png")


def plot_uncertainty_breakdown(df_budget: pd.DataFrame) -> None:
    set_plot_style()
    labels = df_budget["Line"].tolist()
    x = np.arange(len(labels))
    width = 0.24

    stat = df_budget["Statistical_SEM_A"].to_numpy(dtype=float)
    cal = df_budget["Calibration_A"].to_numpy(dtype=float)
    total = df_budget["Total_quadrature_A"].to_numpy(dtype=float)

    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    bars_stat = ax.bar(x - width, stat, width=width, color=BLUE, label="Statistical SEM")
    bars_cal = ax.bar(x, cal, width=width, color=ORANGE, label="Calibration term")
    bars_total = ax.bar(x + width, total, width=width, color=GREEN, label="Total quadrature")
    ax.set_xticks(x, labels)
    ax.set_ylabel("Uncertainty contribution (Angstrom)")
    ax.set_title("Calibration dominates the Day 4 uncertainty budget")
    ax.legend(loc="upper right")
    for bars in (bars_stat, bars_cal, bars_total):
        for bar in bars:
            value = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, value + 0.0015, f"{value:.3f}", ha="center", va="bottom", fontsize=8.5)
    save_figure(fig, OUTDIR / "day4_uncertainty_breakdown.png")


def main() -> None:
    compare_rows: list[dict[str, float | str]] = []
    budget_rows: list[dict[str, float | str]] = []
    summary: dict[str, object] = {"day": "Day4", "inputs": {}, "outputs": {}}

    for line_key, trials in DAY4_TRIALS.items():
        mean_value, sample_std, sem = mean_sem(trials)
        theory_value = THEORY[line_key]
        calibration_term = CAL_TERM[line_key]
        total_quadrature = float(np.sqrt(sem**2 + calibration_term**2))

        final_value, final_total = FINAL_REPORTED[line_key]
        pct_diff = percent_diff(final_value, theory_value)
        display_label = LINE_LABELS[line_key]

        compare_rows.append(
            {
                "Line": display_label,
                "Delta_lambda_exp_A": final_value,
                "Sigma_total_A": final_total,
                "Delta_lambda_th_A": theory_value,
                "Percent_difference_%": pct_diff,
            }
        )

        budget_rows.append(
            {
                "Line": display_label,
                "Statistical_SEM_A": sem,
                "Calibration_A": calibration_term,
                "Total_quadrature_A": total_quadrature,
                "Final_reported_total_A": final_total,
            }
        )

        summary["inputs"][line_key] = {
            "trials_A": trials.tolist(),
            "theory_A": theory_value,
            "calibration_term_A": calibration_term,
        }
        summary["outputs"][line_key] = {
            "line_label": display_label,
            "trial_mean_A": mean_value,
            "trial_sample_std_A": sample_std,
            "trial_SEM_A": sem,
            "quadrature_total_A": total_quadrature,
            "final_reported_A": final_value,
            "final_reported_total_A": final_total,
            "percent_difference_%": pct_diff,
        }

    df_compare = pd.DataFrame(compare_rows)
    df_budget = pd.DataFrame(budget_rows)

    df_compare.to_csv(OUTDIR / "day4_tableII_compare.csv", index=False)
    df_budget.to_csv(OUTDIR / "day4_tableIII_error_budget.csv", index=False)

    with open(OUTDIR / "day4_summary.json", "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    plot_shift_summary(df_compare)
    plot_uncertainty_breakdown(df_budget)

    print("Wrote:")
    print(" -", OUTDIR / "day4_tableII_compare.csv")
    print(" -", OUTDIR / "day4_tableIII_error_budget.csv")
    print(" -", OUTDIR / "day4_summary.json")
    print(" -", OUTDIR / "day4_shift_summary.png")
    print(" -", OUTDIR / "day4_uncertainty_breakdown.png")


if __name__ == "__main__":
    main()
