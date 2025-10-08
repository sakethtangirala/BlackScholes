"""Simple European stock ranker using historical price data from yfinance.

Default metrics:
- 1y return
- 6m momentum
- annualized volatility (inverse used as stability)
- dividend yield

Outputs a CSV with metrics and a combined score.
"""
from __future__ import annotations

import argparse
import sys
from typing import List, Dict, Tuple

import numpy as np
import pandas as pd
import yfinance as yf


def fetch_adj_close(ticker: str, period: str = "1y") -> pd.Series:
    t = yf.Ticker(ticker)
    hist = t.history(period=period, auto_adjust=False)
    if hist.empty:
        raise ValueError(f"No history for {ticker}")
    # Use Adjusted Close if available
    if "Close" in hist.columns and "Dividends" in hist.columns:
        # yfinance returns 'Close' and 'Adj Close' depending on version; prefer 'Close' adjusted by splits/dividends
        if "Adj Close" in hist.columns:
            return hist["Adj Close"].dropna()
    if "Adj Close" in hist.columns:
        return hist["Adj Close"].dropna()
    if "Close" in hist.columns:
        return hist["Close"].dropna()
    raise ValueError(f"No close prices for {ticker}")


def compute_metrics(price: pd.Series) -> Dict[str, float]:
    # price indexed by Timestamp
    returns = price.pct_change().dropna()
    ann_vol = returns.std() * np.sqrt(252)

    def pct_change_over(period_days: int) -> float:
        if len(price) < period_days:
            # fallback to available range
            return (price.iloc[-1] / price.iloc[0] - 1.0)
        return (price.iloc[-1] / price.iloc[-period_days] - 1.0)

    # approximate days
    r_1y = pct_change_over(252)
    r_6m = pct_change_over(126)

    return {
        "1y_return": float(r_1y),
        "6m_return": float(r_6m),
        "ann_vol": float(ann_vol),
    }


def get_dividend_yield(ticker: str) -> float:
    t = yf.Ticker(ticker)
    info = t.info if hasattr(t, "info") else {}
    # yfinance's info keys vary; try common ones
    for key in ("dividendYield", "dividendYieldPct", "dividendRate"):
        if key in info and info[key] is not None:
            val = info[key]
            # dividendYield is typically decimal
            if key == "dividendRate":
                # dividendRate is absolute amount; compute yield from price
                try:
                    price = info.get("previousClose") or info.get("regularMarketPrice")
                    if price:
                        return float(val) / float(price)
                except Exception:
                    pass
            else:
                return float(val)
    return 0.0


def score_metrics(m: Dict[str, float], weights: Dict[str, float]) -> float:
    # Normalize metrics across sensible transforms: higher is better for returns & dividend, lower is better for vol
    r1 = m["1y_return"]
    r6 = m["6m_return"]
    vol = m["ann_vol"]
    dy = m.get("dividend_yield", 0.0)

    # Avoid division by zero
    vol_score = 1.0 / (vol + 1e-6)

    # z-score each (we'll combine raw but scale by simple transforms)
    # For simplicity we combine scaled metrics directly
    score = (
        weights["1y"] * r1 + weights["6m"] * r6 + weights["vol"] * vol_score + weights["div"] * dy
    )
    return float(score)


def rank_tickers(tickers: List[str], weights: Dict[str, float], period: str = "1y") -> pd.DataFrame:
    rows = []
    for t in tickers:
        try:
            price = fetch_adj_close(t, period=period)
        except Exception as e:
            print(f"Warning: skipping {t} - {e}", file=sys.stderr)
            continue

        m = compute_metrics(price)
        try:
            dy = get_dividend_yield(t)
        except Exception:
            dy = 0.0
        m["dividend_yield"] = dy
        s = score_metrics(m, weights)
        rows.append({"ticker": t, **m, "score": s})

    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("No tickers processed successfully")
    # normalize score
    df = df.sort_values("score", ascending=False).reset_index(drop=True)
    return df


def default_tickers() -> List[str]:
    # A small default sample of prominent European tickers (Yahoo format)
    return [
        "ASML.AS",  # ASML (Netherlands)
        "SAP.DE",  # SAP (Germany)
        "SAN.PA",  # Sanofi (France)
        "MC.PA",  # LVMH (France)
        "RDSA.AS",  # Shell (Netherlands - A)
        "SHEL.L",  # Shell (LSE)
        "GLEN.L",  # Glencore (LSE)
        "NESN.SW",  # Nestle (Switzerland)
        "NOVN.SW",  # Novartis
        "AIR.PA",  # Airbus
    ]


def parse_weights(s: str) -> Dict[str, float]:
    # Expect comma-separated key=val pairs
    w = {"1y": 0.4, "6m": 0.3, "vol": 0.2, "div": 0.1}
    if not s:
        return w
    for item in s.split(","):
        k, v = item.split("=")
        k = k.strip()
        v = float(v)
        if k in w:
            w[k] = v
    # normalize
    ssum = sum(w.values())
    if ssum <= 0:
        raise ValueError("weights must sum to > 0")
    for k in w:
        w[k] = w[k] / ssum
    return w


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tickers", nargs="*", help="Tickers to rank (Yahoo format)")
    parser.add_argument("--top", type=int, default=10, help="How many top results to show")
    parser.add_argument("--period", default="1y", help="History period for yfinance (e.g., 1y, 2y)")
    parser.add_argument(
        "--weights",
        default="",
        help="Comma separated weights as key=val for keys 1y,6m,vol,div. Example: 1y=0.5,6m=0.3,vol=0.15,div=0.05",
    )
    parser.add_argument("--out", default="tools/ranked_stocks.csv", help="CSV output path")

    args = parser.parse_args(argv)

    tickers = args.tickers or default_tickers()
    weights = parse_weights(args.weights)

    df = rank_tickers(tickers, weights, period=args.period)
    df.to_csv(args.out, index=False)
    print(df.head(args.top).to_string(index=False))
    print(f"Saved CSV to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
