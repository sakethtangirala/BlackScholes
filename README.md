# Black–Scholes Options Pricer

A simple Python CLI to compute European option prices and Greeks using the Black–Scholes model.

- Supports call and put options
- Supports continuous dividend yield (q)
- Outputs price and optional Greeks (delta, gamma, theta, vega, rho)

## Usage

From the project root:

- Run as a module:
  python -m bs_pricer --type call --S 100 --K 100 --r 0.05 --sigma 0.2 --T 1 --show-greeks

- Or import and use in Python:
  from bs_pricer.black_scholes import black_scholes_price, greeks
  price = black_scholes_price("call", 100, 100, 0.05, 0.2, 1, 0.0)

Arguments:
- --type: call or put
- --S: spot price (>0)
- --K: strike price (>0)
- --r: risk-free rate (annual decimal)
- --sigma: volatility (annual decimal)
- --T: time to maturity in years (>0)
- --q: dividend yield (annual decimal, default 0)
- --show-greeks: include Greeks in output

## Project Layout
- src/bs_pricer/black_scholes.py: Pricing and Greeks
- src/bs_pricer/cli.py: CLI entrypoint
- src/bs_pricer/__main__.py: Enables `python -m bs_pricer`
- tests/test_black_scholes.py: Basic unit tests
