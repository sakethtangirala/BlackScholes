import argparse
from .black_scholes import black_scholes_price, greeks


def positive_float(value: str) -> float:
    f = float(value)
    if f <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return f


def nonnegative_float(value: str) -> float:
    f = float(value)
    if f < 0:
        raise argparse.ArgumentTypeError("value must be non-negative")
    return f


def main():
    parser = argparse.ArgumentParser(description="Black–Scholes option pricer (European) with Greeks")
    parser.add_argument("--type", choices=["call", "put"], required=True, help="Option type")
    parser.add_argument("--S", type=positive_float, required=True, help="Spot price")
    parser.add_argument("--K", type=positive_float, required=True, help="Strike price")
    parser.add_argument("--r", type=float, required=True, help="Risk-free rate (annual, as decimal e.g. 0.05)")
    parser.add_argument("--sigma", type=positive_float, required=True, help="Volatility (annual, as decimal e.g. 0.2)")
    parser.add_argument("--T", type=positive_float, required=True, help="Time to maturity in years (e.g. 0.5)")
    parser.add_argument("--q", type=nonnegative_float, default=0.0, help="Dividend yield (annual, decimal)")
    parser.add_argument("--show-greeks", action="store_true", help="Also print Greeks")

    args = parser.parse_args()
    price = black_scholes_price(args.type, args.S, args.K, args.r, args.sigma, args.T, args.q)
    print(f"Price: {price:.6f}")

    if args.show_greeks:
        g = greeks(args.type, args.S, args.K, args.r, args.sigma, args.T, args.q)
        for k in ["delta", "gamma", "theta", "vega", "rho"]:
            print(f"{k.capitalize()}: {g[k]:.6f}")


if __name__ == "__main__":
    main()
