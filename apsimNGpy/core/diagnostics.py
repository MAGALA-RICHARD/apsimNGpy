import os
import subprocess
from pathlib import Path
from platform import system
from typing import Union

import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import label
from summarytools import dfSummary
from winerror import XACT_S_LAST

from apsimNGpy.settings import logger
try:
    import seaborn as sns
except ModuleNotFoundError:
    logger.info("Seaborn is not installed. Please install it to continue.")
    import sys
    sys.exit(1)

from apsimNGpy.core.apsim import ApsimModel

HOME = Path.home()


def open_file(filepath):
    """Open a file using the default OS application."""
    try:
        if system() == 'Darwin':
            subprocess.call(['open', filepath])
        elif system() == 'Windows':
            os.startfile(filepath)
        elif system() == 'Linux':
            subprocess.call(['xdg-open', filepath])
        else:
            raise OSError('Unsupported operating system')
    except Exception as e:
        print(f"Failed to open file: {e}")


class Diagnostics(ApsimModel):
    def __init__(self, model, out_path=None, **kwargs):
        super().__init__(model, out_path, **kwargs)
        self.display = False
        if not self.ran_ok:
            self.run()

    def _clean_numeric_data(self, exclude_vars=('SimulationID', 'CheckpointID', 'CheckpointName')):
        """Select numeric _variables and remove low-signal columns."""
        df = self.results.select_dtypes(include="number").copy()

        # Drop excluded _variables
        for var in exclude_vars:
            if var in df.columns:
                print(f"Removing column: {var}")
                df.drop(columns=var, inplace=True)

        # Remove columns with near-zero sum
        low_info_cols = [col for col in df.columns if df[col].sum() < 1]
        if low_info_cols:
            print(f"Removing low-info columns: {low_info_cols}")
            df.drop(columns=low_info_cols, inplace=True)

        return df

    def plot_distribution(self, variable, *, stat='density', y=None, xlab=None, ylab=None,
                          title='', show=False, save_as='',**kwargs):
        """Plot distribution for a numeric variable."""
        self._refresh()
        kwargs['stat'] = stat
        kwargs.pop('x', None)
        if y:
            kwargs['y'] = y

        from pandas.api.types import is_string_dtype

        if is_string_dtype(self.results[variable]):
            raise ValueError(f"{variable} contains strings")

        sns.histplot(data=self.results, x=variable, kde=True, **kwargs)
        plt.title(title)
        plt.tight_layout()
        xlab = xlab or variable
        if ylab:
            plt.xlabel(ylab)

        plt.xlabel(xlab)
        self._finalize(show, save_as)

    def label(self):
       ...

    def _finalize(self, show, save_as):
        assert isinstance(show, bool), f"show is expected to be a boolean value"
        if not any([show, save_as]):
            logger.warning('Please specify either show (bool) or save_as (str) as an argument')
        if save_as:
            plt.savefig(save_as)
        if show:
            self.display=True
            self.show()

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
    def line_plot(self, y:Union[str, list, tuple], *,  xlab=None, ylab=None, x=None, time='Year',table_name='Report',show =True, save_as='', **kwargs):
        """Plot time series of a variable against a time field."""
        self._refresh()
        var_name = time.capitalize()
        self.add_report_variable(f'[Clock].Today.{var_name} as {var_name}', table_name)
        pops = ['y', 'x']
        for p in pops:
            kwargs.pop(p, None)
        if x is None:
            self.run(report_name=table_name)

        else:
            var_name =x

        df = self.results
        if isinstance(y, str):
           sns.lineplot(data=df, x=var_name, y=y, **kwargs)
        if isinstance(y, (tuple,list)):
            labels= y or kwargs.get('label', None)
            if len(y) != len(labels):
                raise ValueError("labels are inadequate")
            kwargs.pop('label', None)
            for yv, lab in zip(y, labels):
                sns.lineplot(data=df, x=var_name, y=yv, label=lab, **kwargs)
        plt.title(f"{y} over {var_name}")
        if xlab:
            plt.xlabel(xlab)
        if ylab:
            plt.ylabel(ylab)
        plt.tight_layout()
        self._finalize(show, save_as)

    def scatter_plot(self, y: Union[str, list, tuple], *, xlab=None, ylab=None, x=None,
                     time='Year', table_name='Report', show=True, save_as='', **kwargs):
        """Plot scatter plot of a variable against a time field or x-axis."""
        self._refresh()
        var_name = time.capitalize()
        self.add_report_variable(f'[Clock].Today.{var_name} as {var_name}', table_name)
        pops = ['y', 'x']
        for p in pops:
            kwargs.pop(p, None)
        if x is None:
            self.run(report_name=table_name)
        else:
            var_name = x

        df = self.results

        if isinstance(y, str):
            sns.scatterplot(data=df, x=var_name, y=y, **kwargs)
        elif isinstance(y, (tuple, list)):
            labels = kwargs.get('label', y)
            if len(y) != len(labels):
                raise ValueError("labels are inadequate")
            kwargs.pop('label', None)
            for yv, lab in zip(y, labels):
                sns.scatterplot(data=df, x=var_name, y=yv, label=lab, **kwargs)

        plt.title(f"{y} over {var_name}")
        if xlab:
            plt.xlabel(xlab)
        if ylab:
            plt.ylabel(ylab)
        plt.tight_layout()
        self._finalize(show, save_as)

    def cat_plot(self, y, *, vary_by=None, x=None, time='Year', show =False, save_as='', **kwargs):
            self._refresh()
            """Plot time series of a variable against a time field. use seaborn.catplot"""
            var_name = time.capitalize()
            self.add_report_variable(f'[Clock].Today.{var_name} as {var_name}', 'Report')

            if x is None:
                self.run(report_name='Report')
            else:
                var_name = x
            if vary_by:
                kwargs['hue'] =vary_by
            df = self.results
            sns.catplot(data=df, x=var_name, y=y, **kwargs)
            plt.title(f"{y} over {var_name}")
            plt.tight_layout()
            self._finalize(show, save_as)

    def plot_correlation_heatmap(self, figsize=(10, 8), show =False, save_as=''):
        self._refresh()
        """Plot correlation heatmap for numeric _variables."""
        df = self._clean_numeric_data()
        if df.empty:
            print("No valid numeric data for correlation heatmap.")
            return

        corr = df.corr()
        plt.figure(figsize=figsize)
        sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f")
        plt.title("Correlation Heatmap")
        plt.tight_layout()
        self._finalize(show, save_as)

