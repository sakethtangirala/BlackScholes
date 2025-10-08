"""Rank European options to short using Black-Scholes and market option chains.

This script fetches option chains via yfinance for provided tickers, computes
implied volatility for each option by matching market mid price to Black-
Scholes theoretical price (European assumptions), and scores options to find
candidates to short (e.g., IV >> historical vol, high extrinsic value, high
theta decay).

Output: CSV of option metrics and printed top candidates.
"""
from __future__ import annotations

import csv
import sys
import math
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

import numpy as np
import yfinance as yf

# Ensure the project's `src` directory is on sys.path so we can import bs_pricer
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
src_path = os.path.join(repo_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from bs_pricer.black_scholes import black_scholes_price, greeks


@dataclass
class OptionRow:
    ticker: str
    expiry: str
    option_type: str
    strike: float
    last_price: float
    bid: float
    ask: float
    mid: float
    iv: Optional[float]
    hv: Optional[float]
    extrinsic: float
    theta: Optional[float]


def implied_vol_from_price(option_type: str, S: float, K: float, r: float, T: float, q: float, market_price: float, initial_guess: float = 0.2) -> Optional[float]:
    # Use bisection in [1e-6, 5.0]
    lo = 1e-6
    hi = 5.0
    # If market price is below intrinsic (for calls: max(S-K,0)) then no solution
    intrinsic = max(S - K, 0.0) if option_type == "call" else max(K - S, 0.0)
    if market_price <= intrinsic + 1e-12:
        return 0.0

    def f(sigma: float) -> float:
        return black_scholes_price(option_type, S, K, r, sigma, T, q) - market_price

    f_lo = f(lo)
    f_hi = f(hi)
    # Expand hi if needed
    tries = 0
    while f_lo * f_hi > 0 and tries < 10:
        hi *= 2
        f_hi = f(hi)
        tries += 1

    if f_lo * f_hi > 0:
        return None

    for _ in range(60):
        mid = 0.5 * (lo + hi)
        val = f(mid)
        if abs(val) < 1e-8:
            return float(mid)
        if f_lo * val < 0:
            hi = mid
            f_hi = val
        else:
            lo = mid
            f_lo = val

    return float(0.5 * (lo + hi))


def historical_volatility(price_series, days=30):
    # daily returns
    if len(price_series) < 2:
        return None
    rets = price_series.pct_change().dropna()
    if rets.empty:
        return None
    return float(rets.std() * math.sqrt(252))


def rank_options_for_ticker(ticker: str, top_n: int = 20) -> List[OptionRow]:
    t = yf.Ticker(ticker)
    try:
        spot = float(t.history(period="1d")["Close"].iloc[-1])
    except Exception:
        print(f"Could not fetch spot for {ticker}", file=sys.stderr)
        return []

    # estimate dividend yield and r ~ 0.01 default
    info = getattr(t, "info", {}) or {}
    q = float(info.get("dividendYield") or 0.0) or 0.0
    r = 0.01

    # fetch historical for HV
    try:
        hist = t.history(period="6mo")
        hv = historical_volatility(hist["Close"], days=30)
    except Exception:
        hv = None

    rows: List[OptionRow] = []

    expiries = t.options
    for expiry in expiries:
        try:
            opt_chain = t.option_chain(expiry)
        except Exception:
            continue

        # combine calls and puts
        for df, opt_type in ((opt_chain.calls, "call"), (opt_chain.puts, "put")):
            for _, r0 in df.iterrows():
                strike = float(r0.get("strike"))
                bid = float(r0.get("bid") or 0.0)
                ask = float(r0.get("ask") or 0.0)
                last = float(r0.get("lastPrice") or 0.0)
                mid = (bid + ask) / 2.0 if (bid and ask and bid > 0 and ask > 0) else last

                # time to expiry in years
                ex_date = datetime.strptime(expiry, "%Y-%m-%d")
                today = datetime.utcnow()
                T = max((ex_date - today).days / 365.0, 1e-6)

                iv = None
                if mid and mid > 0:
                    try:
                        iv = implied_vol_from_price(opt_type, spot, strike, r, T, q, mid)
                    except Exception:
                        iv = None

                extrinsic = max(mid - (max(spot - strike, 0.0) if opt_type == "call" else max(strike - spot, 0.0)), 0.0)

                theta = None
                if iv is not None:
                    try:
                        g = greeks(opt_type, spot, strike, r, iv, T, q)
                        theta = g.get("theta")
                    except Exception:
                        theta = None

                rows.append(OptionRow(ticker, expiry, opt_type, strike, last, bid, ask, mid, iv, hv, extrinsic, theta))

    # Score: prefer high IV relative to HV, high extrinsic, negative theta magnitude
    scored = []
    for r0 in rows:
        if r0.iv is None or r0.mid <= 0:
            continue
        iv = r0.iv
        hv_local = r0.hv or 0.0001
        iv_hv = iv / (hv_local + 1e-6)
        theta_score = -r0.theta if r0.theta is not None else 0.0
        score = iv_hv * 0.6 + (r0.extrinsic / (r0.mid + 1e-6)) * 0.3 + theta_score * 0.1
        scored.append((score, r0))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored[:top_n]]


def main(argv: List[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Rank European options to short")
    parser.add_argument("--tickers", nargs="*", help="Tickers to evaluate (Yahoo format)")
    parser.add_argument("--top", type=int, default=20, help="Top options per ticker to return")
    parser.add_argument("--out", default="tools/ranked_options.csv", help="CSV output path")
    args = parser.parse_args(argv)

    tickers = args.tickers or []
    if not tickers:
        print("Please pass tickers to evaluate, e.g., --tickers ASML.AS SAP.DE", file=sys.stderr)
        return 2

    all_rows: List[OptionRow] = []
    for t in tickers:
        print(f"Processing {t}...", file=sys.stderr)
        out = rank_options_for_ticker(t, top_n=args.top)
        all_rows.extend(out)

    # write CSV
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ticker", "expiry", "type", "strike", "last", "bid", "ask", "mid", "iv", "hv", "extrinsic", "theta"])
        for r in all_rows:
            w.writerow([r.ticker, r.expiry, r.option_type, r.strike, r.last_price, r.bid, r.ask, r.mid, r.iv, r.hv, r.extrinsic, r.theta])

    print(f"Wrote {len(all_rows)} option rows to {args.out}")
    # print top 20 overall
    all_rows_sorted = sorted(all_rows, key=lambda x: (x.iv or 0.0), reverse=True)
    for r in all_rows_sorted[:20]:
        print(f"{r.ticker} {r.expiry} {r.option_type} K={r.strike} mid={r.mid:.2f} iv={r.iv:.3f} hv={r.hv:.3f} extr={r.extrinsic:.2f} theta={r.theta}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
