"""Rolling beta × locked-sign shock. Causal through close(t); macro already as-of lagged."""
from __future__ import print_function

import numpy as np

from research_engine.cn_a_share_strategy_v14_1.scores import daily_return


def _window(c, lookback):
    out = np.empty_like(c, dtype=np.float64)
    out[: lookback - 1] = np.nan
    out[lookback - 1 :] = c[lookback - 1 :]
    if lookback < c.shape[0]:
        out[lookback:] = c[lookback:] - c[:-lookback]
    return out


def rolling_beta_block(y, x, lookback):
    """y (T,K), x (T,). Window ends at t. Requires lookback finite pairs."""
    t, k = y.shape
    valid_x = np.isfinite(x)
    valid_y = np.isfinite(y)
    both = valid_y & valid_x[:, None]
    x0 = np.where(valid_x, x, 0.0)
    y0 = np.where(both, y, 0.0)
    x_rep = np.where(both, x0[:, None], 0.0)
    x2_rep = np.where(both, (x0 * x0)[:, None], 0.0)
    xy = y0 * x0[:, None]
    sx = _window(np.cumsum(x_rep, axis=0), lookback)
    sx2 = _window(np.cumsum(x2_rep, axis=0), lookback)
    sy = _window(np.cumsum(y0, axis=0), lookback)
    sxy = _window(np.cumsum(xy, axis=0), lookback)
    cnt = _window(np.cumsum(both.astype(np.float64), axis=0), lookback)
    L = float(lookback)
    var_x = sx2 / L - (sx / L) ** 2
    cov = sxy / L - (sx / L) * (sy / L)
    beta = np.full((t, k), np.nan, dtype=np.float64)
    ok = (cnt == lookback) & (var_x > 1e-18)
    beta[ok] = cov[ok] / var_x[ok]
    return beta


def rolling_beta(y, x, lookback, chunk=400):
    t, n = y.shape
    out = np.full((t, n), np.nan, dtype=np.float64)
    for j0 in range(0, n, chunk):
        j1 = min(n, j0 + chunk)
        out[:, j0:j1] = rolling_beta_block(y[:, j0:j1], x, lookback)
    return out


def score_matrix(pack, shock, lookback, sign):
    close = np.array(pack["close"], dtype=np.float64)
    ret = daily_return(close)
    beta = rolling_beta(ret, shock, lookback)
    shock_2d = shock[:, None]
    out = sign * beta * shock_2d
    out[~np.isfinite(beta)] = np.nan
    out[~np.isfinite(shock)] = np.nan
    return out
