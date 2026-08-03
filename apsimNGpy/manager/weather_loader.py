"""Reliable acquisition, validation, and writing of APSIM weather files.

The module supports NASA POWER, Daymet, and Iowa Environmental Mesonet (IEM)
data.  Coordinates are always ordered ``(longitude, latitude)`` and daily
records use APSIM's ``year`` and one-based ``day`` (day of year) fields.

Network functions deliberately do not use ``functools.lru_cache``: they write
files and therefore are not pure.  Applications that need persistent caching
should cache downloaded responses or generated files explicitly.
"""

from __future__ import annotations

import logging
import math
import os
import secrets
import string
import tempfile
import time
from io import BytesIO
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable, Literal, Mapping, Sequence

import numpy as np
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

LOGGER = logging.getLogger(__name__)

APSIM_COLUMNS = ("year", "day", "radn", "maxt", "mint", "rain")
APSIM_UNITS = ("()", "()", "(MJ/m2/day)", "(oC)", "(oC)", "(mm)")
NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
DAYMET_URL = "https://daymet.ornl.gov/single-pixel/api/data"
IEM_COOP_URL = "https://mesonet.agron.iastate.edu/cgi-bin/request/coop.py"
IEM_NETWORK_URL = "https://mesonet.agron.iastate.edu/geojson/network/{network}.geojson"
NASA_PARAMETERS = (
    "T2M_MAX",
    "T2M_MIN",
    "ALLSKY_SFC_SW_DWN",
    "PRECTOTCORR",
)
NASA_MISSING = -999.0


class WeatherError(RuntimeError):
    """Base exception for weather acquisition and conversion errors."""


class WeatherDownloadError(WeatherError):
    """Raised when a remote weather service cannot provide usable data."""


class WeatherValidationError(WeatherError):
    """Raised when weather data violate required APSIM constraints."""


@dataclass(frozen=True)
class ValidationIssue:
    """One validation finding."""

    severity: Literal["error", "warning"]
    code: str
    message: str
    rows: tuple[int, ...] = ()


@dataclass
class ValidationReport:
    """Structured validation result suitable for logging or testing."""

    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == "warning"]

    def raise_for_errors(self) -> None:
        if self.errors:
            detail = "; ".join(issue.message for issue in self.errors)
            raise WeatherValidationError(detail)


@dataclass(frozen=True)
class MetDate:
    """Validated inclusive date interval.

    Strings are accepted in ``MM-DD-YYYY``, ``YYYY-MM-DD``, or any format
    understood unambiguously by :func:`pandas.Timestamp`.
    """

    start: date
    end: date

    def __init__(self, dates: Sequence[str | date | datetime | pd.Timestamp]):
        if len(dates) != 2:
            raise ValueError("dates must contain exactly a start and end date")
        start = _as_date(dates[0])
        end = _as_date(dates[1])
        if start > end:
            raise ValueError(f"start date {start} is after end date {end}")
        object.__setattr__(self, "start", start)
        object.__setattr__(self, "end", end)

    # Compatibility properties used by older apsimNGpy callers.
    @property
    def start_date(self) -> str:
        return self.start.strftime("%m-%d-%Y")

    @property
    def end_date(self) -> str:
        return self.end.strftime("%m-%d-%Y")

    @property
    def start_month(self) -> str:
        return str(self.start.month)

    @property
    def end_month(self) -> str:
        return str(self.end.month)

    @property
    def start_day(self) -> str:
        return str(self.start.day)

    @property
    def end_day(self) -> str:
        return str(self.end.day)

    @property
    def year_start(self) -> str:
        return str(self.start.year)

    @property
    def year_end(self) -> str:
        return str(self.end.year)


def _as_date(value: str | date | datetime | pd.Timestamp) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return pd.Timestamp(value).date()
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid date: {value!r}") from exc


def _validate_years(start: int, end: int, *, minimum: int | None = None) -> None:
    if isinstance(start, bool) or isinstance(end, bool):
        raise TypeError("start and end must be integer years")
    if int(start) != start or int(end) != end:
        raise TypeError("start and end must be integer years")
    if start > end:
        raise ValueError("start year must not exceed end year")
    if minimum is not None and start < minimum:
        raise ValueError(f"requested start year {start} precedes {minimum}")


