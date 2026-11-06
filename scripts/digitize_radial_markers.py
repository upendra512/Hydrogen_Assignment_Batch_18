#!/usr/bin/env python3
"""Digitize orange experimental squares from Mularski et al. Figures 12-14.

Input: the attributed 360-dpi source-page renders in
data/validation/source_figures/. Output: approximate measured markers only;
colored model curves and the legend symbols are excluded.
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "data" / "validation" / "source_figures"
OUT = ROOT / "data" / "validation" / "fig12_14_radial_experiment.csv"

# Pixel positions of the plot rows on the 360-dpi source-page renders. The
# search window is only a seed; the horizontal axis is detected from the raster.
PAGES = {
    15: {
        "file": "mularski_2021_pdf_page15_360dpi.png",
        "stations": [0.13, 0.20, 0.28, 0.34, 0.51],
        "baseline_seeds": [1310, 1834, 2354, 3052, 3559],
    },
    16: {
        "file": "mularski_2021_pdf_page16_360dpi.png",
        "stations": [0.81, 1.12, 1.73],
        "baseline_seeds": [811, 1492, 2022],
    },
}
Y_MAX = {
    0.13: [0.4, 0.3, 0.4, 0.6],
    0.20: [0.5, 0.4, 0.4, 0.5],
    0.28: [0.6, 0.3, 0.3, 0.5],
    0.34: [0.6, 0.3, 0.3, 0.4],
    0.51: [0.4, 0.3, 0.3, 0.3],
    0.81: [0.5, 0.4, 0.3, 0.3],
    1.12: [0.5, 0.4, 0.3, 0.3],
    1.73: [0.5, 0.4, 0.3, 0.3],
}
SPECIES = ["CO", "H2", "CO2", "H2O"]
# Separated by the reference page's four-panel layout.
X_REGIONS = [(250, 850), (850, 1500), (1500, 2120), (2150, 2800)]


def line_runs(indices: np.ndarray) -> list[list[int]]:
    runs: list[list[int]] = []
    for value in indices:
        value = int(value)
        if not runs or value > runs[-1][-1] + 1:
            runs.append([value])
        else:
            runs[-1].append(value)
    return runs


def find_axes(gray: np.ndarray, seed: int, x_region: tuple[int, int]):
    dark = gray < 115
    x0, x1 = x_region
    ys = range(max(0, seed - 50), min(gray.shape[0], seed + 51))
    scores = [int(dark[y, x0:x1].sum()) for y in ys]
    baseline = list(ys)[int(np.argmax(scores))]
    runs = line_runs(np.flatnonzero(dark[baseline, x0:x1]) + x0)
    run = max(runs, key=len)
    left, right = run[0], run[-1]
    if right - left < 350:
        raise ValueError(f"Could not locate plot x-axis near y={baseline}: {run}")

    # Trace upward from the x-axis baseline. Adjacent plot rows reuse the same
    # x pixel columns, so counting all dark pixels would accidentally include
    # the vertical axis from the preceding subplot.
    ylo = max(0, baseline - 600)
    candidates = []
    for x in range(left - 1, left + 6):
        indices = np.flatnonzero(dark[ylo:baseline + 1, x]) + ylo
        runs = line_runs(indices)
        merged = []
        for run in runs:
            if merged and run[0] - merged[-1][-1] <= 30:
                merged[-1].extend(run)
            else:
                merged.append(run)
        for run in merged:
            start, end = run[0], run[-1]
            length = end - start + 1
            if length >= 200 and end >= baseline - 80:
                candidates.append((end, length, start))
    if not candidates:
        raise ValueError(f"Could not locate plot y-axis at x={left}")
    _, _, top = max(candidates)
    return left, right, top, baseline


def orange_square_centers(rgb: np.ndarray) -> list[tuple[float, float]]:
    red, green, blue = rgb.transpose(2, 0, 1)
    mask = ((red > 205) & (green > 70) & (green < 185) & (blue < 110)
            & ((red.astype(int) - green.astype(int)) > 50))
    labels, count = ndimage.label(mask)
    centers = []
    for i, slc in enumerate(ndimage.find_objects(labels), start=1):
        if slc is None:
            continue
        ys, xs = slc
        component = labels[slc] == i
        area = int(component.sum())
        width, height = xs.stop - xs.start, ys.stop - ys.start
        # Experimental squares are 21-25 px at this render size. This removes
        # the smaller orange legend swatches and anti-aliased text fragments.
        if area >= 300 and width >= 18 and height >= 18:
            centers.append(((xs.start + xs.stop - 1) / 2,
                            (ys.start + ys.stop - 1) / 2))
    return centers


def main() -> int:
    rows = []
    for page, meta in PAGES.items():
        image = Image.open(FIGURES / meta["file"]).convert("RGB")
        rgb = np.asarray(image)
        gray = np.asarray(image.convert("L"))
        centers = orange_square_centers(rgb)
        for station, seed in zip(meta["stations"], meta["baseline_seeds"]):
            for col, sp in enumerate(SPECIES):
                left, right, top, baseline = find_axes(gray, seed, X_REGIONS[col])
                points = [(x, y) for x, y in centers
                          if left - 12 < x < right + 12 and top - 8 < y < baseline + 8]
                for x, y in points:
                    radius_m = np.clip(0.1 * (x - left) / (right - left), 0.0, 0.1)
                    value_pct = 100.0 * Y_MAX[station][col] * np.clip(
                        (baseline - y) / (baseline - top), 0.0, 1.0)
                    rows.append({
                        "axial_station_m": f"{station:.2f}",
                        "radius_m": f"{radius_m:.5f}",
                        "species": sp,
                        "mole_fraction_pct": f"{value_pct:.2f}",
                        "source_pdf_page": page,
                    })

    with OUT.open("w", newline="", encoding="utf-8") as stream:
        stream.write("# Source: Mularski & Modlinski (2021), Figures 12-14, experimental orange squares.\n")
        stream.write("# PDF pages 15-16; 360-dpi raster; axis endpoints and y maxima calibrated from plotted ticks.\n")
        stream.write("# Approximate digitization uncertainty: +/-0.001 m radius and +/-0.5 mole-fraction percentage point.\n")
        stream.write("# Values are experimental markers only, not the paper's CFD curves. H2O is not scored because the paper derives it by hydrogen balance.\n")
        writer = csv.DictWriter(stream, fieldnames=["axial_station_m", "radius_m", "species",
                                                    "mole_fraction_pct", "source_pdf_page"])
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda r: (float(r["axial_station_m"]), r["species"],
                                                     float(r["radius_m"]))))
    counts = {sp: sum(row["species"] == sp for row in rows) for sp in SPECIES}
    print(f"Wrote {OUT}; total markers={len(rows)}; counts={counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
