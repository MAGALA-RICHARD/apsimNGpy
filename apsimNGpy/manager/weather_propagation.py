from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Mapping, Sequence

import numpy as np
import pandas as pd

CalibrationMode = Literal["annual", "seasonal", "monthly"]
CorrectionMode = Literal["auto", "always", "never"]


@dataclass(frozen=True)
class PropagationStatistic:
    """Calibration statistics for one weather variable and period."""

    variable: str
    period: int | str
    slope: float
    intercept: float
    r2: float
    rmse: float
    observed_mean: float
    relative_rmse: float
    corrected: bool
    n: int


@dataclass
class PropagatedWeather:
    """Output from the weather-propagation procedure."""

    data: pd.DataFrame
    statistics: pd.DataFrame

    def write_apsim_met(
            self,
            path: str | Path,
            *,
            latitude: float,
            longitude: float,
            tav: float | None = None,
            amp: float | None = None,
            site: str = "Propagated weather",
    ) -> Path:
        return write_apsim_met(
            self.data,
            path,
            latitude=latitude,
            longitude=longitude,
            tav=tav,
            amp=amp,
            site=site,
        )


def propagate_weather(
        observed: pd.DataFrame,
        gridded: pd.DataFrame,
        *,
        calibration_variables: Sequence[str] = ("maxt", "mint"),
        pass_through: Sequence[str] = ("radn", "rain"),
        observed_columns: Mapping[str, str] | None = None,
        gridded_columns: Mapping[str, str] | None = None,
        date_column: str = "date",
        calibration: CalibrationMode = "annual",
        correct: CorrectionMode = "auto",
        min_calibration_years: int = 3,
        min_samples: int = 365,
        minimum_r2: float = 0.70,
        maximum_relative_rmse: float = 0.30,
        acceptable_slope: tuple[float, float] = (0.80, 1.20),
        maximum_intercept_fraction: float = 0.02,
        preserve_observed_overlap: bool = False,
        enforce_temperature_order: bool = True,
) -> PropagatedWeather:
    """
    Create long-term propagated weather data following Van Wart et al. (2015).

    Parameters
    ----------
    observed
        Short-term station observations. Must contain a date column and the
        variables listed in ``calibration_variables``.
    gridded
        Long-term gridded weather. Must contain a date column, calibration
        variables, and pass-through variables.
    calibration_variables
        Variables calibrated against observations, normally ``maxt`` and
        ``mint``.
    pass_through
        Variables copied from the long-term gridded dataset, normally
        radiation and precipitation.
    observed_columns, gridded_columns
        Optional mappings from canonical names such as ``maxt`` to the
        corresponding input column names.
    calibration
        ``annual`` fits one regression per variable. ``seasonal`` fits four
        three-month regressions. ``monthly`` fits one regression per month.
    correct
        ``auto`` applies correction only when diagnostic thresholds indicate
        bias; ``always`` applies every fitted regression; ``never`` evaluates
        the regressions but retains the original gridded values.
    preserve_observed_overlap
        Replace propagated temperatures with observations on dates where
        observations are available.
    """

    if min_calibration_years < 1:
        raise ValueError("min_calibration_years must be at least 1.")

    obs = _prepare_weather_frame(
        observed,
        date_column=date_column,
        column_map=observed_columns,
        required=calibration_variables,
        frame_name="observed",
    )
    grid = _prepare_weather_frame(
        gridded,
        date_column=date_column,
        column_map=gridded_columns,
        required=tuple(calibration_variables) + tuple(pass_through),
        frame_name="gridded",
    )

    overlap = obs[
        ["date", *calibration_variables]
    ].merge(
        grid[["date", *calibration_variables]],
        on="date",
        how="inner",
        suffixes=("_observed", "_gridded"),
        validate="one_to_one",
    )

    valid_years = overlap["date"].dt.year.nunique()

    if valid_years < min_calibration_years:
        raise ValueError(
            "Insufficient overlapping calibration years: "
            f"found {valid_years}, but at least "
            f"{min_calibration_years} are required."
        )

    output = grid[
        ["date", *calibration_variables, *pass_through]
    ].copy()

    output["year"] = output["date"].dt.year
    output["day"] = output["date"].dt.dayofyear

    overlap["_period"] = _calibration_period(
        overlap["date"],
        calibration,
    )
    output["_period"] = _calibration_period(
        output["date"],
        calibration,
    )

    records: list[PropagationStatistic] = []

    for variable in calibration_variables:
        observed_name = f"{variable}_observed"
        gridded_name = f"{variable}_gridded"

        for period in sorted(overlap["_period"].unique()):
            calibration_data = overlap.loc[
                overlap["_period"] == period,
                [observed_name, gridded_name],
            ].dropna()

            if len(calibration_data) < min_samples_for_period(
                    min_samples,
                    calibration,
            ):
                raise ValueError(
                    f"Insufficient data to calibrate {variable!r} "
                    f"for period {period!r}: "
                    f"{len(calibration_data)} valid observations."
                )

            x = calibration_data[gridded_name].to_numpy(dtype=float)
            y = calibration_data[observed_name].to_numpy(dtype=float)

            slope, intercept = np.polyfit(x, y, deg=1)
            fitted = slope * x + intercept

            residual = y - fitted
            rmse = float(np.sqrt(np.mean(residual ** 2)))

            observed_mean = float(np.mean(y))
            mean_scale = max(abs(observed_mean), np.finfo(float).eps)
            relative_rmse = rmse / mean_scale

            ss_res = float(np.sum((y - fitted) ** 2))
            ss_tot = float(np.sum((y - observed_mean) ** 2))
            r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan

            should_correct = _should_correct(
                mode=correct,
                r2=r2,
                rmse_fraction=relative_rmse,
                slope=slope,
                intercept=intercept,
                observed_mean=observed_mean,
                minimum_r2=minimum_r2,
                maximum_relative_rmse=maximum_relative_rmse,
                acceptable_slope=acceptable_slope,
                maximum_intercept_fraction=maximum_intercept_fraction,
            )

            target = output["_period"] == period

            if should_correct:
                output.loc[target, variable] = (
                        slope * output.loc[target, variable] + intercept
                )

            records.append(
                PropagationStatistic(
                    variable=variable,
                    period=period,
                    slope=float(slope),
                    intercept=float(intercept),
                    r2=float(r2),
                    rmse=rmse,
                    observed_mean=observed_mean,
                    relative_rmse=relative_rmse,
                    corrected=should_correct,
                    n=len(calibration_data),
                )
            )

    if preserve_observed_overlap:
        output = _insert_observed_values(
            output,
            obs,
            calibration_variables,
        )

    if enforce_temperature_order:
        _validate_temperature_order(output)

    output = output.drop(columns="_period")
    output = output.sort_values("date").reset_index(drop=True)

    statistics = pd.DataFrame(
        [record.__dict__ for record in records]
    )

    return PropagatedWeather(
        data=output,
        statistics=statistics,
    )


