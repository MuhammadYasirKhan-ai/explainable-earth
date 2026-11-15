# 🌍 Explainable Earth

**NASA Space Apps Challenge 2026, Islamabad. Challenge: Be An Earth System Trend Detective!**

Explainable trend detection on NASA GISS surface temperature data. The app answers three questions:

1. **What is the trend?** OLS trend with an autocorrelation-adjusted 95% confidence interval.
2. **What happens next, and can we trust it?** A linear forecast whose fitting window (30 yrs, 50 yrs, all years) is chosen by a
   rolling-origin backtest against a naive baseline, so the skill score is honest.
3. **Who drives it?** The global trend is split *exactly* into area-weighted latitude-band contributions, showing that the
   Arctic (64N-90N) warms about 3.5x faster than the global average while covering about 5% of Earth's surface.

**Live demo:** [add your https://....streamlit.app link here]  |  **Deploy guide:** see `DEPLOY.md`

## NASA data

NASA GISS Surface Temperature Analysis (GISTEMP v4), zonal annual means (anomalies vs 1951-1980):
https://data.giss.nasa.gov/gistemp/tabledata_v4/ZonAnn.Ts+dSST.csv

The repository bundles a snapshot (1880-2022) so the app runs offline. Click **Refresh from NASA** in the sidebar, or run
`python -m explainable_earth.data --refresh`, to download and validate the latest file.

## Run

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py          # open http://localhost:8501
```

Docker: `docker build -t explainable-earth . && docker run -p 8501:8501 explainable-earth`

## Develop

```bash
pip install -e ".[dev]"
ruff check . && ruff format --check . && mypy && pytest --cov=explainable_earth
```

26 tests, about 96% coverage, `mypy --strict` and ruff clean. Property-based tests use Hypothesis.

## Layout

```
src/explainable_earth/
  data.py     load, validate, cache and refresh NASA data
  model.py    trend + CI, forecast + prediction band, backtest, rolling trend
  explain.py  area-weighted latitude-band decomposition, plain-language findings
  app.py      Streamlit UI
tests/        pytest + hypothesis + Streamlit AppTest
```

## Limitations

Linear extrapolation cannot anticipate volcanoes, El Nino or policy changes. Surface temperature only, and the
decomposition is descriptive, not causal attribution.

## SI-use acknowledgment

The code, tests and documentation were written with AI assistance (Claude by Anthropic) and run and reviewed by the team.
No AI-generated images, audio or video and no NASA branding are used in this project.
