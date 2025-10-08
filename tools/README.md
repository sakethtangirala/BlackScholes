European Stock Ranker
=====================

This simple tool fetches historical price data from Yahoo Finance (via `yfinance`) and ranks a list of European tickers using a small set of metrics.

Usage
-----

1. Install dependencies (use a virtualenv):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate; pip install -r tools\requirements.txt
```

2. Run the ranker (defaults used if no tickers provided):

```powershell
python tools\stock_ranker.py --top 10
```

3. Provide custom tickers or weights:

```powershell
python tools\stock_ranker.py --tickers ASML.AS SAP.DE MC.PA --weights "1y=0.5,6m=0.3,vol=0.15,div=0.05"
```

Notes
-----
- This is a data-driven helper, not investment advice.
- The script uses `yfinance` and therefore requires internet access.
- For production use, expand the universe and add error handling, caching, and tests.
