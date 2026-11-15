import pytest

from explainable_earth.data import (
    BUNDLED_PATH,
    DataValidationError,
    load_zonal,
    parse_zonal_csv,
)


def test_bundled_dataset_loads() -> None:
    ds = load_zonal(BUNDLED_PATH)
    assert ds.first_year == 1880
    assert ds.last_year >= 2022
    assert len(ds.frame) >= 140
    assert ds.frame["Glob"].notna().all()


def test_missing_markers_and_partial_year_handled() -> None:
    text = BUNDLED_PATH.read_text(encoding="utf-8").rstrip("\n")
    text += "\n2023,***,***,***,***,***,***,***,***,***,***,***,***,***,***\n"
    frame = parse_zonal_csv(text)
    assert int(frame["Year"].iloc[-1]) <= 2022


def test_missing_columns_rejected() -> None:
    with pytest.raises(DataValidationError, match="Missing required columns"):
        parse_zonal_csv("Year,Glob\n1880,.1\n")


def test_too_short_rejected() -> None:
    header = BUNDLED_PATH.read_text(encoding="utf-8").splitlines()[:11]
    with pytest.raises(DataValidationError, match="at least"):
        parse_zonal_csv("\n".join(header))


def test_implausible_values_rejected() -> None:
    lines = BUNDLED_PATH.read_text(encoding="utf-8").splitlines()
    lines[5] = lines[5].replace(lines[5].split(",")[1], "99.9", 1)
    with pytest.raises(DataValidationError, match="plausible"):
        parse_zonal_csv("\n".join(lines))


def test_refresh_downloads_validates_and_caches(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    import io

    from explainable_earth import data

    payload = BUNDLED_PATH.read_bytes()
    monkeypatch.setattr(data, "CACHE_PATH", tmp_path / "cache" / "zon.csv")
    monkeypatch.setattr(data, "urlopen", lambda *_a, **_k: io.BytesIO(payload))
    ds = data.refresh_from_nasa()
    assert ds.source.startswith("NASA GISS download")
    assert (tmp_path / "cache" / "zon.csv").exists()
    cached = data.load_zonal()
    assert "cached" in cached.source


def test_load_falls_back_to_bundled_when_no_cache(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    from explainable_earth import data

    monkeypatch.setattr(data, "CACHE_PATH", tmp_path / "missing.csv")
    assert "bundled" in data.load_zonal().source


def test_unparseable_csv_rejected() -> None:
    with pytest.raises(DataValidationError):
        parse_zonal_csv("")
