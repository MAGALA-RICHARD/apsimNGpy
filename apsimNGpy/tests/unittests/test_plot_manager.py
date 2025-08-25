from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.tests.unittests.base_unit_tests import BaseTester
from pathlib import Path
import matplotlib.pyplot as plt
import unittest
SHOW = False # use this to turm of interactive plot in the panel

class TestPlotting(BaseTester):

    def setUp(self):
        """
        ApsimModel is defined here
        @return:
        """
        self.test_path = Path(__file__).parent.joinpath(f'test_plots{self._testMethodName}.apsimx')
        self.figure_name = Path(__file__).parent.joinpath(f'figure{self._testMethodName}.png')
        self.db_path = self.test_path.with_suffix('.db')
        self.model = ApsimModel('Maize', out_path=self.test_path)
        self.model.run()


    def test_cat_plot(self):
        self.model.cat_plot(x="SimulationName", y= 'Yield')
        fig_enum = plt.get_fignums()
        self.assertTrue(fig_enum)
        self.model.render_plot(save_as=self.figure_name, show=SHOW)
        self.assertGreater(self.figure_name.stat().st_size, 0, f'Empty figure detected in: {self._testMethodName}')
        # lastly close
        plt.close()

    def test_line_plot(self):
        self.figure_name.unlink(missing_ok=True)
        self.model.series_plot(y='Yield', x='Clock.Today')
        fig_enum = plt.get_fignums()
        self.assertTrue(fig_enum)
        # render before fig evaluation test because render closes the plot
        self.model.render_plot(save_as=self.figure_name, show=SHOW)
        self.assertGreater(self.figure_name.stat().st_size, 0, f'Empty figure detected in: {self._testMethodName}')
        plt.close()

    def test_distribution_plot(self):
        self.figure_name.unlink(missing_ok=True)
        self.model.distribution("Yield")
        fig_enum = plt.get_fignums()
        self.assertTrue(fig_enum)
        self.model.render_plot(save_as=self.figure_name, show=SHOW)
        self.assertGreater(self.figure_name.stat().st_size, 0, f'Empty figure detected in: {self._testMethodName}')
        plt.close()

    def test_scatter_plot(self):
        self.figure_name.unlink(missing_ok=True)
        self.model.scatter_plot(x = 'Maize.Grain.Wt', y= 'Yield')
        fig_enum = plt.get_fignums()
        self.assertTrue(fig_enum)
        self.model.render_plot(save_as=self.figure_name, show=SHOW)
        self.assertGreater(self.figure_name.stat().st_size, 0, f'Empty figure detected in: {self._testMethodName}')
        plt.close()

    def test_scatter_plot_with_external_df(self):
        self.figure_name.unlink(missing_ok=True)
        df= self.model.results
        self.model.scatter_plot(x='Maize.Grain.Wt', y='Yield', data=df)
        fig_enum = plt.get_fignums()
        self.assertTrue(fig_enum)
        self.model.render_plot(save_as=self.figure_name, show=SHOW)
        self.assertGreater(self.figure_name.stat().st_size, 0, f'Empty figure detected in: {self._testMethodName}')
        plt.close()


    def tearDown(self):
            self.test_path.unlink(missing_ok=True)
            self.figure_name.unlink(missing_ok=True)
            self.db_path.unlink(missing_ok=True)
            self.model.clean_up(db=True)

if __name__ == '__main__':
    unittest.main()