def _validate_lonlat(lonlat: Sequence[float]) -> tuple[float, float]:
    if len(lonlat) != 2:
        raise ValueError("lonlat must contain (longitude, latitude)")
    lon, lat = map(float, lonlat)
    if not (-180.0 <= lon <= 180.0 and -90.0 <= lat <= 90.0):
        raise ValueError(f"invalid longitude/latitude: {(lon, lat)}")
    return lon, lat


def _session(retries: int = 3, backoff: float = 0.5) -> requests.Session:
    """Return a session that retries transient HTTP failures."""

    if retries < 0:
        raise ValueError("retries must be non-negative")
    policy = Retry(
        total=retries,
        connect=retries,
        read=retries,
        status=retries,
        backoff_factor=backoff,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=policy))
    return session


def _get(
    url: str,
    *,
    params: Mapping[str, object] | Sequence[tuple[str, object]] | None = None,
    timeout: float = 60.0,
    retries: int = 3,
    session: requests.Session | None = None,
) -> requests.Response:
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    owns_session = session is None
    client = session or _session(retries=retries)
    try:
        response = client.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        return response
    except (requests.RequestException, ValueError) as exc:
        raise WeatherDownloadError(f"request failed for {url}: {exc}") from exc
    finally:
        if owns_session:
            client.close()


def generate_unique_name(base_name: str, length: int = 6) -> str:
    """Return a process-safe random name without modifying the filesystem."""

    if not base_name:
        raise ValueError("base_name must not be empty")
    if length < 1:
        raise ValueError("length must be positive")
    suffix = "".join(secrets.choice(string.ascii_lowercase) for _ in range(length))
    return f"{base_name}_{suffix}"


def daterange(start: int, end: int) -> pd.DatetimeIndex:
    """Return every calendar day from January 1 to December 31, inclusive."""

    _validate_years(start, end)
    return pd.date_range(f"{start}-01-01", f"{end}-12-31", freq="D")


def isleapyear(year: int) -> bool:
    """Return whether *year* is a Gregorian leap year."""

    return date(int(year), 12, 31).timetuple().tm_yday == 366


def _dates_from_year_day(frame: pd.DataFrame) -> pd.DatetimeIndex:
    year = pd.to_numeric(frame["year"], errors="raise").astype("int64")
    day = pd.to_numeric(frame["day"], errors="raise").astype("int64")
    dates = pd.to_datetime(year.astype(str), format="%Y") + pd.to_timedelta(day - 1, unit="D")
    # Day 366 in a non-leap year silently rolls into the next year; reject it.
    if not np.array_equal(dates.dt.year.to_numpy(), year.to_numpy()):
        raise WeatherValidationError("invalid day of year for one or more years")
    return pd.DatetimeIndex(dates.to_numpy())


def calculate_tav_amp(df: pd.DataFrame) -> tuple[float, float]:
    """Calculate APSIM ``tav`` and ``amp`` from complete daily temperatures.

    ``tav`` is mean annual air temperature. ``amp`` is the mean, across years,
    of the annual range in monthly mean air temperature.  Daily mean air
    temperature is approximated by ``(maxt + mint) / 2``.
    """

    required = {"year", "day", "maxt", "mint"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"missing columns for tav/amp calculation: {sorted(missing)}")
    dates = _dates_from_year_day(df)
    mean_temp = (
        pd.to_numeric(df["maxt"], errors="coerce").to_numpy()
        + pd.to_numeric(df["mint"], errors="coerce").to_numpy()
    ) / 2.0
    series = pd.Series(mean_temp, index=dates).dropna()
    if series.empty:
        raise WeatherValidationError("temperature data contain no finite observations")
    tav = float(series.mean())
    monthly = series.resample("MS").mean()
    annual_amp = monthly.groupby(monthly.index.year).agg(lambda x: x.max() - x.min())
    amp = float(annual_amp.mean())
    return round(tav, 3), round(amp, 3)


def _replace_with_retry(
    source: str | Path,
    destination: str | Path,
    *,
    attempts: int = 5,
    initial_delay: float = 0.05,
) -> None:
    """Atomically replace a file, tolerating short-lived Windows locks.

    Only :class:`PermissionError` is retried. Persistent permission failures,
    read-only destinations, and genuine authorization problems remain visible
    to the caller rather than being silently ignored.
    """

    if attempts < 1:
        raise ValueError("attempts must be at least one")
    delay = initial_delay
    for attempt in range(attempts):
        try:
            os.replace(source, destination)
            return
        except PermissionError:
            if attempt == attempts - 1:
                raise
            time.sleep(delay)
            delay *= 2


