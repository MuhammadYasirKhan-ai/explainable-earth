from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).parent.parent / "streamlit_app.py")


def test_app_renders_without_exceptions() -> None:
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    assert at.title[0].value.endswith("Explainable Earth")
    assert len(at.tabs) == 3


def test_app_handles_band_series_selection() -> None:
    at = AppTest.from_file(APP, default_timeout=60).run()
    at.sidebar.selectbox[0].select("64N-90N").run()
    assert not at.exception
