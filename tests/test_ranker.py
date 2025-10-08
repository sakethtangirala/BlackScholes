import pandas as pd
import numpy as np

from tools import stock_ranker as sr


def test_compute_metrics_basic():
    # create 252 trading days of synthetic prices
    rng = pd.date_range(end=pd.Timestamp.today(), periods=252, freq='B')
    prices = pd.Series(np.linspace(100, 120, len(rng)), index=rng)
    m = sr.compute_metrics(prices)
    assert "1y_return" in m and "6m_return" in m and "ann_vol" in m
    assert m["1y_return"] > 0


def test_score_metrics():
    m = {"1y_return": 0.2, "6m_return": 0.1, "ann_vol": 0.15, "dividend_yield": 0.02}
    w = {"1y": 0.4, "6m": 0.3, "vol": 0.2, "div": 0.1}
    s = sr.score_metrics(m, w)
    assert isinstance(s, float)
    # higher return should yield positive score
    assert s > 0