def _prepare_weather_frame(
        frame: pd.DataFrame,
        *,
        date_column: str,
        column_map: Mapping[str, str] | None,
        required: Sequence[str],
        frame_name: str,
) -> pd.DataFrame:
    data = frame.copy()

    if date_column not in data:
        raise KeyError(
            f"{frame_name!r} data do not contain date column "
            f"{date_column!r}."
        )

    data = data.rename(columns={date_column: "date"})

    if column_map:
        rename = {
            source_name: canonical_name
            for canonical_name, source_name in column_map.items()
        }
        data = data.rename(columns=rename)

    missing = sorted(set(required).difference(data.columns))

    if missing:
        raise KeyError(
            f"{frame_name!r} data are missing required columns: "
            f"{missing}."
        )

    data["date"] = pd.to_datetime(data["date"], errors="raise").dt.normalize()

    if data["date"].duplicated().any():
        duplicate_dates = (
            data.loc[data["date"].duplicated(), "date"]
            .dt.strftime("%Y-%m-%d")
            .tolist()
        )
        raise ValueError(
            f"{frame_name!r} data contain duplicate dates: "
            f"{duplicate_dates[:5]}."
        )

    for variable in required:
        data[variable] = pd.to_numeric(data[variable], errors="coerce")

    return data.sort_values("date").reset_index(drop=True)