if __name__ == '__main__':
    from apsimNGpy.core.base_data import load_default_simulations
    scrach =Path.home()/'testss'
    scrach.mkdir(exist_ok=True)
    apsim = load_default_simulations(crop='Maize', simulations_object=False, set_wd= scrach)
    model = Diagnostics(apsim)
    model.add_report_variable(variable_spec='[Soil].Nutrient.TotalC[1]/1000 as SOC1', report_name='Report', set_event_names=['[Clock].EndOfYear', '[Maize].Harvesting'])
    model.add_db_table(variable_spec=['[Soil].Nutrient.TotalC[1]/1000 as SOC1', '[Soil].Nutrient.TotalC[2]/1000 as SOC2', '[Clock].Today.Year as Year'])
   # model.add_db_table(variable_spec=['[Soil].Nutrient.TotalC[2]/1000 as SOC2',])
    model.update_mgt(management=({"Name": 'Sow using a variable rule', 'Population': 8},))
    model.run(report_name='my_table')
    model.cat_plot(y='Yield', x = 'Zone' )

    model.line_plot(y=['SOC1', 'SOC2'], time='Year', table_name='my_table', show=False, ylab = 'Soil organic carbon(Mg^{-1})')
    model.plot_distribution('SOC1', show=False)
    #model.plot_distribution('Yield')
    model.run(report_name='Report')
    model.plot_correlation_heatmap()
    #model.get_weather_from_web(lonlat=(-93.50456, 42.601247), start=1990, end=2001, source='daymet')
