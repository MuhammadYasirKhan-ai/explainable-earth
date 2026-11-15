"""Streamlit UI: trend, backtested forecast and 'who drives it?' explanation.

SI-use acknowledgment: this code was written with AI assistance (Claude by Anthropic).
"""

from __future__ import annotations

import logging

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from explainable_earth.data import (
    BAND_COLUMNS,
    NASA_ZONAL_URL,
    SERIES_COLUMNS,
    ZonalDataset,
    load_zonal,
    refresh_from_nasa,
)
from explainable_earth.explain import (
    narrative,
    period_rates,
    regional_contributions,
    weighted_global_slope,
)
from explainable_earth.model import (
    backtest,
    fit_linear_trend,
    forecast_trend,
    rolling_trend,
    window_label,
)

logger = logging.getLogger(__name__)
LABELS = {"Glob": "Global", "NHem": "Northern Hemisphere", "SHem": "Southern Hemisphere"}


@st.cache_data(show_spinner=False)
def _load() -> ZonalDataset:
    return load_zonal()


def _trend_tab(frame: pd.DataFrame, series: str, horizon: int) -> None:
    years, vals = frame["Year"], frame[series]
    bt = backtest(years, vals)
    window = bt.best_window
    fit = fit_linear_trend(years[years >= 1980], vals[years >= 1980])
    fc = forecast_trend(years, vals, horizon, window)

    fig = go.Figure()
    fig.add_scatter(x=years, y=vals, mode="markers+lines", name="NASA GISTEMP annual", line={"width": 1})
    fig.add_scatter(x=fc.years, y=fc.mean, name=f"Forecast ({window_label(window)})", line={"dash": "dash"})
    fig.add_scatter(x=fc.years, y=fc.upper, line={"width": 0}, showlegend=False, hoverinfo="skip")
    fig.add_scatter(
        x=fc.years,
        y=fc.lower,
        fill="tonexty",
        line={"width": 0},
        name="95% prediction band",
        fillcolor="rgba(255,127,14,0.2)",
    )
    fig.update_layout(yaxis_title="Anomaly vs 1951-1980 (C)", xaxis_title="Year", height=430)
    st.plotly_chart(fig)

    c1, c2, c3 = st.columns(3)
    c1.metric(
        "Trend since 1980",
        f"{fit.slope_per_decade:.2f} C/decade",
        f"95% CI {fit.ci_low:.2f} to {fit.ci_high:.2f}",
        delta_color="off",
    )
    c2.metric(
        f"Forecast {int(fc.years[-1])}",
        f"{fc.mean[-1]:.2f} C",
        f"band {fc.lower[-1]:.2f} to {fc.upper[-1]:.2f}",
        delta_color="off",
    )
    c3.metric("Backtest skill vs baseline", f"{bt.skill * 100:.0f}%", f"{bt.horizon}-yr horizon", delta_color="off")

    with st.expander("Backtest: how good are the forecasts? (rolling origin, from 1950)"):
        table = pd.DataFrame({"MAE (C)": {**bt.mae_by_window, "baseline: mean of last 10 yrs": bt.baseline_mae}})
        st.dataframe(table.style.format("{:.3f}"))
        st.caption(
            f"The trend window with the lowest error ({window_label(window)}) is used for the forecast. "
            "Linear extrapolation cannot anticipate volcanoes, El Nino or policy changes."
        )

    ends, slopes = rolling_trend(years, vals, 30)
    roll = go.Figure(go.Scatter(x=ends, y=slopes, mode="lines"))
    roll.update_layout(
        title="Is warming accelerating? Trend of every 30-year window",
        yaxis_title="C per decade",
        xaxis_title="Window end year",
        height=320,
    )
    st.plotly_chart(roll)