def _calibration_period(
        dates: pd.Series,
        mode: CalibrationMode,
) -> pd.Series:
    if mode == "annual":
        return pd.Series("annual", index=dates.index)

    if mode == "monthly":
        return dates.dt.month

    if mode == "seasonal":
        # Four consecutive three-month periods:
        # Jan-Mar, Apr-Jun, Jul-Sep, Oct-Dec.
        return ((dates.dt.month - 1) // 3 + 1).astype(int)

    raise ValueError(
        "calibration must be 'annual', 'seasonal', or 'monthly'."
    )


def min_samples_for_period(
        annual_minimum: int,
        mode: CalibrationMode,
) -> int:
    if mode == "annual":
        return annual_minimum
    if mode == "seasonal":
        return max(90, annual_minimum // 4)
    return max(28, annual_minimum // 12)


def _should_correct(
        *,
        mode: CorrectionMode,
        r2: float,
        rmse_fraction: float,
        slope: float,
        intercept: float,
        observed_mean: float,
        minimum_r2: float,
        maximum_relative_rmse: float,
        acceptable_slope: tuple[float, float],
        maximum_intercept_fraction: float,
) -> bool:
    if mode == "always":
        return True

    if mode == "never":
        return False

    if mode != "auto":
        raise ValueError("correct must be 'auto', 'always', or 'never'.")

    slope_is_biased = not (
            acceptable_slope[0] <= slope <= acceptable_slope[1]
    )

    intercept_limit = maximum_intercept_fraction * max(
        abs(observed_mean),
        np.finfo(float).eps,
    )
    intercept_is_biased = abs(intercept) > intercept_limit
    agreement_is_poor = rmse_fraction > maximum_relative_rmse

    # Following the paper's conceptual rule: calibration is meaningful when
    # daily correspondence is sufficiently strong and bias/agreement is poor.
    return bool(
        np.isfinite(r2)
        and r2 >= minimum_r2
        and (
                agreement_is_poor
                or slope_is_biased
                or intercept_is_biased
        )
    )


def _insert_observed_values(
        propagated: pd.DataFrame,
        observed: pd.DataFrame,
        variables: Sequence[str],
) -> pd.DataFrame:
    replacement = observed[["date", *variables]].copy()

    merged = propagated.merge(
        replacement,
        on="date",
        how="left",
        suffixes=("", "_observed"),
        validate="one_to_one",
    )

    for variable in variables:
        observed_variable = f"{variable}_observed"
        merged[variable] = merged[observed_variable].combine_first(
            merged[variable]
        )
        merged = merged.drop(columns=observed_variable)

    return merged


def _validate_temperature_order(data: pd.DataFrame) -> None:
    if not {"mint", "maxt"}.issubset(data.columns):
        return

    invalid = data["mint"] > data["maxt"]

    if invalid.any():
        dates = (
            data.loc[invalid, "date"]
            .dt.strftime("%Y-%m-%d")
            .head()
            .tolist()
        )
        raise ValueError(
            "Temperature propagation produced mint > maxt on "
            f"{invalid.sum()} days. Example dates: {dates}. "
            "Consider seasonal calibration or inspect the observations."
        )


def write_apsim_met(
        weather: pd.DataFrame,
        path: str | Path,
        *,
        latitude: float,
        longitude: float,
        tav: float | None = None,
        amp: float | None = None,
        site: str = "Propagated weather",
) -> Path:
    """
    Write propagated daily weather to an APSIM-compatible .met file.
    """

    required = {"date", "year", "day", "radn", "maxt", "mint", "rain"}
    missing = sorted(required.difference(weather.columns))

    if missing:
        raise KeyError(
            f"Cannot write APSIM met file; missing columns: {missing}."
        )

    data = weather.copy()
    data["date"] = pd.to_datetime(data["date"])

    if tav is None:
        tav = float(
            ((data["maxt"] + data["mint"]) / 2.0)
            .groupby(data["date"].dt.year)
            .mean()
            .mean()
        )

    if amp is None:
        monthly_temperature = (
            ((data["maxt"] + data["mint"]) / 2.0)
            .groupby(data["date"].dt.month)
            .mean()
        )
        amp = float(
            monthly_temperature.max() - monthly_temperature.min()
        )

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    header = [
        f"!site: {site}",
        "!weather data propagated using the method of "
        "Van Wart et al. (2015)",
        f"latitude = {latitude:.6f} (DECIMAL DEGREES)",
        f"longitude = {longitude:.6f} (DECIMAL DEGREES)",
        f"tav = {tav:.3f} (oC)",
        f"amp = {amp:.3f} (oC)",
        "year day radn maxt mint rain",
        "() () (MJ/m2/day) (oC) (oC) (mm)",
    ]

    met_data = data[
        ["year", "day", "radn", "maxt", "mint", "rain"]
    ].copy()

    with output_path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write("\n".join(header))
        stream.write("\n")
        met_data.to_csv(
            stream,
            sep=" ",
            index=False,
            header=False,
            float_format="%.3f",
        )

    return output_path


if __name__ == "__main__":
    observed = pd.read_csv(
        "station_weather.csv",
        parse_dates=["date"],
    )

    power = pd.read_csv(
        "nasa_power_daily.csv",
        parse_dates=["date"],
    )

    result = propagate_weather(
        observed=observed,
        gridded=power,
        observed_columns={
            "maxt": "maximum_temperature",
            "mint": "minimum_temperature",
        },
        gridded_columns={
            "maxt": "T2M_MAX",
            "mint": "T2M_MIN",
            "radn": "ALLSKY_SFC_SW_DWN",
            "rain": "PRECTOTCORR",
        },
        calibration="annual",
        correct="auto",
    )

    print(result.statistics)

    result.write_apsim_met(
        "weather/ames_propagated.met",
        latitude=42.0308,
        longitude=-93.6319,
        site="Ames, Iowa",
    )
