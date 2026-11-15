"""Explain a global trend by decomposing it into area-weighted latitude-band contributions.

Global mean = sum_b w_b * mean_b where w_b is the band's share of Earth's surface.
Because the OLS slope is linear in the data, the global slope is the same weighted sum
of band slopes, so each band's contribution is exact, not an approximation.

SI-use acknowledgment: this code was written with AI assistance (Claude by Anthropic).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

from explainable_earth.model import fit_linear_trend


@dataclass(frozen=True)
class Band:
    name: str
    lat_low: float
    lat_high: float


BANDS: tuple[Band, ...] = (
    Band("64N-90N", 64, 90),
    Band("44N-64N", 44, 64),
    Band("24N-44N", 24, 44),
    Band("EQU-24N", 0, 24),
    Band("24S-EQU", -24, 0),
    Band("44S-24S", -44, -24),
    Band("64S-44S", -64, -44),
    Band("90S-64S", -90, -64),
)


def area_share(lat_low: float, lat_high: float) -> float:
    """Fraction of Earth's surface between two latitudes (spherical Earth)."""
    return abs(math.sin(math.radians(lat_high)) - math.sin(math.radians(lat_low))) / 2.0


def regional_contributions(frame: pd.DataFrame, start_year: int | None = None) -> pd.DataFrame:
    """Per-band trend, area share and exact contribution to the area-weighted global trend."""
    data = frame if start_year is None else frame[frame["Year"] >= start_year]
    rows: list[dict[str, float | str]] = []
    for band in BANDS:
        sub = data.dropna(subset=[band.name])
        fit = fit_linear_trend(sub["Year"], sub[band.name])
        share = area_share(band.lat_low, band.lat_high)
        rows.append(
            {
                "band": band.name,
                "area_share": share,
                "slope_per_decade": fit.slope_per_decade,
                "ci_low": fit.ci_low,
                "ci_high": fit.ci_high,
                "contribution": share * fit.slope_per_decade,
            }
        )
    out = pd.DataFrame(rows)
    total = float(out["contribution"].sum())
    out["contribution_share"] = out["contribution"] / total
    out["amplification"] = out["slope_per_decade"] / total
    return out


def weighted_global_slope(contrib: pd.DataFrame) -> float:
    return float(contrib["contribution"].sum())


def period_rates(frame: pd.DataFrame, split_year: int = 1980) -> tuple[float, float]:
    """Global trend (C/decade) before and from `split_year`."""
    early = frame[frame["Year"] < split_year]
    late = frame[frame["Year"] >= split_year]
    return (
        fit_linear_trend(early["Year"], early["Glob"]).slope_per_decade,
        fit_linear_trend(late["Year"], late["Glob"]).slope_per_decade,
    )


def narrative(frame: pd.DataFrame, start_year: int = 1980) -> list[str]:
    """Plain-language findings computed from the data (no hard-coded numbers)."""
    contrib = regional_contributions(frame, start_year)
    top = contrib.sort_values("amplification", ascending=False).iloc[0]
    big = contrib.sort_values("contribution_share", ascending=False).iloc[0]
    early, late = period_rates(frame, start_year)
    last_year = int(frame["Year"].iloc[-1])
    return [
        f"Since {start_year}, global surface temperature has risen "
        f"{weighted_global_slope(contrib):.2f} C per decade (before {start_year}: {early:.2f} C per decade; "
        f"from {start_year}: {late:.2f} C per decade), data through {last_year}.",
        f"The fastest-warming band is {top['band']}: {top['slope_per_decade']:.2f} C per decade, "
        f"{top['amplification']:.1f}x the global rate, while covering only "
        f"{top['area_share'] * 100:.0f}% of Earth's surface.",
        f"The largest absolute contribution comes from {big['band']}: "
        f"{big['contribution_share'] * 100:.0f}% of the global trend from "
        f"{big['area_share'] * 100:.0f}% of the area.",
    ]
