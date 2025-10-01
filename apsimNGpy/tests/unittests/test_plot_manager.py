from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.tests.unittests.base_unit_tests import BaseTester
from pathlib import Path
import matplotlib.pyplot as plt
import unittest

SHOW = False  # use this to turm of interactive plot in the panel
import tempfile


class TestPlotting(BaseTester):

    def setUp(self):
        """
        ApsimModel is defined here
        @return:
        """
        self.test_path = Path(f'test_plots{self._testMethodName}.apsimx').resolve()
        self.figure_name = Path(f'figure{self._testMethodName}.png').resolve()
        self.db_path = self.test_path.with_suffix('.db')
        self.bak_path = self.db_path.with_suffix('.bak')
        self.model = ApsimModel('Maize', out_path=self.test_path)

        self.model.run()

    def test_cat_plot(self):
        'test cat_plot for kind=points, default in seaborn'
        self.model.cat_plot(x='Clock.Today', y='Yield', table=None)
        fig_enum = plt.get_fignums()
        self.assertTrue(fig_enum)
        self.model.render_plot(save_as=self.figure_name, show=SHOW)
        # check if the figure was successfully saved on file
        self.assertGreater(self.figure_name.stat().st_size, 0, f'Empty figure detected in: {self._testMethodName}')
        # lastly close
        plt.close()

    def test_cat_plot_table_isNotNone(self):
        'test cat_plot for kind=points, default in seaborn'
        self.model.cat_plot(x='Clock.Today', y='Yield', table='Report')
        fig_enum = plt.get_fignums()
        self.assertTrue(fig_enum)
        self.model.render_plot(save_as=self.figure_name, show=SHOW)
        # check if the figure was successfully saved on file
        self.assertGreater(self.figure_name.stat().st_size, 0, f'Empty figure detected in: {self._testMethodName}')
        # lastly close
        plt.close()

    def test_cat_plot_kind_bar(self):
        """
        test cat_plot for kind=bar
        @return:
        """
        self.model.cat_plot(x='Clock.Today', y='Yield', kind='bar', orientation='vertical')
        fig_enum = plt.get_fignums()
        self.assertTrue(fig_enum)
        # labels, saving, and showing plots are aggregated in render_plots
        self.model.render_plot(save_as=self.figure_name, show=SHOW)
        # check if a figure was successfully saved on file
        fig_size = self.figure_name.stat().st_size

        self.assertGreater(fig_size, 0, f'Empty figure detected in: {self._testMethodName}')
        # lastly close
        plt.close()

    def test_cat_plot_kind_bar_table_is_notNone(self):
        """
        test cat_plot for kind=bar
        @return:
        """
        self.model.cat_plot(x='Clock.Today', y='Yield', kind='bar', table='Report', orientation='vertical')
        fig_enum = plt.get_fignums()
        self.assertTrue(fig_enum)
        # labels, saving, and showing plots are aggregated in render_plots
        self.model.render_plot(save_as=self.figure_name, show=SHOW)
        # check if a figure was successfully saved on file
        fig_size = self.figure_name.stat().st_size

        self.assertGreater(fig_size, 0, f'Empty figure detected in: {self._testMethodName}')
        # lastly close
        plt.close()

    def test_cat_plot_kind_box(self):
        """
        test cat_plot for kind=box
        @return:
        """
        self.model.cat_plot(x='Clock.Today', y='Yield', kind='box')
        fig_enum = plt.get_fignums()
        self.assertTrue(fig_enum)
        self.model.render_plot(save_as=self.figure_name, show=SHOW)
        # check if a figure was successfully saved on file
        self.assertGreater(self.figure_name.stat().st_size, 0, f'Empty figure detected in: {self._testMethodName}')
        # lastly close
        plt.close()

    def test_cat_plot_kind_box_tableisNotNone(self):
        """
        test cat_plot for kind=box
        @return:
        """
        self.model.cat_plot(x='Clock.Today', y='Yield', kind='box', table='Report')
        fig_enum = plt.get_fignums()
        self.assertTrue(fig_enum)
        self.model.render_plot(save_as=self.figure_name, show=SHOW)
        # check if a figure was successfully saved on file
        self.assertGreater(self.figure_name.stat().st_size, 0, f'Empty figure detected in: {self._testMethodName}')
        # lastly close
        plt.close()

    def test_relplot_kind_line(self):
        """
        test relative plot for kind=line
        @return:
        """
        self.model.relplot(x='Maize.Grain.Wt', y='Yield', kind='line')
        fig_enum = plt.get_fignums()
        self.assertTrue(fig_enum)
        self.model.render_plot(save_as=self.figure_name, show=SHOW)
        # check if a figure was successfully saved on file
        self.assertGreater(self.figure_name.stat().st_size, 0, f'Empty figure detected in: {self._testMethodName}')
        # lastly close
        plt.close()

    def test_line_plot(self):
        """test line_plot"""
        self.figure_name.unlink(missing_ok=True)

        self.model.series_plot(y='Yield', x='Clock.Today', table='Report')
        fig_enum = plt.get_fignums()
        self.assertTrue(fig_enum)
        # render before fig evaluation test because render closes the plot
        self.model.render_plot(save_as=self.figure_name, show=SHOW)
        # check if a figure was successfully saved on file
        self.assertGreater(self.figure_name.stat().st_size, 0, f'Empty figure detected in: {self._testMethodName}')
        plt.close()

    def test_distribution_plot(self):
        """
        test distribution_plot
        @return:
        """

        self.figure_name.unlink(missing_ok=True)
        self.model.distribution("Yield")
        fig_enum = plt.get_fignums()
        self.assertTrue(fig_enum)
        # labels, saving, and showing plots are aggregated in render_plots
        self.model.render_plot(save_as=self.figure_name, show=SHOW)
        # check if a figure was successfully saved on file
        self.assertGreater(self.figure_name.stat().st_size, 0, f'Empty figure detected in: {self._testMethodName}')
        plt.close()

    def test_scatter_plot(self):
        self.figure_name.unlink(missing_ok=True)
        self.model.scatter_plot(x='Maize.Grain.Wt', y='Yield')
        fig_enum = plt.get_fignums()
        self.assertTrue(fig_enum)
        self.model.render_plot(save_as=self.figure_name, show=SHOW)
        # check if the figure was successfully saved on file
        self.assertGreater(self.figure_name.stat().st_size, 0, f'Empty figure detected in: {self._testMethodName}')
        plt.close()

    def test_scatter_plot_with_tabl_isNone(self):
        self.figure_name.unlink(missing_ok=True)
        self.model.scatter_plot(x='Maize.Grain.Wt', y='Yield', table=None)
        fig_enum = plt.get_fignums()
        self.assertTrue(fig_enum)
        self.model.render_plot(save_as=self.figure_name, show=SHOW)
        self.assertGreater(self.figure_name.stat().st_size, 0, f'Empty figure detected in: {self._testMethodName}')
        plt.close()

    def test_scatter_plot_with_tabl_is_notNone(self):
        self.figure_name.unlink(missing_ok=True)
        self.model.scatter_plot(x='Maize.Grain.Wt', y='Yield', table='Report')
        fig_enum = plt.get_fignums()
        self.assertTrue(fig_enum)
        self.model.render_plot(save_as=self.figure_name, show=SHOW)
        self.assertGreater(self.figure_name.stat().st_size, 0, f'Empty figure detected in: {self._testMethodName}')
        plt.close()

    def tearDown(self):
        try:
            self.figure_name.unlink(missing_ok=True)

        except PermissionError:
            pass

        # cleans up everything related to the model stored on the computer
        self.clean_up_apsim_data(self.test_path)


if __name__ == '__main__':
    unittest.main()