def _explain_tab(frame: pd.DataFrame, start_year: int) -> None:
    for line in narrative(frame, start_year):
        st.markdown(f"- {line}")
    contrib = regional_contributions(frame, start_year)

    left, right = st.columns(2)
    bar = go.Figure(
        go.Bar(
            x=contrib["band"],
            y=contrib["slope_per_decade"],
            error_y={
                "type": "data",
                "symmetric": False,
                "array": contrib["ci_high"] - contrib["slope_per_decade"],
                "arrayminus": contrib["slope_per_decade"] - contrib["ci_low"],
            },
        )
    )
    bar.update_layout(title="Warming rate by latitude band (C/decade, 95% CI)", height=360)
    left.plotly_chart(bar)

    share = go.Figure()
    share.add_bar(x=contrib["band"], y=contrib["area_share"] * 100, name="Share of Earth's area (%)")
    share.add_bar(x=contrib["band"], y=contrib["contribution_share"] * 100, name="Share of global warming (%)")
    share.update_layout(barmode="group", title="Area vs contribution to the global trend", height=360)
    right.plotly_chart(share)

    heat = frame.set_index("Year")[list(BAND_COLUMNS)].T
    hm = go.Figure(
        go.Heatmap(z=heat.values, x=heat.columns, y=heat.index, colorscale="RdBu_r", zmid=0, colorbar={"title": "C"})
    )
    hm.update_layout(title="Temperature anomaly by latitude band and year", height=380)
    st.plotly_chart(hm)
    st.caption(
        f"Contributions are exact: global trend = sum(area share x band trend) = "
        f"{weighted_global_slope(contrib):.3f} C/decade."
    )


def main() -> None:
    st.set_page_config(page_title="Explainable Earth", page_icon="🌍", layout="wide")
    st.title("🌍 Explainable Earth")
    st.caption("Explainable trend detection on NASA GISS surface temperature data (GISTEMP v4).")

    with st.sidebar:
        st.header("Controls")
        series = st.selectbox(
            "Series", [*SERIES_COLUMNS, *BAND_COLUMNS], format_func=lambda s: LABELS.get(s, f"Latitude band {s}")
        )
        horizon = st.slider("Forecast horizon (years)", 5, 30, 10)
        start_year = st.slider("Explain trend since", 1900, 2000, 1980, step=10)
        if st.button("Refresh from NASA"):
            try:
                refresh_from_nasa()
                _load.clear()
                st.success("Loaded the latest NASA file.")
            except Exception as exc:  # noqa: BLE001 - surface any network/parse failure to the user
                logger.warning("Refresh failed: %s", exc)
                st.error(f"Could not refresh from NASA ({type(exc).__name__}). Using the existing data.")

    ds = _load()
    st.info(f"Data: {ds.source}, {ds.first_year}-{ds.last_year}. Source: {NASA_ZONAL_URL}")
    tab1, tab2, tab3 = st.tabs(["Trend and forecast", "Who drives the trend?", "Method and SI use"])
    with tab1:
        _trend_tab(ds.frame, series, horizon)
    with tab2:
        _explain_tab(ds.frame, start_year)
    with tab3:
        early, late = period_rates(ds.frame, start_year)
        st.markdown(
            "**Method.** OLS trends with an autocorrelation-adjusted 95% CI; forecasts are linear extrapolations "
            "whose fitting window is chosen by a rolling-origin backtest against a naive baseline. The explanation "
            "splits the global trend exactly into area-weighted latitude-band contributions.\n\n"
            f"Rates: before {start_year} = {early:.2f}, from {start_year} = {late:.2f} C/decade.\n\n"
            "**Limits.** Surface temperature only; no causal attribution; linear extrapolation.\n\n"
            "**SI use.** Code and text were written with AI assistance (Claude by Anthropic) and reviewed by the team. "
            "No AI-generated imagery, audio or NASA branding is used.\n\n"
            "**Data.** NASA GISS GISTEMP v4 zonal annual means."
        )


if __name__ == "__main__":
    main()
