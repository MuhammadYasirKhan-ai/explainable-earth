import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from explainable_earth.model import (
    backtest,
    fit_linear_trend,
    forecast_trend,
    rolling_trend,
)

YEARS = np.arange(1900, 2021, dtype=float)


def _series(slope_decade: float, noise: float = 0.05, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return 0.1 + slope_decade / 10 * (YEARS - 1900) + rng.normal(0, noise, YEARS.size)


def test_slope_recovered_and_ci_contains_truth() -> None:
    fit = fit_linear_trend(YEARS, _series(0.12))
    assert fit.slope_per_decade == pytest.approx(0.12, abs=0.01)
    assert fit.ci_low < 0.12 < fit.ci_high
    assert 0.0 <= fit.r_squared <= 1.0


def test_perfect_line_has_zero_width_ci() -> None:
    fit = fit_linear_trend(YEARS, 0.02 * (YEARS - 1900))
    assert fit.slope_per_decade == pytest.approx(0.2)
    assert fit.ci_high - fit.ci_low < 1e-6


def test_forecast_band_widens_and_brackets_mean() -> None:
    fc = forecast_trend(YEARS, _series(0.1), horizon=15, window=40)
    width = fc.upper - fc.lower
    assert np.all(fc.lower < fc.mean) and np.all(fc.mean < fc.upper)
    assert width[-1] > width[0]
    assert fc.years[0] == 2021


def test_backtest_prefers_recent_window_when_trend_changes() -> None:
    y = np.where(YEARS < 1970, 0.0, 0.03 * (YEARS - 1970))
    y = y + np.random.default_rng(1).normal(0, 0.03, YEARS.size)
    res = backtest(YEARS, y, first_origin_year=1950)
    assert res.best_window in (30, 50)
    assert res.mae_by_window["last 30 yrs"] < res.mae_by_window["all years"]


def test_rolling_trend_shape() -> None:
    ends, slopes = rolling_trend(YEARS, _series(0.1), 30)
    assert ends.size == slopes.size == YEARS.size - 29
    assert ends[-1] == 2020


@pytest.mark.parametrize("bad", [np.array([1.0, 2.0]), np.array([np.nan] * 10)])
def test_invalid_inputs_rejected(bad: np.ndarray) -> None:
    with pytest.raises(ValueError):
        fit_linear_trend(np.arange(bad.size, dtype=float), bad)


def test_bad_horizon_rejected() -> None:
    with pytest.raises(ValueError):
        forecast_trend(YEARS, _series(0.1), horizon=0)


@settings(max_examples=40, deadline=None)
@given(slope=st.floats(-0.5, 0.5), offset=st.floats(-2, 2))
def test_slope_is_translation_invariant(slope: float, offset: float) -> None:
    base = slope / 10 * (YEARS - 1900)
    a = fit_linear_trend(YEARS, base).slope_per_decade
    b = fit_linear_trend(YEARS, base + offset).slope_per_decade
    assert a == pytest.approx(b, abs=1e-9)


def test_misc_validation_errors() -> None:
    with pytest.raises(ValueError, match="equal length"):
        fit_linear_trend(np.arange(6.0), np.arange(7.0))
    with pytest.raises(ValueError, match="window"):
        rolling_trend(YEARS, _series(0.1), 5)
    with pytest.raises(ValueError, match="Not enough"):
        backtest(YEARS[:30], _series(0.1)[:30])
