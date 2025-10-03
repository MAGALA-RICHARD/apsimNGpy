import os
import subprocess
from pathlib import Path
from platform import system
from typing import Union, Hashable, Optional

from collections.abc import Sequence as _Sequence

from apsimNGpy.exceptions import ForgotToRunError, EmptyDateFrameError
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import label
from abc import abstractmethod, ABC
from collections import OrderedDict
from apsimNGpy.settings import logger
from functools import wraps
from apsimNGpy.stats.data_insights import mva

try:
    import seaborn as sns
except ModuleNotFoundError:
    logger.info("Seaborn is not installed. Please install it to continue.")
    import sys

    sys.exit(1)

HOME = Path.home()


def open_file(filepath):
    """Open a file using the default OS application."""

    if system() == 'Darwin':
        subprocess.call(['open', filepath])
    elif system() == 'Windows':
        os.startfile(filepath)
    elif system() == 'Linux':
        subprocess.call(['xdg-open', filepath])
    else:
        raise OSError('Unsupported operating system')


def inherit_docstring_from(obj):
    def decorator(func):
        @wraps(obj)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.__doc__ = func.__doc__ + "\n" + obj.__doc__
        return wrapper

    return decorator


added_plots = OrderedDict()


def _ensure_sequence(x) -> list:
    if x is None:
        return []
    if isinstance(x, str):
        return [x]
    if isinstance(x, _Sequence):
        return list(x)
    return [x]


def _maybe_make_group_label(df: pd.DataFrame, group_cols: list[Hashable]) -> Optional[str]:
    """
    If multiple grouping columns are used and the caller didn't provide hue,
    create a compact label column to use as hue.
    """
    if not group_cols:
        return None
    if len(group_cols) == 1:
        return group_cols[0]
    label_col = "_group_label_"
    if label_col not in df.columns:
        df[label_col] = df[group_cols].astype(str).agg(" | ".join, axis=1)
    return label_col


def _maybe_to_datetime(df: pd.DataFrame, col: Hashable, auto: bool) -> None:
    if auto and not pd.api.types.is_datetime64_any_dtype(df[col]):
        try:
            df[col] = pd.to_datetime(df[col], errors="raise")
        except Exception:
            # Leave as-is if conversion fails
            pass


def _sort_for_ts(df: pd.DataFrame, time_col: Hashable, group_cols: list[Hashable]) -> pd.DataFrame:
    sort_cols = group_cols + [time_col] if group_cols else [time_col]
    return df.sort_values(sort_cols, kind="mergesort")


def _coerce_to_str(x: Hashable) -> str:
    return str(x)


def _default_ylabel(response: Hashable, window: int, centered: bool = True) -> str:
    center_txt = "centered" if centered else "trailing"
    return f"{_coerce_to_str(response)} ({window}-pt {center_txt} moving average)"


def _add_raw_overlay(g: sns.FacetGrid, time_col: Hashable, response: Hashable, **line_kws) -> None:
    # Draw raw lines on top of each facet, respecting hue mapping from the grid
    import seaborn as sns  # local import to avoid namespace surprises
    g.map_dataframe(
        sns.lineplot,
        x=time_col,
        y=response,
        estimator=None,
        **line_kws
    )