def _atomic_write_text(path: Path, text: str) -> Path:
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        _replace_with_retry(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise
    return path


def write_apsim_met(
    data: pd.DataFrame,
    filename: str | Path,
    lonlat: Sequence[float],
    *,
    site: str | None = None,
    extra_metadata: Mapping[str, object] | None = None,
    validate: bool = True,
) -> str:
    """Validate and atomically write an APSIM-compatible ``.met`` file."""

    lon, lat = _validate_lonlat(lonlat)
    frame = _coerce_weather_frame(data)
    report = validate_met(frame)
    if validate:
        report.raise_for_errors()
    tav, amp = calculate_tav_amp(frame)
    metadata = [
        f"!site: {site or 'Not stated'}",
        f"latitude = {lat:.6f}",
        f"longitude = {lon:.6f}",
        f"tav = {tav:.3f}",
        f"amp = {amp:.3f}",
    ]
    for key, value in (extra_metadata or {}).items():
        metadata.append(f"!{key}: {value}")

    values = frame.loc[:, APSIM_COLUMNS].copy()
    values["year"] = values["year"].astype("int64")
    values["day"] = values["day"].astype("int64")
    body = values.to_csv(
        sep=" ", index=False, header=False, na_rep="?", float_format="%.6g"
    )
    text = "\n".join(metadata) + "\n"
    text += " ".join(APSIM_COLUMNS) + "\n"
    text += " ".join(APSIM_UNITS) + "\n"
    text += body
    return str(_atomic_write_text(Path(filename), text))


def _coerce_weather_frame(data: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(data, pd.DataFrame):
        raise TypeError("weather data must be a pandas DataFrame")
    missing = set(APSIM_COLUMNS).difference(data.columns)
    if missing:
        raise WeatherValidationError(f"missing APSIM columns: {sorted(missing)}")
    frame = data.copy()
    for column in APSIM_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.loc[:, list(APSIM_COLUMNS) + [c for c in frame.columns if c not in APSIM_COLUMNS]]
    return frame


def validate_met(met: pd.DataFrame, *, strict: bool = False) -> ValidationReport:
    """Validate APSIM weather data and return all detected issues.

    Hard errors cover missing fields, non-numeric/missing required values,
    impossible dates, duplicated or discontinuous dates, negative rain or
    radiation, and ``mint > maxt``. Broad physical-range checks are warnings
    because genuine climatic extremes can exceed conventional thresholds.
    """

    if not isinstance(met, pd.DataFrame):
        raise TypeError("met must be a pandas DataFrame")
    report = ValidationReport()
    if met.empty:
        report.issues.append(ValidationIssue("error", "empty", "weather data are empty"))
        if strict:
            report.raise_for_errors()
        return report
    missing_columns = set(APSIM_COLUMNS).difference(met.columns)
    if missing_columns:
        report.issues.append(ValidationIssue(
            "error", "missing_columns", f"missing columns: {sorted(missing_columns)}"
        ))
        if strict:
            report.raise_for_errors()
        return report

    frame = _coerce_weather_frame(met)
    for column in APSIM_COLUMNS:
        rows = tuple(frame.index[frame[column].isna()].map(int))
        if rows:
            report.issues.append(ValidationIssue(
                "error", "missing_value", f"{column} has {len(rows)} missing/non-numeric values", rows
            ))

    if frame[list(APSIM_COLUMNS)].isna().any().any():
        if strict:
            report.raise_for_errors()
        return report

    integer_year = np.isclose(frame["year"], np.round(frame["year"]))
    integer_day = np.isclose(frame["day"], np.round(frame["day"]))
    bad_integer = frame.index[~(integer_year & integer_day)]
    if len(bad_integer):
        report.issues.append(ValidationIssue(
            "error", "non_integer_date", "year and day must be integers", tuple(map(int, bad_integer))
        ))
    else:
        try:
            dates = _dates_from_year_day(frame)
        except WeatherValidationError as exc:
            report.issues.append(ValidationIssue("error", "invalid_date", str(exc)))
        else:
            duplicates = frame.index[dates.duplicated(keep=False)]
            if len(duplicates):
                report.issues.append(ValidationIssue(
                    "error", "duplicate_date", "duplicate calendar dates found", tuple(map(int, duplicates))
                ))
            if not dates.is_monotonic_increasing:
                report.issues.append(ValidationIssue("error", "date_order", "dates are not increasing"))
            expected = pd.date_range(dates.min(), dates.max(), freq="D")
            missing_dates = expected.difference(dates)
            if len(missing_dates):
                preview = ", ".join(d.strftime("%Y-%m-%d") for d in missing_dates[:5])
                report.issues.append(ValidationIssue(
                    "error", "date_gaps", f"{len(missing_dates)} daily records are missing ({preview})"
                ))

    checks = (
        (frame["radn"] < 0, "negative_radiation", "radiation must be non-negative"),
        (frame["rain"] < 0, "negative_rain", "rainfall must be non-negative"),
        (frame["mint"] > frame["maxt"], "temperature_order", "mint exceeds maxt"),
    )
    for mask, code, message in checks:
        rows = tuple(map(int, frame.index[mask]))
        if rows:
            report.issues.append(ValidationIssue("error", code, message, rows))

    warnings = (
        (frame["radn"] > 45, "high_radiation", "radiation exceeds 45 MJ m-2 day-1"),
        (frame["rain"] > 500, "high_rain", "daily rainfall exceeds 500 mm"),
        (frame["mint"] < -80, "low_mint", "minimum temperature is below -80 °C"),
        (frame["maxt"] > 60, "high_maxt", "maximum temperature exceeds 60 °C"),
    )
    for mask, code, message in warnings:
        rows = tuple(map(int, frame.index[mask]))
        if rows:
            report.issues.append(ValidationIssue("warning", code, message, rows))

    if strict:
        report.raise_for_errors()
    return report


def get_nasa_data(
    lonlat: Sequence[float],
    start: int,
    end: int,
    *,
    timeout: float = 60.0,
    retries: int = 3,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    """Download NASA POWER daily data and return APSIM weather columns."""

    _validate_years(start, end, minimum=1981)
    lon, lat = _validate_lonlat(lonlat)
    params = {
        "start": f"{start}0101",
        "end": f"{end}1231",
        "latitude": lat,
        "longitude": lon,
        "community": "AG",
        "parameters": ",".join(NASA_PARAMETERS),
        "format": "JSON",
        "time-standard": "LST",
    }
    with _get(
        NASA_POWER_URL, params=params, timeout=timeout, retries=retries, session=session
    ) as response:
        try:
            parameter = response.json()["properties"]["parameter"]
            raw = pd.DataFrame(parameter)
        except (ValueError, KeyError, TypeError) as exc:
            raise WeatherDownloadError("NASA POWER returned an unexpected payload") from exc

    required = set(NASA_PARAMETERS)
    missing = required.difference(raw.columns)
    if missing:
        raise WeatherDownloadError(f"NASA POWER omitted parameters: {sorted(missing)}")
    dates = pd.to_datetime(raw.index, format="%Y%m%d", errors="raise")
    raw = raw.replace(NASA_MISSING, np.nan)
    frame = pd.DataFrame({
        "year": dates.year,
        "day": dates.dayofyear,
        "radn": pd.to_numeric(raw["ALLSKY_SFC_SW_DWN"], errors="coerce").to_numpy(),
        "maxt": pd.to_numeric(raw["T2M_MAX"], errors="coerce").to_numpy(),
        "mint": pd.to_numeric(raw["T2M_MIN"], errors="coerce").to_numpy(),
        "rain": pd.to_numeric(raw["PRECTOTCORR"], errors="coerce").to_numpy(),
    })
    expected = daterange(start, end)
    frame.index = dates
    frame = frame.reindex(expected)
    frame["year"] = expected.year
    frame["day"] = expected.dayofyear
    frame.reset_index(drop=True, inplace=True)
    return frame


def get_nasa(lonlat: Sequence[float], start: int, end: int) -> pd.DataFrame:
    """Compatibility alias for :func:`get_nasa_data`."""

    return get_nasa_data(lonlat, start, end)


def get_nasarad(lonlat: Sequence[float], start: int, end: int) -> pd.DataFrame:
    """Return NASA POWER radiation using its service-native column name."""

    frame = get_nasa_data(lonlat, start, end)
    return frame[["radn"]].rename(columns={"radn": "ALLSKY_SFC_SW_DWN"})


def _download_daymet(
    lonlat: Sequence[float],
    start: int,
    end: int,
    *,
    timeout: float,
    retries: int,
) -> tuple[pd.DataFrame, str | None]:
    _validate_years(start, end, minimum=1980)
    lon, lat = _validate_lonlat(lonlat)
    params = {
        "lat": lat,
        "lon": lon,
        "years": ",".join(map(str, range(start, end + 1))),
        "measuredParams": "dayl,prcp,srad,tmax,tmin,vp,swe",
    }
    with _get(DAYMET_URL, params=params, timeout=timeout, retries=retries) as response:
        try:
            raw = pd.read_csv(BytesIO(response.content), skiprows=6)
        except (pd.errors.ParserError, UnicodeDecodeError) as exc:
            raise WeatherDownloadError("Daymet returned data that could not be parsed") from exc
        disposition = response.headers.get("Content-Disposition", "")
    required = {"year", "yday", "dayl (s)", "srad (W/m^2)", "tmax (deg c)", "tmin (deg c)", "prcp (mm/day)"}
    missing = required.difference(raw.columns)
    if missing:
        raise WeatherDownloadError(f"Daymet omitted columns: {sorted(missing)}")
    # Daymet srad is daylight-period mean flux; multiply by day length.
    radn = raw["dayl (s)"] * raw["srad (W/m^2)"] / 1_000_000.0
    frame = pd.DataFrame({
        "year": raw["year"],
        "day": raw["yday"],
        "radn": radn,
        "maxt": raw["tmax (deg c)"],
        "mint": raw["tmin (deg c)"],
        "rain": raw["prcp (mm/day)"],
    })
    site = disposition.partition("filename=")[2].strip('"').split("_")[0] or None
    return frame, site


def _daymet_dates(frame: pd.DataFrame) -> pd.DatetimeIndex:
    """Convert Daymet's 365-day calendar to Gregorian dates.

    Daymet omits February 29. Consequently, interpreting ``yday`` directly as
    Gregorian day-of-year shifts every post-February record in leap years by
    one day. Mapping through a non-leap reference year avoids that error.
    """

    years = pd.to_numeric(frame["year"], errors="raise").astype("int64")
    days = pd.to_numeric(frame["day"], errors="raise").astype("int64")
    if ((days < 1) | (days > 365)).any():
        raise WeatherValidationError("Daymet day values must be between 1 and 365")
    reference = pd.Timestamp("2001-01-01") + pd.to_timedelta(days - 1, unit="D")
    values = [date(int(year), int(month), int(day)) for year, month, day in zip(years, reference.dt.month, reference.dt.day)]
    return pd.DatetimeIndex(values)


def impute_data(
    met: pd.DataFrame,
    method: Literal["linear", "time", "spline", "mean", "ffill", "bfill", "approx"] = "linear",
    *,
    columns: Iterable[str] | None = None,
    limit: int | None = None,
    copy: bool = True,
    verbose: bool = False,
    **kwargs: object,
) -> pd.DataFrame:
    """Impute selected numeric weather fields.

    Interpolation uses record order unless ``method='time'``, which uses dates
    derived from ``year`` and ``day``.  Extrapolation is intentionally avoided;
    edge gaps require ``ffill``, ``bfill``, or explicit domain knowledge.
    """

    if not isinstance(met, pd.DataFrame):
        raise TypeError("met must be a pandas DataFrame")
    aliases = {"approx": "linear"}
    method = aliases.get(method, method)  # type: ignore[assignment]
    valid = {"linear", "time", "spline", "mean", "ffill", "bfill"}
    if method not in valid:
        raise ValueError(f"method must be one of {sorted(valid)}")
    frame = met.copy(deep=True) if copy else met
    selected = list(columns or [c for c in frame.columns if c not in {"year", "day"}])
    unknown = set(selected).difference(frame.columns)
    if unknown:
        raise KeyError(f"unknown columns: {sorted(unknown)}")
    original_index = frame.index
    if method == "time":
        frame.index = _dates_from_year_day(frame)
    for column in selected:
        if not pd.api.types.is_numeric_dtype(frame[column]):
            raise TypeError(f"cannot impute non-numeric column {column!r}")
        before = int(frame[column].isna().sum())
        if not before:
            continue
        if method == "mean":
            frame[column] = frame[column].fillna(frame[column].mean())
        elif method in {"ffill", "bfill"}:
            frame[column] = frame[column].fillna(method=method, limit=limit)
        else:
            interpolation_method = "time" if method == "time" else method
            frame[column] = frame[column].interpolate(
                method=interpolation_method, limit=limit, limit_area="inside", **kwargs
            )
        if verbose:
            LOGGER.info("imputed %d of %d missing values in %s", before - frame[column].isna().sum(), before, column)
    frame.index = original_index
    return frame


def get_met_from_day_met(
    lonlat: Sequence[float],
    start: int,
    end: int,
    filename: str | Path,
    fill_method: str | None = "linear",
    retry_number: int | None = 3,
    *,
    radiation_source: Literal["daymet", "nasa"] = "daymet",
    timeout: float = 60.0,
    wait: float | None = None,
    site: str | None = None,
    **_: object,
) -> str:
    """Download Daymet weather and write an APSIM ``.met`` file.

    Daymet radiation is retained by default. Set ``radiation_source='nasa'``
    only when a documented harmonization decision requires NASA POWER.
    """

    retries = 0 if retry_number is None else int(retry_number)
    frame, detected_site = _download_daymet(
        lonlat, start, end, timeout=timeout, retries=retries
    )
    dates = _daymet_dates(frame)
    frame.index = dates
    expected = daterange(start, end)
    frame = frame.reindex(expected)
    frame["year"] = expected.year
    frame["day"] = expected.dayofyear
    frame.reset_index(drop=True, inplace=True)
    if radiation_source == "nasa":
        frame["radn"] = get_nasa_data(lonlat, start, end, timeout=timeout, retries=retries)["radn"]
    elif radiation_source != "daymet":
        raise ValueError("radiation_source must be 'daymet' or 'nasa'")
    if fill_method:
        frame = impute_data(frame, method=fill_method)  # type: ignore[arg-type]
    return write_apsim_met(frame, filename, lonlat, site=site or detected_site)


def get_met_nasa_power(
    lonlat: Sequence[float],
    start: int = 1990,
    end: int = 2000,
    fname: str | Path = "get_met_nasa_power.met",
    site: str | None = None,
    *,
    impute_method: str | None = None,
    timeout: float = 60.0,
    retries: int = 3,
) -> str:
    frame = get_nasa_data(lonlat, start, end, timeout=timeout, retries=retries)
    if impute_method:
        frame = impute_data(frame, method=impute_method)  # type: ignore[arg-type]
    return write_apsim_met(frame, fname, lonlat, site=site or "NASA POWER")


def _is_within_USA_mainland(lonlat: Sequence[float]) -> bool:
    """Approximate Daymet domain precheck for the contiguous United States."""

    lon, lat = _validate_lonlat(lonlat)
    return -125.0 <= lon <= -66.9 and 24.4 <= lat <= 49.4


def get_weather(
    lonlat: Sequence[float],
    start: int = 1990,
    end: int = 2020,
    source: Literal["nasa", "nasapower", "daymet"] = "daymet",
    filename: str | Path = "__met_.met",
    **kwargs: object,
) -> str:
    """Acquire weather from a supported source and return the output path."""

    source = source.lower()  # type: ignore[assignment]
    if source in {"nasa", "nasapower"}:
        return get_met_nasa_power(lonlat, start, end, fname=filename, **kwargs)
    if source == "daymet":
        if not _is_within_USA_mainland(lonlat):
            raise ValueError("coordinates are outside this module's Daymet domain precheck; use source='nasa'")
        return get_met_from_day_met(lonlat, start, end, filename=filename, **kwargs)
    raise ValueError("source must be 'nasa', 'nasapower', or 'daymet'")


def _haversine_km(a: Sequence[float], b: Sequence[float]) -> float:
    lon1, lat1 = map(math.radians, _validate_lonlat(a))
    lon2, lat2 = map(math.radians, _validate_lonlat(b))
    dlon, dlat = lon2 - lon1, lat2 - lat1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * 6371.0088 * math.asin(math.sqrt(h))


def nearest_iem_station(
    lonlat: Sequence[float],
    network: str = "IA_COOP",
    *,
    radius_km: float | None = None,
    timeout: float = 30.0,
) -> str:
    """Return the nearest IEM station using great-circle distance."""

    target = _validate_lonlat(lonlat)
    with _get(IEM_NETWORK_URL.format(network=network), timeout=timeout) as response:
        try:
            features = response.json()["features"]
        except (ValueError, KeyError, TypeError) as exc:
            raise WeatherDownloadError("IEM returned an unexpected station payload") from exc
    candidates: list[tuple[float, str]] = []
    for feature in features:
        try:
            coordinates = feature["geometry"]["coordinates"][:2]
            station = feature["properties"]["sid"]
            distance = _haversine_km(target, coordinates)
        except (KeyError, TypeError, ValueError):
            continue
        candidates.append((distance, str(station)))
    if not candidates:
        raise WeatherDownloadError(f"no stations found in IEM network {network!r}")
    distance, station = min(candidates)
    if radius_km is not None and distance > radius_km:
        raise WeatherDownloadError(
            f"nearest station {station} is {distance:.1f} km away, beyond {radius_km:.1f} km"
        )
    return station


def get_iem_by_station(
    dates_tuple: Sequence[str | date | datetime],
    station: str,
    path: str | Path,
    met_tag: str = "",
    *,
    network: str | None = None,
    timeout: float = 60.0,
) -> str:
    """Download an APSIM-formatted file from an IEM COOP station."""

    interval = MetDate(dates_tuple)
    if not station or not station.strip():
        raise ValueError("station must not be empty")
    network = network or f"{station[:2].upper()}CLIMATE"
    params: list[tuple[str, object]] = [
        ("network", network),
        ("stations", station),
        ("year1", interval.start.year),
        ("month1", interval.start.month),
        ("day1", interval.start.day),
        ("year2", interval.end.year),
        ("month2", interval.end.month),
        ("day2", interval.end.day),
        ("vars[]", "apsim"),
        ("what", "view"),
        ("delim", "comma"),
        ("gis", "no"),
    ]
    with _get(IEM_COOP_URL, params=params, timeout=timeout) as response:
        content = response.content
    if not content.strip():
        raise WeatherDownloadError(f"IEM returned an empty file for station {station}")
    output = Path(path).expanduser().resolve() / f"{station}{met_tag}.met"
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{output.name}.", dir=output.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        _replace_with_retry(temporary, output)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise
    return str(output)


def get_iem_by_lonlat(
    dates_tuple: Sequence[str | date | datetime],
    lonlat: Sequence[float],
    path: str | Path,
    met_tag: str = "",
    radius_km: float = 50.0,
    *,
    network: str = "IA_COOP",
) -> dict[str, str]:
    station = nearest_iem_station(lonlat, network=network, radius_km=radius_km)
    filepath = get_iem_by_station(
        dates_tuple, station, path, met_tag, network=network
    )
    return {"station": station, "filepath": filepath}


def read_apsim_met(
    met_path: str | Path,
    skip: int | None = None,
    index_drop: int | Sequence[int] | None = None,
    separator: str = r"\s+",
) -> pd.DataFrame:
    """Read an APSIM weather file, detecting the column-header row by default."""

    path = Path(met_path)
    if not path.is_file():
        raise FileNotFoundError(path)
    if skip is None:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        try:
            header_index = next(
                i for i, line in enumerate(lines)
                if {"year", "day", "radn", "maxt", "mint", "rain"}.issubset(line.lower().split())
            )
        except StopIteration as exc:
            raise WeatherValidationError("could not locate APSIM weather column header") from exc
        skip = header_index
    frame = pd.read_csv(path, skiprows=skip, sep=separator, engine="python")
    if len(frame) and all(str(value).startswith("(") for value in frame.iloc[0].astype(str)):
        frame = frame.iloc[1:]
    if index_drop is not None:
        labels = [index_drop] if isinstance(index_drop, int) else list(index_drop)
        frame = frame.drop(index=labels, errors="ignore")
    frame.reset_index(drop=True, inplace=True)
    for column in frame.columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def write_edited_met(
    old: str | Path,
    daf: pd.DataFrame,
    filename: str = "edited_met.met",
) -> str:
    """Write edited data while preserving the source file's metadata header."""

    old_path = Path(old)
    lines = old_path.read_text(encoding="utf-8-sig").splitlines()
    try:
        column_index = next(i for i, line in enumerate(lines) if "year" in line.lower().split() and "day" in line.lower().split())
    except StopIteration as exc:
        raise WeatherValidationError("source file has no recognizable column header") from exc
    units_index = column_index + 1
    header = "\n".join(lines[: units_index + 1]) + "\n"
    data = daf.to_csv(sep=" ", index=False, header=False, na_rep="?", float_format="%.6g")
    destination = old_path.parent / filename
    return str(_atomic_write_text(destination, header + data))


def merge_columns(
    df1_main: pd.DataFrame,
    common_column: str | Sequence[str],
    df2: pd.DataFrame,
    fill_column: str,
    df2_colummn: str,
) -> pd.DataFrame:
    """Left-join and replace ``fill_column`` where ``df2_colummn`` is present."""

    keys = [common_column] if isinstance(common_column, str) else list(common_column)
    for name, frame, required in (
        ("df1_main", df1_main, set(keys) | {fill_column}),
        ("df2", df2, set(keys) | {df2_colummn}),
    ):
        missing = required.difference(frame.columns)
        if missing:
            raise KeyError(f"{name} is missing columns: {sorted(missing)}")
    if df2.duplicated(keys).any():
        raise ValueError("df2 has duplicate merge keys and would multiply rows")
    replacement = "__replacement__"
    right = df2[keys + [df2_colummn]].rename(columns={df2_colummn: replacement})
    result = df1_main.merge(right, on=keys, how="left", validate="many_to_one")
    result[fill_column] = result[replacement].combine_first(result[fill_column])
    return result.drop(columns=replacement)


def separate_date(date_str: str) -> tuple[str, str, str]:
    """Split a ``YYYYMMDD`` string after strict calendar validation."""

    parsed = datetime.strptime(date_str, "%Y%m%d")
    return parsed.strftime("%Y"), parsed.strftime("%m"), parsed.strftime("%d")


def day_of_year_to_date(year: int, day_of_year: int) -> datetime:
    """Convert a valid one-based day of year to ``datetime``."""

    result = datetime(int(year), 1, 1) + timedelta(days=int(day_of_year) - 1)
    if result.year != int(year) or int(day_of_year) < 1:
        raise ValueError(f"invalid day {day_of_year} for year {year}")
    return result


def impute_missing_leaps(
    dmet: pd.DataFrame,
    fill: float | Mapping[str, float] | None = None,
) -> pd.DataFrame:
    """Insert missing calendar days without fabricating meteorological values.

    By default inserted weather values remain ``NaN`` and must be imputed with
    a scientifically justified method. A scalar or per-column mapping may be
    supplied explicitly, but filling temperature or radiation with zero is
    generally inappropriate.
    """

    frame = _coerce_weather_frame(dmet)
    dates = _dates_from_year_day(frame)
    if dates.duplicated().any():
        raise WeatherValidationError("duplicate dates prevent calendar reindexing")
    frame.index = dates
    full_index = pd.date_range(dates.min(), dates.max(), freq="D")
    result = frame.reindex(full_index)
    inserted = result["year"].isna()
    result["year"] = result.index.year
    result["day"] = result.index.dayofyear
    weather_columns = [c for c in APSIM_COLUMNS if c not in {"year", "day"}]
    if fill is not None:
        if isinstance(fill, Mapping):
            for column, value in fill.items():
                if column in weather_columns:
                    result.loc[inserted, column] = value
        else:
            result.loc[inserted, weather_columns] = float(fill)
    result.index.name = "date"
    return result


__all__ = [
    "APSIM_COLUMNS",
    "MetDate",
    "ValidationIssue",
    "ValidationReport",
    "WeatherDownloadError",
    "WeatherError",
    "WeatherValidationError",
    "calculate_tav_amp",
    "daterange",
    "day_of_year_to_date",
    "generate_unique_name",
    "get_iem_by_lonlat",
    "get_iem_by_station",
    "get_met_from_day_met",
    "get_met_nasa_power",
    "get_nasa",
    "get_nasa_data",
    "get_nasarad",
    "get_weather",
    "impute_data",
    "impute_missing_leaps",
    "isleapyear",
    "merge_columns",
    "nearest_iem_station",
    "read_apsim_met",
    "separate_date",
    "validate_met",
    "write_apsim_met",
    "write_edited_met",
]
