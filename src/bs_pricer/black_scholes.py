import math

SQRT_2PI = math.sqrt(2 * math.pi)


def norm_cdf(x: float) -> float:
    """Standard normal CDF using math.erf."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / SQRT_2PI


def d1(S: float, K: float, r: float, sigma: float, T: float, q: float = 0.0) -> float:
    return (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))


def d2(S: float, K: float, r: float, sigma: float, T: float, q: float = 0.0) -> float:
    return d1(S, K, r, sigma, T, q) - sigma * math.sqrt(T)


def black_scholes_price(option_type: str, S: float, K: float, r: float, sigma: float, T: float, q: float = 0.0) -> float:
    """
    Black-Scholes price for European call/put with continuous dividend yield q.
    option_type: 'call' or 'put'
    """
    _d1 = d1(S, K, r, sigma, T, q)
    _d2 = _d1 - sigma * math.sqrt(T)
    if option_type.lower() == "call":
        return S * math.exp(-q * T) * norm_cdf(_d1) - K * math.exp(-r * T) * norm_cdf(_d2)
    elif option_type.lower() == "put":
        return K * math.exp(-r * T) * norm_cdf(-_d2) - S * math.exp(-q * T) * norm_cdf(-_d1)
    else:
        raise ValueError("option_type must be 'call' or 'put'")


def greeks(option_type: str, S: float, K: float, r: float, sigma: float, T: float, q: float = 0.0) -> dict:
    """
    Returns a dict of Greeks: delta, gamma, theta, vega, rho.
    All rates are annualized; T in years; sigma annual volatility.
    Theta is per year; vega per 1 vol (e.g., 0.01 = 1%).
    """
    _d1 = d1(S, K, r, sigma, T, q)
    _d2 = _d1 - sigma * math.sqrt(T)
    pdf_d1 = norm_pdf(_d1)

    if option_type.lower() == "call":
        delta = math.exp(-q * T) * norm_cdf(_d1)
        theta = (
            - (S * math.exp(-q * T) * pdf_d1 * sigma) / (2 * math.sqrt(T))
            - r * K * math.exp(-r * T) * norm_cdf(_d2)
            + q * S * math.exp(-q * T) * norm_cdf(_d1)
        )
        rho = K * T * math.exp(-r * T) * norm_cdf(_d2)
    elif option_type.lower() == "put":
        delta = -math.exp(-q * T) * norm_cdf(-_d1)
        theta = (
            - (S * math.exp(-q * T) * pdf_d1 * sigma) / (2 * math.sqrt(T))
            + r * K * math.exp(-r * T) * norm_cdf(-_d2)
            - q * S * math.exp(-q * T) * norm_cdf(-_d1)
        )
        rho = -K * T * math.exp(-r * T) * norm_cdf(-_d2)
    else:
        raise ValueError("option_type must be 'call' or 'put'")

    gamma = (math.exp(-q * T) * pdf_d1) / (S * sigma * math.sqrt(T))
    vega = S * math.exp(-q * T) * pdf_d1 * math.sqrt(T)

    return {
        "delta": delta,
        "gamma": gamma,
        "theta": theta,
        "vega": vega,
        "rho": rho,
    }