class PlotManager(ABC):
    """"
     Abstract base class for high-level visualization of APSIMNGpy simulation outputs.

    The Goal of this class is to provide quick and high level plotting functions for apsimNGpy simulations. Wraps around seaborn and pandas plotting fucntions

    This class provides a clean interface for generating commonly used plots from
    APSIM model results using seaborn and pandas under the hood. It is intended
    to be subclassed by simulation engines (e.g., CoreModel) that implement access
    to APSIM outputs through the abstract methods.

    Features:
        - High-level wrappers for Seaborn plots (lineplot, catplot, scatterplot, histplot, etc.)
        - Automatic result refreshing and cleanup between plots
        - Rendering and saving utility with customizable aesthetics
        - Built-in support for correlation heatmaps and grouped comparisons
        - Leverages APSIM report variables dynamically for plotting

    Requirements for subclasses:
        - Must implement the `results` property
        - Must provide methods: `get_simulated_output`, `add_report_variable`, and `run`

    Example use:
        Subclass PlotManager in your simulation engine and use built-in methods to
        quickly visualize results:
            >>> model = ApsimModel(...)
            >>> model.run()
            >>> model.series_plot(y='Biomass', x='DaysAfterSowing')
            >>> model.render_plot(title='Biomass over Time', show=True, ylabel='Biomass kg/ha', xlabel = 'Days after sowing')

    See Also:
        - seaborn.lineplot
        - seaborn.catplot
        - seaborn.scatterplot
        - pandas.DataFrame.boxplot
    """

    def __init__(self):

        self.added_plots = None
        self.displayed = False

    @property
    @abstractmethod
    def results(self):
        pass

    @abstractmethod
    def get_simulated_output(self, report_name: str):
        pass

    @abstractmethod
    def add_report_variable(self, specification: str):
        pass

    @abstractmethod
    def run(self, report_name: Union[str, list, tuple]):
        pass

    def _clean_numeric_data(self, df, exclude_vars=('SimulationID', 'CheckpointID', 'CheckpointName')):
        """Select numeric _variables and remove low-signal columns."""
        df = df.select_dtypes(include="number").copy()

        # Drop excluded _variables
        for var in exclude_vars:
            if var in df.columns:
                df.drop(columns=var, inplace=True)

        # Remove columns with near-zero sum
        low_info_cols = [col for col in df.columns if df[col].sum() < 1]
        if low_info_cols:
            print(f"Removing low-info columns: {low_info_cols}")
            df.drop(columns=low_info_cols, inplace=True)

        return df

    def _harmonize_df(self, table):
        if table is not None:
            data = self.get_simulated_output(table)
        else:
            data = self.results
        return data

    @inherit_docstring_from(sns.relplot)  # keep your original decorator if available
    def plot_mva(
            self,
            table: pd.DataFrame,
            time_col: Hashable,
            response: Hashable,
            *,
            window: int = 5,
            min_period: int = 1,
            grouping: Optional[Union[Hashable, _Sequence[Hashable]]] = None,
            preserve_start: bool = True,
            kind: str = "line",
            estimator=None,  # avoid aggregation by default (pass-through to seaborn)
            plot_raw: bool = False,  # overlay original (unsmoothed) series
            raw_alpha: float = 0.35,
            raw_linewidth: float = 1.0,
            auto_datetime: bool = False,  # attempt to convert time_col to datetime
            ylabel: Optional[str] = None,  # override auto y-label
            return_data: bool = False,  # optionally return (FacetGrid, smoothed_df)
            **kwargs,
    ) -> sns.FacetGrid | tuple[sns.FacetGrid, pd.DataFrame]:
        """
        Plot a centered moving average (MVA) of `response` using seaborn.relplot.

        Enhancements over a direct relplot call:
          - Computes MVA with `mva(...)` and **plots the smoothed series**
          - Auto-assigns `hue` from `grouping` (supports multi-column grouping)
          - Optional overlay of the **raw** series for comparison
          - Preserves original row order and handles NaN groups
        """

        group_cols = _ensure_sequence(grouping)

        # harmonize & optional datetime conversion
        data = self._harmonize_df(table)
        _maybe_to_datetime(data, time_col, auto_datetime)

        # compute moving average on a sorted copy for determinism
        data_sorted = _sort_for_ts(data.copy(), time_col, group_cols)
        smoothed = mva(
            data_sorted,
            time_col=time_col,
            response=response,
            window=window,
            min_period=min_period,
            grouping=grouping,
            preserve_start=preserve_start,
        )

        # relplot should see the smoothed data, not the raw table
        y_smooth = f"{response}_roll_mean"
        if y_smooth not in smoothed.columns:
            raise KeyError(f"Smoothed column `{y_smooth}` not found after mva().")

        # choose hue if user did not supply one
        if "hue" not in kwargs and group_cols:
            hue_col = _maybe_make_group_label(smoothed, group_cols)
            if hue_col is not None:
                kwargs["hue"] = hue_col

        # seaborn.relplot defaults to kind='scatter'; for time series we use line
        kwargs.setdefault("kind", kind)
        kwargs.setdefault("estimator", estimator)  # None → draw each observation
        kwargs.setdefault("marker", None)

        # wire x/y; do not let user override `data` accidentally
        kwargs.pop("data", None)
        kwargs['x'] = time_col
        kwargs["y"] = y_smooth

        g = sns.relplot(data=smoothed, **kwargs)

        # y-label
        if ylabel is None:
            ylabel = _default_ylabel(response, window, centered=True)
        try:
            g.set_ylabels(ylabel)
        except Exception:
            pass  # older seaborn: ignore

        # Optional raw overlay
        if plot_raw:
            # We need raw data with same sorting & hue semantics as smoothed
            raw = data_sorted.copy()
            # If we created a composite hue, replicate it on raw
            if "hue" in kwargs and kwargs["hue"] not in raw.columns and kwargs["hue"] in smoothed.columns:
                raw[kwargs["hue"]] = smoothed[kwargs["hue"]].values

            _add_raw_overlay(
                g,
                time_col=time_col,
                response=response,
                alpha=raw_alpha,
                linewidth=raw_linewidth,
                hue=kwargs.get("hue", None),
            )

        if return_data:
            return g, smoothed
        return g

    @inherit_docstring_from(pd.DataFrame)
    def boxplot(self, column, *, table=None,
                by=None, figsize=(10, 8), grid=False, **kwargs):

        """
        Plot a boxplot from the simulation results using ``pandas.DataFrame.boxplot`` \n
        =======================================================================.
        """
        self._refresh()

        if self.results is None and table is None:
            raise ForgotToRunError("Results not found.")
        df = self.results if table is None else self.get_simulated_output(table)

        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in results.")

        if by and by not in df.columns:
            raise ValueError(f"Grouping column '{by}' not found in results.")

        # Plot
        plt.figure(figsize=figsize)
        ax = df.boxplot(column=column, by=by, grid=grid, **kwargs)

        return ax

    @inherit_docstring_from(sns.histplot)
    def distribution(self, x, *, table=None, **kwargs):
        """Plot distribution for a numeric variable. It uses ``seaborn.histplot`` function. Please see their documentation below
        =========================================================================================================\n
        """
        added_plots['current_plot'] = 'distribution'
        self._refresh()

        from pandas.api.types import is_string_dtype

        if is_string_dtype(self.results[x]):
            raise ValueError(f"{x} contains strings")

        df = self.results if table is None else self.get_simulated_output(table)
        kwargs.pop('show', None)
        sns.histplot(data=df, x=x, kde=True, **kwargs)

    def label(self):
        ...

    def render_plot(
            self,
            *,
            save_as: Union[str, Path] = '',
            dpi: int = 600,
            show: bool = True,
            xlabel: str = '',
            ylabel: str = '',
            title: str = '',
            titlesize: int = 12,
            axessize: int = 14,
            xticksize: int = 10,
            yticksize: int = 10,
            legend_size: int = 12,
            figtitle_size: int = 15,
            xlabel_size: int = 16,
            ylabel_size=16,

    ):

        # Configure plot aesthetics
        plt.rcParams['axes.titlesize'] = titlesize
        plt.rcParams['axes.labelsize'] = axessize
        plt.rcParams['xtick.labelsize'] = xticksize
        plt.rcParams['ytick.labelsize'] = yticksize
        plt.rcParams['legend.fontsize'] = legend_size
        plt.rcParams['figure.titlesize'] = figtitle_size

        # Set optional labels and title

        if xlabel:
            plt.xlabel(xlabel, fontsize=xlabel_size)
        ylabel
        if ylabel:
            plt.ylabel(ylabel, fontsize=ylabel_size)
        if title:
            plt.title(title, )

        plt.tight_layout()

        if save_as:
            plt.savefig(str(save_as), dpi=dpi)

        if show:
            self.show()
            self.displayed = True

    @staticmethod
    def show():
        try:
            if plt.get_fignums():
                plt.show()
            else:
                logger.info('Plot is closed. Initiate again')
        finally:
            if plt.get_fignums():
                plt.close()

    @staticmethod
    def _refresh():
        if plt.get_fignums():
            plt.close()

    @inherit_docstring_from(sns.lineplot)
    def series_plot(self, table=None, *, x: str = None, y: Union[str, list] = None, hue=None, size=None, style=None,
                    units=None, weights=None,
                    palette=None, hue_order=None, hue_norm=None, sizes=None, size_order=None, size_norm=None,
                    dashes=True, markers=None, style_order=None, estimator='mean', errorbar=('ci', 95), n_boot=1000,
                    seed=None, orient='x', sort=True, err_style='band', err_kws=None, legend='auto',
                    ci='deprecated', ax=None, **kwargs):
        """
        Just a wrapper for seaborn.lineplot that supports multiple y columns that could be provided as a list

        Examples::

           from apsimNGpy.core.apsim import ApsimModel
           model = ApsimModel(model= 'Maize')
           # run the results
           model.run(report_names='Report')
           model.series_plot(x='Maize.Grain.Size', y='Yield', table='Report')
           model.render_plot(show=True, ylabel = 'Maize yield', xlabel ='Maize grain size')

        Plot two variables::

           model.series_plot(x='Yield', y=['Maize.Grain.N', 'Maize.Grain.Size'], table= 'Report')

         see below or https://seaborn.pydata.org/generated/seaborn.lineplot.html \n
        =============================================================================================================================================\n
        """
        self._refresh()
        added_plots['current_plot'] = 'series_plot'
        if table:
            data = self.get_simulated_output(table)
        else:
            data = self.results

        df = data.copy()

        if isinstance(y, list):
            if x is None:
                raise ValueError("When passing a list for y, x must be specified")

            # Ensure x column exists
            if x not in df.columns:
                raise KeyError(f"{x} not found in data")

            # Melt into long-form
            df = df[[x] + y].melt(id_vars=x, var_name='Variable', value_name='Value')

            # Adjust parameters for seaborn
            x = x
            y = 'Value'
            if hue is None:
                hue = 'Variable'  # Color lines by variable name

        sns.lineplot(
            data=df, x=x, y=y, hue=hue, size=size, style=style, units=units, weights=weights,
            palette=palette, hue_order=hue_order, hue_norm=hue_norm, sizes=sizes, size_order=size_order,
            size_norm=size_norm,
            dashes=dashes, markers=markers, style_order=style_order, estimator=estimator, errorbar=errorbar,
            n_boot=n_boot,
            seed=seed, orient=orient, sort=sort, err_style=err_style, err_kws=err_kws, legend=legend,
            ci=ci, ax=ax, **kwargs)

    @inherit_docstring_from(sns.scatterplot)
    def scatter_plot(
            self,
            table=None,
            *,
            x=None,
            y=None,
            hue=None,
            size=None,
            style=None,
            palette=None,
            hue_order=None,
            hue_norm=None,
            sizes=None,
            size_order=None,
            size_norm=None,
            markers=True,
            style_order=None,
            legend='auto',
            ax=None,
            **kwargs
    ):
        """
        Plot scatter plot using seaborn with flexible aesthetic mappings.
        reference: https://seaborn.pydata.org/generated/seaborn.scatterplot.html. Check seaborn documentation below for more details \n
        ================================================================================================================================\n"""
        self._refresh()
        if table is None:
            data = self.results
        else:
            data = self.get_simulated_output(table)
        sns.scatterplot(
            data=data,
            x=x,
            y=y,
            hue=hue,
            size=size,
            style=style,
            palette=palette,
            hue_order=hue_order,
            hue_norm=hue_norm,
            sizes=sizes,
            size_order=size_order,
            size_norm=size_norm,
            markers=markers,
            style_order=style_order,
            legend=legend,
            ax=ax,
            **kwargs
        )

    @inherit_docstring_from(sns.catplot)
    def cat_plot(self,
                 table=None,
                 *,
                 x=None,
                 y=None,
                 hue=None,
                 row=None,
                 col=None,
                 kind='strip',
                 estimator='mean',
                 errorbar=('ci', 95),
                 n_boot=1000,
                 seed=None,
                 units=None,
                 weights=None,
                 order=None,
                 hue_order=None,
                 row_order=None,
                 col_order=None,
                 col_wrap=None,
                 height=5,
                 aspect=1,
                 log_scale=None,
                 native_scale=False,
                 formatter=None,
                 orient=None,
                 color=None,
                 palette=None,
                 hue_norm=None,
                 legend='auto',
                 legend_out=True,
                 sharex=True,
                 sharey=True,
                 margin_titles=False,
                 facet_kws=None,
                 **kwargs
                 ):
        """Wrapper for seaborn.catplot with all keyword arguments.
        reference https://seaborn.pydata.org/generated/seaborn.catplot.html or check seaborn documentation below\n
        =========================================================================================================\n"""
        self._refresh()
        added_plots['cat_plot'] = 'cat_plot'
        df = self.results if not table else self.get_simulated_output(table)
        return sns.catplot(
            data=df,
            x=x,
            y=y,
            hue=hue,
            row=row,
            col=col,
            kind=kind,
            estimator=estimator,
            errorbar=errorbar,
            n_boot=n_boot,
            seed=seed,
            units=units,
            weights=weights,
            order=order,
            hue_order=hue_order,
            row_order=row_order,
            col_order=col_order,
            col_wrap=col_wrap,
            height=height,
            aspect=aspect,
            log_scale=log_scale,
            native_scale=native_scale,
            formatter=formatter,
            color=color,
            palette=palette,
            hue_norm=hue_norm,
            legend=legend,
            legend_out=legend_out,
            sharex=sharex,
            sharey=sharey,
            margin_titles=margin_titles,
            facet_kws=facet_kws,
            **kwargs
        )

    def relplot(self, table=None, **kwargs):
        data = self.get_simulated_output(table) if table is not None else self.results
        g = sns.relplot(data=data, **kwargs)
        return g

    def correlation_heatmap(self, columns: list = None, table=None, figsize=(10, 8), **kwargs):
        self._refresh()
        added_plots['correlation_heatmap'] = 'correlation_heatmap'
        """Plot correlation heatmap for numeric _variables."""
        df = self.get_simulated_output(table) if table is not None else self.results
        if columns:
            df = df[columns]
        else:
            df = self._clean_numeric_data(df)
            if df.empty:
                raise EmptyDateFrameError("No valid numeric data for correlation heatmap.")

        corr = df.corr()
        plt.figure(figsize=figsize)
        sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", **kwargs)
        plt.title("Correlation Heatmap")
        plt.tight_layout()


