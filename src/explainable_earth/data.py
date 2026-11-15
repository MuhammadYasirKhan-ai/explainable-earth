"""Load, validate and refresh NASA GISTEMP v4 zonal annual temperature anomalies.

Source: NASA GISS Surface Temperature Analysis (GISTEMP v4), zonal annual means,
anomalies in degrees C relative to the 1951-1980 base period.

SI-use acknowledgment: this code was written with AI assistance (Claude by Anthropic).
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd

logger = logging.getLogger(__name__)

NASA_ZONAL_URL = "https://data.giss.nasa.gov/gistemp/tabledata_v4/ZonAnn.Ts+dSST.csv"
BUNDLED_PATH = Path(__file__).parent / "data" / "ZonAnn.Ts+dSST.csv"
CACHE_PATH = Path.home() / ".cache" / "explainable_earth" / "ZonAnn.Ts+dSST.csv"

SERIES_COLUMNS: tuple[str, ...] = ("Glob", "NHem", "SHem")
BAND_COLUMNS: tuple[str, ...] = (
    "64N-90N",
    "44N-64N",
    "24N-44N",
    "EQU-24N",
    "24S-EQU",
    "44S-24S",
    "64S-44S",
    "90S-64S",
)
REQUIRED_COLUMNS: tuple[str, ...] = ("Year", *SERIES_COLUMNS, *BAND_COLUMNS)
MIN_YEARS = 50
_MISSING_MARKERS = ["***", "****", "*****", "-99.99", ""]


class DataValidationError(ValueError):
    """Raised when a dataset does not look like a GISTEMP zonal annual table."""


@dataclass(frozen=True)
class ZonalDataset:
    """Validated zonal dataset plus provenance."""

    frame: pd.DataFrame
    source: str

    @property
    def first_year(self) -> int:
        return int(self.frame["Year"].iloc[0])

    @property
    def last_year(self) -> int:
        return int(self.frame["Year"].iloc[-1])


def parse_zonal_csv(text: str) -> pd.DataFrame:
    """Parse and validate the text of a GISTEMP ZonAnn CSV file."""
    try:
        raw = pd.read_csv(io.StringIO(text), na_values=_MISSING_MARKERS)
    except (pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        raise DataValidationError(f"Cannot parse CSV: {exc}") from exc

    missing = [c for c in REQUIRED_COLUMNS if c not in raw.columns]
    if missing:
        raise DataValidationError(f"Missing required columns: {missing}")

    frame = raw.loc[:, list(REQUIRED_COLUMNS)].apply(pd.to_numeric, errors="coerce")
    frame = frame.dropna(subset=["Year", "Glob"]).reset_index(drop=True)
    frame["Year"] = frame["Year"].astype(int)

    if len(frame) < MIN_YEARS:
        raise DataValidationError(f"Need at least {MIN_YEARS} years, got {len(frame)}")
    if not frame["Year"].is_monotonic_increasing or frame["Year"].duplicated().any():
        raise DataValidationError("Years must be unique and increasing")
    values = frame.drop(columns="Year")
    if float(values.abs().max().max()) > 15.0:
        raise DataValidationError("Anomalies outside plausible range (|x| > 15 C)")
    return pd.DataFrame(frame)


def load_zonal(path: Path | None = None, *, prefer_cache: bool = True) -> ZonalDataset:
    """Load the dataset from an explicit path, the refreshed cache, or the bundled copy."""
    if path is not None:
        chosen, label = path, f"file:{path}"
    elif prefer_cache and CACHE_PATH.exists():
        chosen, label = CACHE_PATH, "NASA GISS download (cached)"
    else:
        chosen, label = BUNDLED_PATH, "bundled snapshot (NASA GISTEMP v4 via TidyTuesday mirror)"
    frame = parse_zonal_csv(chosen.read_text(encoding="utf-8"))
    logger.info("Loaded %d years from %s", len(frame), label)
    return ZonalDataset(frame=frame, source=label)


def refresh_from_nasa(url: str = NASA_ZONAL_URL, *, timeout: float = 30.0) -> ZonalDataset:
    """Download the latest zonal table from NASA GISS, validate it and cache it."""
    request = Request(url, headers={"User-Agent": "explainable-earth/1.0"})  # noqa: S310
    with urlopen(request, timeout=timeout) as response:  # noqa: S310
        text = response.read().decode("utf-8")
    frame = parse_zonal_csv(text)
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(text, encoding="utf-8")
    logger.info("Refreshed NASA data: %d years cached at %s", len(frame), CACHE_PATH)
    return ZonalDataset(frame=frame, source="NASA GISS download (fresh)")


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)
    ds = refresh_from_nasa() if "--refresh" in sys.argv else load_zonal()
    print(f"{ds.source}: {ds.first_year}-{ds.last_year}")
