from apsimNGpy.sensitivity.sens_file import ConfigProblem, evaluate_model_sensitivity
import numpy as np
import unittest

Years = 10
Total = Years * 2 * 2


def all_equal(arr):
    arr = np.asarray(arr)

    if arr.size == 0:
        return True

    return np.all(arr == arr.flat[0])


def is_consecutive(arr):
    arr = np.asarray(arr)
    return np.all(np.diff(arr) == 1)


def change_report(model):
    model.edit_model('Models.Report', model_name='Report', variable_spec=['[Clock].Today.Year as Year'], )


class TestFileBaseSensitivity(unittest.TestCase):
    def setUp(self):
        self.params = {
            "[Fertilise at sowing].Script.Amount": (0.0, 300),
            '[Maize].Leaf.Photosynthesis.RUE.FixedValue': (1, 2.5)

        }
        self.outputs = ["Yield", 'Maize.AboveGround.Wt']
        self.names = ['Nitrogen', 'RUE', ]
        self.test_problem = ConfigProblem(

            base_model="Maize",
            params=self.params,
            outputs=self.outputs,
            names=self.names,
            apsim_result_tables=["Report"],
            apsim_model_callback=change_report

        )

    def test_evaluate_model_sensitivity(self):
        se = evaluate_model_sensitivity(
            self.test_problem,
            method="fast",
            N=102,
            agg_func="sum",
            chunk_size=50,
            retry_rate=2,
            grouping=['Year'],
            sample_options={
                "num_levels": 6,
                "optimal_trajectories": 10,
            },
            analyze_options={
                "num_resamples": 500,
                "print_to_console": False,
            },
        )

        sens = se.sensitivity
        self.assertTrue(sens.shape[0] == Total)
        result = (
            sens.groupby(["names", "Response"])["Year"]
            .apply(is_consecutive)
        )
        if not all(result):
            print(result)
        self.assertTrue(all(result), "results are not consecutive based on the grouping column year")
        self.assertFalse(all_equal(sens.ST))
        self.assertFalse(all_equal(sens.S1))

        ##########################################

    def test_grouping_is_none_fast(self):
        no_rgp = evaluate_model_sensitivity(
            self.test_problem,
            method="fast",
            N=102,
            agg_func="sum",
            chunk_size=50,
            retry_rate=2,
            grouping=None,
            sample_options={
                "num_levels": 6,
                "optimal_trajectories": 10,
            },
            analyze_options={
                "num_resamples": 500,
                "print_to_console": False,
            },
        )
        self.assertIn('names', no_rgp.sensitivity)
        self.assertTrue(no_rgp.sensitivity.shape[0] == len(self.names) * len(self.outputs))
        self.assertFalse(all_equal(no_rgp.sensitivity.ST))
        self.assertFalse(all_equal(no_rgp.sensitivity.S1))

    def test_grouping_is_none_sobol(self):
        no_rgp = evaluate_model_sensitivity(
            self.test_problem,
            method="sobol",
            N=2**6,
            agg_func="sum",
            chunk_size=50,
            retry_rate=2,
            grouping=None,
            sample_options={
                "num_levels": 6,
                "optimal_trajectories": 10,
                'calc_second_order': False
            },
            analyze_options={
                "num_resamples": 500,
                "print_to_console": False,
            },
        )
        self.assertTrue(no_rgp.sensitivity.shape[0] == len(self.names) * len(self.outputs))
        self.assertFalse(all_equal(no_rgp.sensitivity.ST))
        self.assertFalse(all_equal(no_rgp.sensitivity.S1))

    def test_grouping_is_none_sobol_second_order(self):
        no_rgp = evaluate_model_sensitivity(
            self.test_problem,
            method="sobol",
            N=2**6,
            agg_func="sum",
            chunk_size=50,
            retry_rate=2,
            grouping=None,
            sample_options={
                "num_levels": 6,
                "optimal_trajectories": 10,
                'calc_second_order': True
            },
            analyze_options={
                "num_resamples": 500,
                "print_to_console": True,
                'calc_second_order': True
            },
        )
        print(no_rgp.sensitivity.columns)
       # self.assertTrue(no_rgp.sensitivity.shape[0] == len(self.names) * len(self.outputs))
        self.assertFalse(all_equal(no_rgp.sensitivity.ST))
        self.assertFalse(all_equal(no_rgp.sensitivity.S1))


if __name__ == '__main__':
    unittest.main()