if __name__ == '__main__':
    from apsimNGpy.core.apsim import ApsimModel
    from apsimNGpy.core.base_data import load_default_simulations

    scrach = Path.home() / 'testss'
    scrach.mkdir(exist_ok=True)

    apsim = load_default_simulations(crop='Maize', simulations_object=False, set_wd=scrach)
    model = ApsimModel(model='maize')
    model.add_report_variable(variable_spec='[Soil].Nutrient.TotalC[1]/1000 as SOC1', report_name='Report',
                              set_event_names=['[Clock].EndOfYear', '[Maize].Harvesting'])
    model.add_db_table(
        variable_spec=['[Soil].Nutrient.TotalC[1]/1000 as SOC1', '[Soil].Nutrient.TotalC[2]/1000 as SOC2',
                       '[Clock].Today.Year as Year'], rename='my_table')
    # model.add_db_table(variable_spec=['[Soil].Nutrient.TotalC[2]/1000 as SOC2',])
    model.update_mgt(management=({"Name": 'Sow using a variable rule', 'Population': 8},))
    model.run(report_name='my_table')

    model.cat_plot(y='SOC1', x='Zone')

    model.series_plot(y='SOC2', x='Year')
    model.distribution('SOC1', show=True)
    # model.plot_distribution('Yield')
    model.run(report_name='Report')
    model.correlation_heatmap()
    # model.get_weather_from_web(lonlat=(-93.50456, 42.601247), start=1990, end=2001, source='daymet')
