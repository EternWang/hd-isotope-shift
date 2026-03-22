#!/usr/bin/env python3
"""Fit a two-Gaussian plus linear-baseline model to raw scan segments.

This is an optional helper for refitting the raw H-D scans. Because peak
overlap and baseline drift can make the fit sensitive to the chosen time
window, per-file windows are stored in windows.json.

Examples:
  python fit_from_raw.py --csv ../data/hd/day4_new_lamp/6559-6561_L-H_trail_2.csv --expected-dt 21.6
  python fit_from_raw.py --batch ../data/hd/day4_new_lamp --windows windows.json --plot
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.optimize import curve_fit


def load_csv(path: Path) -> tuple[np.ndarray, np.ndarray]:
    arr = np.loadtxt(path, delimiter=",")
    return arr[:, 0], arr[:, 1]


def model(t, A1, mu1, sig1, A2, mu2, sig2, c0, c1):
    return (
        A1 * np.exp(-(t - mu1) ** 2 / (2 * sig1**2))
        + A2 * np.exp(-(t - mu2) ** 2 / (2 * sig2**2))
        + c0
        + c1 * t
    )


def fit_window(
    t: np.ndarray,
    y: np.ndarray,
    left: float,
    right: float,
    mu1_guess: float,
    mu2_guess: float,
):
    mask = (t >= left) & (t <= right)
    t_window = t[mask]
    y_window = y[mask]

    n_points = len(t_window)
    downsample = max(1, n_points // 30000)
    t_fit = t_window[::downsample]
    y_fit = y_window[::downsample]

    baseline = np.percentile(y_fit, 5)
    amp_guess = max(1e-6, np.max(y_fit) - baseline)
    sigma_guess = max(0.05, (right - left) / 20)

    p0 = [amp_guess, mu1_guess, sigma_guess, amp_guess / 2, mu2_guess, sigma_guess, baseline, 0.0]
    bounds_lo = [0, left, 1e-4, 0, left, 1e-4, -np.inf, -np.inf]
    bounds_hi = [np.inf, right, right - left, np.inf, right, right - left, np.inf, np.inf]

    popt, pcov = curve_fit(model, t_fit, y_fit, p0=p0, bounds=(bounds_lo, bounds_hi), maxfev=200000)
    perr = np.sqrt(np.diag(pcov))
    return popt, perr, (t_fit, y_fit)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=str, help="Path to a single CSV file")
    parser.add_argument("--expected-dt", type=float, default=None, help="Expected peak separation in seconds")
    parser.add_argument("--left", type=float, default=None)
    parser.add_argument("--right", type=float, default=None)
    parser.add_argument("--plot", action="store_true", help="Save fit overlay plots into ../results/")
    parser.add_argument("--batch", type=str, help="Folder of CSV files to process")
    parser.add_argument("--windows", type=str, default="windows.json", help="JSON file with per-file windows")
    args = parser.parse_args()

    outdir = Path(__file__).resolve().parents[1] / "results"
    outdir.mkdir(exist_ok=True, parents=True)

    def run_one(csv_path: Path, expected_dt: float | None, left: float | None, right: float | None) -> None:
        t, y = load_csv(csv_path)

        if left is None or right is None:
            threshold = np.percentile(y, 95) * 0.2
            mask = y > threshold
            if np.any(mask):
                left = float(max(t[0], t[mask].min() - 10))
                right = float(min(t[-1], t[mask].max() + 10))
            else:
                left, right = float(t[0]), float(t[-1])

        t_window = t[(t >= left) & (t <= right)]
        y_window = y[(t >= left) & (t <= right)]
        y_smooth = gaussian_filter1d(y_window, sigma=200)
        idx = np.argsort(y_smooth)[-8:]
        candidates = np.sort(t_window[idx])

        if expected_dt is not None and len(candidates) >= 2:
            best_pair = None
            best_score = np.inf
            for i in range(len(candidates)):
                for j in range(i + 1, len(candidates)):
                    dt = abs(candidates[j] - candidates[i])
                    score = ((dt - expected_dt) / expected_dt) ** 2
                    if score < best_score:
                        best_score = score
                        best_pair = (candidates[i], candidates[j])
            mu1_guess, mu2_guess = best_pair
        else:
            mu1_guess, mu2_guess = candidates[-2], candidates[-1]

        popt, perr, (t_fit, y_fit) = fit_window(t, y, left, right, mu1_guess, mu2_guess)
        _, mu1, _, _, mu2, _, _, _ = popt
        delta_t = abs(mu2 - mu1)

        print(f"\n{csv_path.name}")
        print(f"  window: [{left:.3f}, {right:.3f}] s")
        print(f"  mu1 = {mu1:.6f} s, mu2 = {mu2:.6f} s, Delta t = {delta_t:.6f} s")

        if args.plot:
            t_dense = np.linspace(left, right, 2000)
            plt.figure(figsize=(7.0, 4.0))
            plt.plot(t_fit, y_fit, label="Data (downsampled)")
            plt.plot(t_dense, model(t_dense, *popt), label="Fit")
            plt.xlabel("Time (s)")
            plt.ylabel("Signal (V)")
            plt.title(f"{csv_path.stem}: two-peak fit")
            plt.legend()
            plt.tight_layout()
            outpath = outdir / f"fit_{csv_path.stem}.png"
            plt.savefig(outpath, dpi=200)
            plt.close()
            print(f"  saved plot: {outpath}")

    if args.batch:
        windows = json.loads(Path(args.windows).read_text(encoding="utf-8"))
        batch_dir = Path(args.batch)
        for csv_path in sorted(batch_dir.glob("*.csv")):
            config = windows.get(csv_path.name, {})
            run_one(
                csv_path,
                expected_dt=config.get("expected_dt_s", args.expected_dt),
                left=config.get("left_s", args.left),
                right=config.get("right_s", args.right),
            )
    else:
        if not args.csv:
            raise SystemExit("Provide --csv or --batch.")
        run_one(Path(args.csv), expected_dt=args.expected_dt, left=args.left, right=args.right)


if __name__ == "__main__":
    main()
