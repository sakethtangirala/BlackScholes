"""Plot ranked options CSV into a bar chart image.

Loads `tools/ranked_options.csv`, computes IV/HV ratio, selects top N by IV/HV,
and saves a bar chart to `tools/ranked_options.png`.
"""
from __future__ import annotations

import argparse
import math
import os
import sys
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    return df


def prepare_df(df: pd.DataFrame) -> pd.DataFrame:
    # Ensure numeric
    for c in ("iv", "hv", "mid", "extrinsic"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=["iv", "mid"]) if "iv" in df.columns else df
    df["hv"] = df["hv"].fillna(1e-6)
    df["iv_hv"] = df["iv"] / (df["hv"] + 1e-9)
    df["label"] = df["ticker"] + "\n" + df["expiry"] + "\n" + df["type"] + " K=" + df["strike"].astype(str)
    return df


def plot_top(df: pd.DataFrame, top_n: int, out: str, metric: str = "iv_hv") -> None:
    df2 = df.sort_values(metric, ascending=False).head(top_n)
    if df2.empty:
        print("No rows to plot", file=sys.stderr)
        return

    labels = df2["label"]
    values = df2[metric]

    plt.figure(figsize=(max(8, len(values) * 0.6), 6))
    bars = plt.bar(range(len(values)), values, color="tab:blue")
    plt.xticks(range(len(values)), labels, rotation=45, ha="right")
    plt.ylabel(metric)
    plt.title(f"Top {top_n} options by {metric}")
    plt.tight_layout()
    plt.savefig(out)
    print(f"Saved plot to {out}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="tools/ranked_options.csv")
    parser.add_argument("--out", default="tools/ranked_options.png")
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--metric", default="iv_hv", help="Metric to plot: iv, hv, iv_hv, mid")
    args = parser.parse_args(argv)

    if not os.path.exists(args.csv):
        print(f"CSV not found: {args.csv}", file=sys.stderr)
        return 2

    df = load_csv(args.csv)
    df = prepare_df(df)
    plot_top(df, args.top, args.out, args.metric)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
