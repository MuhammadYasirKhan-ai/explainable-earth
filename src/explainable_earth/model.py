"""Trend estimation, honest backtested forecasting and rolling-trend analysis.

SI-use acknowledgment: this code was written with AI assistance (Claude by Anthropic).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
from scipy import stats

FloatArray = npt.NDArray[np.float64]

WINDOW_CANDIDATES: tuple[int | None, ...] = (30, 50, None)
BASELINE_YEARS = 10


@dataclass(frozen=True)
class TrendFit:
    """OLS trend with an autocorrelation-aware 95% interval."""

    slope_per_decade: float
    ci_low: float
    ci_high: float
    intercept: float
    r_squared: float
    start_year: int
    end_year: int
    n: int

    def predict(self, years: FloatArray) -> FloatArray:
        return self.intercept + (self.slope_per_decade / 10.0) * years


@dataclass(frozen=True)
class Forecast:
    years: FloatArray
    mean: FloatArray
    lower: FloatArray
    upper: FloatArray
    window: int | None


@dataclass(frozen=True)
class BacktestResult:
    mae_by_window: dict[str, float]
    baseline_mae: float
    best_window: int | None
    horizon: int

    @property
    def skill(self) -> float:
        """Relative MAE reduction versus the baseline (positive = better)."""
        best = self.mae_by_window[window_label(self.best_window)]
        return 1.0 - best / self.baseline_mae


def window_label(window: int | None) -> str:
    return "all years" if window is None else f"last {window} yrs"


def _as_arrays(years: npt.ArrayLike, values: npt.ArrayLike) -> tuple[FloatArray, FloatArray]:
    x = np.asarray(years, dtype=np.float64)
    y = np.asarray(values, dtype=np.float64)
    if x.shape != y.shape or x.ndim != 1:
        raise ValueError("years and values must be 1-D arrays of equal length")
    if x.size < 5:
        raise ValueError("At least 5 observations are required")
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("Inputs must be finite")
    return x, y


def fit_linear_trend(years: npt.ArrayLike, values: npt.ArrayLike) -> TrendFit:
    """Fit y = a + b*year. The CI shrinks the sample size by lag-1 residual autocorrelation."""
    x, y = _as_arrays(years, values)
    n = x.size
    xc = x - x.mean()
    sxx = float(np.sum(xc**2))
    slope = float(np.sum(xc * (y - y.mean())) / sxx)
    intercept = float(y.mean() - slope * x.mean())
    resid = y - (intercept + slope * x)
    ss_res = float(np.sum(resid**2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))

    r1 = float(np.corrcoef(resid[:-1], resid[1:])[0, 1]) if np.std(resid) > 0 else 0.0
    n_eff = max(4.0, n * (1 - r1) / (1 + r1)) if r1 > 0 else float(n)
    s2 = ss_res / (n - 2)
    se = float(np.sqrt(s2 / sxx * (n / n_eff)))
    t_crit = float(stats.t.ppf(0.975, df=n_eff - 2))
    return TrendFit(
        slope_per_decade=slope * 10.0,
        ci_low=(slope - t_crit * se) * 10.0,
        ci_high=(slope + t_crit * se) * 10.0,
        intercept=intercept,
        r_squared=1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0,
        start_year=int(x[0]),
        end_year=int(x[-1]),
        n=n,
    )


def forecast_trend(
    years: npt.ArrayLike,
    values: npt.ArrayLike,
    horizon: int,
    window: int | None = None,
) -> Forecast:
    """Extrapolate a linear trend fitted on the last `window` years with a 95% prediction band."""
    if horizon < 1:
        raise ValueError("horizon must be >= 1")
    x, y = _as_arrays(years, values)
    if window is not None:
        x, y = x[-window:], y[-window:]
    n = x.size
    fit = fit_linear_trend(x, y)
    resid = y - fit.predict(x)
    s = float(np.sqrt(np.sum(resid**2) / (n - 2)))
    sxx = float(np.sum((x - x.mean()) ** 2))
    future = np.arange(x[-1] + 1, x[-1] + 1 + horizon, dtype=np.float64)
    mean = fit.predict(future)
    t_crit = float(stats.t.ppf(0.975, df=n - 2))
    half = t_crit * s * np.sqrt(1 + 1 / n + (future - x.mean()) ** 2 / sxx)
    return Forecast(years=future, mean=mean, lower=mean - half, upper=mean + half, window=window)


def backtest(
    years: npt.ArrayLike,
    values: npt.ArrayLike,
    *,
    horizon: int = 10,
    first_origin_year: int = 1950,
    step: int = 2,
) -> BacktestResult:
    """Rolling-origin backtest of trend windows against a 'mean of last 10 years' baseline."""
    x, y = _as_arrays(years, values)
    errors: dict[int | None, list[float]] = {w: [] for w in WINDOW_CANDIDATES}
    baseline: list[float] = []
    origins = [i for i in range(x.size - horizon) if x[i] >= first_origin_year][::step]
    if not origins:
        raise ValueError("Not enough data for the requested backtest")
    for i in origins:
        actual = y[i + 1 : i + 1 + horizon]
        recent_mean = float(np.mean(y[max(0, i + 1 - BASELINE_YEARS) : i + 1]))
        baseline.append(float(np.mean(np.abs(actual - recent_mean))))
        for w in WINDOW_CANDIDATES:
            fc = forecast_trend(x[: i + 1], y[: i + 1], horizon, w)
            errors[w].append(float(np.mean(np.abs(actual - fc.mean))))
    mae = {window_label(w): float(np.mean(e)) for w, e in errors.items()}
    best = min(WINDOW_CANDIDATES, key=lambda w: mae[window_label(w)])
    return BacktestResult(mae_by_window=mae, baseline_mae=float(np.mean(baseline)), best_window=best, horizon=horizon)


def rolling_trend(years: npt.ArrayLike, values: npt.ArrayLike, window: int = 30) -> tuple[FloatArray, FloatArray]:
    """Trend (C/decade) of every `window`-year span, indexed by the span's last year."""
    x, y = _as_arrays(years, values)
    if window < 10 or window > x.size:
        raise ValueError("window must be between 10 and the series length")
    ends = x[window - 1 :]
    slopes = np.array(
        [fit_linear_trend(x[i : i + window], y[i : i + window]).slope_per_decade for i in range(x.size - window + 1)]
    )
    return ends, slopes
