# NASA Space Apps 2026: submission text (paste into the form)

## Project name
Explainable Earth

## Summary (about 150 words)
Explainable Earth is an interactive tool that detects, forecasts and explains trends in NASA Earth observation data. Using
NASA GISS GISTEMP v4 zonal temperature anomalies (1880-2022), it estimates the warming trend with an honest confidence
interval, forecasts the next decade with a prediction band, and, most importantly, explains where the warming comes from.
Because the global trend is an area-weighted sum of latitude-band trends, we split it exactly into per-band contributions.
The result: since 1980 the world warmed about 0.19 C per decade, and the Arctic (64N-90N) warmed about 0.66 C per decade,
roughly 3.5 times the global rate, from only 5% of Earth's surface. A rolling-origin backtest picks the forecast window and
reports skill against a naive baseline, so users can see how far to trust it. The app makes climate trends transparent
and checkable for students, journalists and decision-makers.

## Project Details
**What it does.** Loads NASA GISTEMP v4 zonal annual anomalies. Tab 1 shows the series, a 30-year-window trend with 95% CI, a
10-30 year forecast with a 95% prediction band, a backtest table and a rolling 30-year trend showing acceleration
(about 0.04 C per decade before 1980 vs 0.19 C per decade after). Tab 2 explains the trend: warming rate per latitude band,
area share vs share of warming, and a latitude-year heatmap. Tab 3 documents method, limits and SI use.

**How it works.** OLS trend with a CI that accounts for lag-1 residual autocorrelation; linear forecast with a
prediction interval; rolling-origin backtest (from 1950, 10-year horizon) comparing 30-year, 50-year and all-year windows
against a "mean of last 10 years" baseline (best window: last 30 years, about 31% lower error than baseline);
exact decomposition global slope = sum(area share x band slope), validated against NASA's own global series (0.188 vs 0.190 C per decade).

**Impact.** Makes the "why" behind climate trends visible and checkable, supporting education and evidence-based discussion.

**Tools.** Python 3.12, pandas, NumPy, SciPy, Plotly, Streamlit; pytest, Hypothesis, ruff, mypy (strict); Docker.

**Creativity.** The explainability layer: an exact, auditable decomposition instead of a black box, plus an honest backtest.

**Limitations.** Linear extrapolation; surface temperature only; descriptive, not causal.

## Use of SI
Select: code, and text/documentation written with AI assistance (Claude by Anthropic). Tick "image/video/audio" only if you
add AI-generated media (for example an AI-made logo; then add a visible SI watermark).

## NASA Data (Link Text / Link URL)
- NASA GISS Surface Temperature Analysis (GISTEMP v4), zonal annual means | https://data.giss.nasa.gov/gistemp/tabledata_v4/ZonAnn.Ts+dSST.csv
- NASA GISS GISTEMP v4 main page | https://data.giss.nasa.gov/gistemp/

## Space Agency Partner & Other Data (Link Text / Link URL)
- TidyTuesday copy of GISTEMP zonal means (bundled snapshot) | https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data/2023/2023-07-11/zonann_temps.csv
- Python libraries: pandas, NumPy, SciPy, Plotly, Streamlit (open source) | https://pypi.org/
- Project code | [YOUR GITHUB REPO URL]

## 7-slide demo outline (or 30-second video)
1. Title: Explainable Earth, team name, challenge
2. The question: "Not just *that* it's warming, but *where from*?"
3. Data: NASA GISTEMP v4 zonal means, 1880-present
4. Trend + forecast chart with the backtest skill number
5. Explanation: area share vs share of warming bar chart (Arctic about 3.5x)
6. Acceleration: rolling 30-year trend chart
7. Impact, limits, SI-use acknowledgment, repo link
