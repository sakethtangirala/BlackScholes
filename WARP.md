# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

Project: Black–Scholes Options Pricer (Python)

Common commands (PowerShell on Windows)
- One-time per session, set Python path for src-layout:
  $env:PYTHONPATH = "src"

- Run the CLI (module mode):
  python -m bs_pricer --type call --S 100 --K 100 --r 0.05 --sigma 0.2 --T 1 --q 0 --show-greeks

- Run all tests (unittest):
  python -m unittest discover -s tests -v

- Run a single test:
  python -m unittest tests.test_black_scholes.TestBlackScholes.test_call_price_no_dividend

Notes
- src-layout: The package lives under src/bs_pricer. Ensure PYTHONPATH includes src for imports and python -m bs_pricer to work during local dev.
- No dedicated build/lint tooling or packaging config is present. Testing uses Python’s built-in unittest, and tests bootstrap sys.path to include src.

High-level architecture
- Package bs_pricer
  - black_scholes.py: Core math for Black–Scholes pricing and Greeks.
    - norm_cdf/norm_pdf: standard normal functions (math.erf-based CDF)
    - d1/d2: intermediary terms
    - black_scholes_price(option_type, S, K, r, sigma, T, q): price for European call/put with continuous dividend yield q
    - greeks(...): returns dict with delta, gamma, theta, vega, rho
  - cli.py: Argument parsing and user interface.
    - Validates inputs (positive/nonnegative), calls pricing/greeks, prints results
  - __main__.py: Enables python -m bs_pricer by delegating to cli.main()
- Tests
  - tests/test_black_scholes.py: unittest-based checks for known prices and greeks presence; temporarily inserts src on sys.path for imports

Key usage from README
- Example run (requires PYTHONPATH=src set):
  python -m bs_pricer --type call --S 100 --K 100 --r 0.05 --sigma 0.2 --T 1 --show-greeks
- Import usage:
  from bs_pricer.black_scholes import black_scholes_price, greeks
  price = black_scholes_price("call", 100, 100, 0.05, 0.2, 1, 0.0)

Environment assumptions
- Python 3.x available on PATH.
- Windows/PowerShell examples above; adapt environment variable syntax if using a different shell.
