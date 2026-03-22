# Data

All raw scans are stored as two-column CSV files:

1. time in seconds
2. detector signal in volts

## Folder meaning

- `hg/day1/`, `hg/day2/`
  Mercury lamp scans used to calibrate the scan rate `beta = d lambda / dt`.
- `hd/day3_old_lamp/`
  Mixed H-D lamp scans from the older lamp, kept as a lower-SNR comparison set.
- `hd/day4_new_lamp/`
  Mixed H-D lamp scans from the new lamp. These are the repeated measurements used for the final Day 4 results.

## Metadata

`metadata.csv` stores one row per file and records:

- day label
- lamp type
- spectral region
- nominal sweep rate, when available from notes
- scan direction, when encoded in the filename
