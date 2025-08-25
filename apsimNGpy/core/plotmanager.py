import os
import subprocess
from pathlib import Path
from platform import system
from typing import Union
from apsimNGpy.exceptions import ForgotToRunError, EmptyDateFrameError
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import label
from abc import abstractmethod, ABC
from collections import OrderedDict
from apsimNGpy.settings import logger
from functools import wraps

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

    def _clean_numeric_data(self, exclude_vars=('SimulationID', 'CheckpointID', 'CheckpointName')):
        """Select numeric _variables and remove low-signal columns."""
        df = self.results.select_dtypes(include="number").copy()

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

    @inherit_docstring_from(pd.DataFrame)
    def boxplot(self, column, *,
                by=None, figsize=(10, 8), grid=False, **kwargs):

        """
        Plot a boxplot from the simulation results using ``pandas.DataFrame.boxplot`` \n
        =======================================================================.
        """
        self._refresh()

        if self.results is None:
            raise ForgotToRunError("Results not found.")
        df = self.results

        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in results.")

        if by and by not in df.columns:
            raise ValueError(f"Grouping column '{by}' not found in results.")

        # Plot
        plt.figure(figsize=figsize)
        ax = df.boxplot(column=column, by=by, grid=grid, **kwargs)

        return ax

    @inherit_docstring_from(sns.histplot)
    def distribution(self, x, *, data=None, **kwargs):
        """Plot distribution for a numeric variable. It uses ``seaborn.histplot`` function. Please see their documentation below
        =========================================================================================================\n
        """
        added_plots['current_plot'] = 'distribution'
        self._refresh()

        from pandas.api.types import is_string_dtype

        if is_string_dtype(self.results[x]):
            raise ValueError(f"{x} contains strings")

        df = data or self.results
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
            figtitle_size: int = 15
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
            plt.xlabel(xlabel)
        ylabel
        if ylabel:
            plt.ylabel(ylabel)
        if title:
            plt.title(title)

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
    def series_plot(self, data=None, *, x: str = None, y: Union[str, list] = None, hue=None, size=None, style=None,
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
           model.series_plot(x='Maize.Grain.Size', y='Yield')
           model.render_plot(show=True, ylabel = 'Maize yield', xlabel ='Maize grain size')

        Plot two variables::

           model.series_plot(x='Yield', y=['Maize.Grain.N', 'Maize.Grain.Size'])

         see below or https://seaborn.pydata.org/generated/seaborn.lineplot.html \n
        =============================================================================================================================================\n
        """
        self._refresh()
        added_plots['current_plot'] = 'series_plot'
        if data is None:
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
            data=None,
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
        if data is None:
            data = self.results
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
                 data=None,
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
        df = self.results if data is None else data
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

    def relplot(self, data=None, **kwargs):
        data = data or self.results
        g = sns.relplot(data=data, **kwargs)
        return g

    def correlation_heatmap(self, columns: list = None, figsize=(10, 8), **kwargs):
        self._refresh()
        added_plots['correlation_heatmap'] = 'correlation_heatmap'
        """Plot correlation heatmap for numeric _variables."""
        if columns:
            df = self.results[columns]
        else:
            df = self._clean_numeric_data()
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
                       '[Clock].Today.Year as Year'])
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
