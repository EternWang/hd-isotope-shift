# Analysis scripts

## 1. Recompute the Day 4 report values

```bash
python recompute_tables_day4.py
```

This script reproduces the Day 4 comparison table and uncertainty budget from the recorded trial shifts plus the quoted calibration term.

Outputs written to `../results/`:

- `day4_tableII_compare.csv`
- `day4_tableIII_error_budget.csv`
- `day4_summary.json`
- `day4_shift_summary.png`
- `day4_uncertainty_breakdown.png`

## 2. Optional refit of raw scans

Raw scan files are two-column CSVs:

- column 1: time in seconds
- column 2: detector signal in volts

The helper script `fit_from_raw.py` fits a two-Gaussian plus linear-baseline model to a chosen time window. Because overlapping peaks and baseline drift can make the fit unstable, per-file windows are stored in `windows.json`.

Batch example:

```bash
python fit_from_raw.py --batch ../data/hd/day4_new_lamp --windows windows.json --plot
```
