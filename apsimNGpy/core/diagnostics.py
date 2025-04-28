import os
import subprocess
from pathlib import Path
from platform import system

import pandas as pd
import matplotlib.pyplot as plt
from summarytools import dfSummary
try:
    import seaborn as sns
except ModuleNotFoundError:
    print("Seaborn is not installed. Please install it to continue.")

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
        super().__init__(model, out_path, time='year', **kwargs)
        if not self.ran_ok:
            self.run()

    def _clean_numeric_data(self, exclude_vars=('SimulationID', 'CheckpointID', 'CheckpointName')):
        """Select numeric variables and remove low-signal columns."""
        df = self.results.select_dtypes(include="number").copy()

        # Drop excluded variables
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
    @property
    def summary(self):
        nums = self.results.select_dtypes(include="number").copy()
        return dfSummary(nums)
    def plot_distribution(self, variable):
        """Plot distribution for a numeric variable."""
        sns.histplot(data=self.results, x=variable, kde=True)
        plt.title(f"Distribution of {variable}")
        plt.tight_layout()
        plt.show()

    def plot_time_series(self, y, x=None, time='Year',table_name='Report', **kwargs):
        """Plot time series of a variable against a time field."""
        var_name = time.capitalize()
        self.add_report_variable(f'[Clock].Today.{var_name} as {var_name}', table_name)

        if x is None:
            self.run(report_name=table_name)
        else:
            var_name =x

        df = self.results
        sns.lineplot(data=df, x=var_name, y=y, **kwargs)
        plt.title(f"{y} over {var_name}")
        plt.tight_layout()

        output_path = HOME / 'series.png'
        plt.savefig(output_path)
        open_file(output_path)
        plt.close()
    def plot_categories(self, y, x=None, time='Year', **kwargs):
            """Plot time series of a variable against a time field."""
            var_name = time.capitalize()
            self.add_report_variable(f'[Clock].Today.{var_name} as {var_name}', 'Report')

            if x is None:
                self.run(report_name='Report')
            else:
                var_name = x

            df = self.results
            sns.catplot(data=df, x=var_name, y=y, **kwargs)
            plt.title(f"{y} over {var_name}")
            plt.tight_layout()

            output_path = HOME / 'category.png'
            plt.savefig(output_path)
            open_file(output_path)
            plt.close()
    def plot_correlation_heatmap(self, figsize=(10, 8)):
        """Plot correlation heatmap for numeric variables."""
        df = self._clean_numeric_data()
        if df.empty:
            print("No valid numeric data for correlation heatmap.")
            return

        corr = df.corr()
        plt.figure(figsize=figsize)
        sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f")
        plt.title("Correlation Heatmap")
        plt.tight_layout()

        output_path = HOME / 'heat.png'
        plt.savefig(output_path)
        open_file(output_path)
        plt.close()

if __name__ == '__main__':
    from apsimNGpy.core.base_data import load_default_simulations
    scrach =Path.home()/'testss'
    scrach.mkdir(exist_ok=True)
    apsim = load_default_simulations(crop='Maize', simulations_object=False, set_wd= scrach)
    model = Diagnostics(apsim)
    model.add_report_variable(variable_spec='[Soil].Nutrient.TotalC[1]/1000 as SOC1', report_name='Report', set_event_names=['[Clock].EndOfYear'])
    model.add_db_table(variable_spec=['[Soil].Nutrient.TotalC[1]/1000 as SOC1', '[Clock].Today.Year as Year'])
    model.update_mgt(management=({"Name": 'Sow using a variable rule', 'Population': 8},))
    model.run(report_name='my_table')

    model.plot_time_series(y='SOC1', time='Year', table_name='my_table')
    model.plot_distribution('SOC1')
    model.run(report_name='Report')
    model.plot_correlation_heatmap()
