import pytest

from explainable_earth.data import load_zonal
from explainable_earth.explain import (
    BANDS,
    area_share,
    narrative,
    period_rates,
    regional_contributions,
    weighted_global_slope,
)
from explainable_earth.model import fit_linear_trend


def test_area_shares_sum_to_one() -> None:
    assert sum(area_share(b.lat_low, b.lat_high) for b in BANDS) == pytest.approx(1.0)


def test_contribution_shares_sum_to_one() -> None:
    contrib = regional_contributions(load_zonal().frame, 1980)
    assert contrib["contribution_share"].sum() == pytest.approx(1.0)


def test_decomposition_matches_published_global_series() -> None:
    frame = load_zonal().frame
    contrib = regional_contributions(frame, 1980)
    recent = frame[frame["Year"] >= 1980]
    published = fit_linear_trend(recent["Year"], recent["Glob"]).slope_per_decade
    assert weighted_global_slope(contrib) == pytest.approx(published, abs=0.02)


def test_arctic_amplification_detected() -> None:
    contrib = regional_contributions(load_zonal().frame, 1980).set_index("band")
    assert contrib.loc["64N-90N", "amplification"] > 2.0


def test_warming_accelerated() -> None:
    early, late = period_rates(load_zonal().frame, 1980)
    assert late > 2 * early


def test_narrative_mentions_fastest_band() -> None:
    lines = narrative(load_zonal().frame)
    assert len(lines) == 3 and "64N-90N" in lines[1]
