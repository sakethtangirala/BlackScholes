"""Diagnostic: check which tickers have option chains available via yfinance."""
from __future__ import annotations

import sys
from typing import List
import yfinance as yf


def check_tickers(tickers: List[str]):
    for t in tickers:
        print(f"Ticker: {t}")
        try:
            tk = yf.Ticker(t)
        except Exception as e:
            print(f"  Error creating Ticker: {e}")
            continue

        # last close
        try:
            hist = tk.history(period="1d")
            if not hist.empty and "Close" in hist.columns:
                print(f"  Last close: {hist['Close'].iloc[-1]}")
            else:
                print("  No recent close data")
        except Exception as e:
            print(f"  Error fetching history: {e}")

        # Try original ticker first, then fallbacks: base symbol (prefix before dot), then known ADR map
        tried = []
        def try_ticker(sym: str):
            try:
                tk2 = yf.Ticker(sym)
            except Exception as e:
                print(f"  Error creating Ticker {sym}: {e}")
                return False
            tried.append(sym)
            try:
                opts = tk2.options
                print(f"  Tried {sym}: expiries count: {len(opts)}")
                if opts:
                    print(f"  first expiries: {opts[:5]}")
                for e in (opts[:3] if opts else []):
                    try:
                        oc = tk2.option_chain(e)
                        calls = len(oc.calls) if hasattr(oc, "calls") else 0
                        puts = len(oc.puts) if hasattr(oc, "puts") else 0
                        print(f"    expiry {e}: calls={calls}, puts={puts}")
                    except Exception as ex:
                        print(f"    expiry {e}: error fetching chain: {ex}")
                return True
            except Exception as e:
                print(f"  Error retrieving options list for {sym}: {e}")
                return False

        ok = try_ticker(t)
        if not ok:
            # try base symbol before dot
            base = t.split(".")[0]
            if base and base != t:
                try_ticker(base)

        # manual ADR mapping for common European stocks -> US ticker
        adr_map = {
            "ASML.AS": "ASML",
            "SAP.DE": "SAP",
            "SAN.PA": "SAN",
            "NESN.SW": "NVS",
            "NOVN.SW": "NVS",
            "SHEL.L": "SHEL",
            "AIR.PA": "EADSY",
            "MC.PA": "LVMUY",
            "GLEN.L": "GLNCY",
        }
        if t in adr_map:
            try_ticker(adr_map[t])

        print(f"  tried symbols: {tried}")


if __name__ == "__main__":
    ticks = sys.argv[1:] or [
        "ASML.AS",
        "SAP.DE",
        "SAN.PA",
        "MC.PA",
        "SHEL.L",
        "GLEN.L",
        "NESN.SW",
        "NOVN.SW",
        "AIR.PA",
    ]
    check_tickers(ticks)
