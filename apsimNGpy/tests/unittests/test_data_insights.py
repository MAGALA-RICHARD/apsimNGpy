# test_mva_unittest.py
import math
import unittest
import numpy as np
import pandas as pd


# from stats.data_insights import mva
from apsimNGpy.stats.data_insights import mva


class TestMVA(unittest.TestCase):
    def setUp(self):
        # 5-point ramp with unsorted index to test "restore original order"
        df = pd.DataFrame(
            {"t": [1, 2, 3, 4, 5], "y": [1.0, 2.0, 3.0, 4.0, 5.0]},
            index=[10, 12, 14, 16, 18],
        )
        # Shuffle deterministically; keep for tests that rely on original order
        self.simple_df = df.sample(frac=1.0, random_state=0)

    # ---------- Core behavior ----------


    def _expected_by_t(self, df, window, min_period, preserve_start):
        # compute expected on t-sorted data, then map back to original order
        df_sorted = df.sort_values("t")
        s = df_sorted["y"]
        r = s.rolling(window=window, center=True, min_periods=min_period).mean()
        if preserve_start and window > 1:
            k = window // 2
            if len(s) > k:
                r.iloc[:k] = s.iloc[:k]
            else:
                r = s.copy()
        # map t -> expected value
        t_to_val = dict(zip(df_sorted["t"].tolist(), r.tolist()))
        # return list aligned to original (shuffled) order
        return [t_to_val[t] for t in df["t"].loc[df.index].tolist()]

    def test_no_grouping_preserve_start(self):
        res = mva(
            self.simple_df, time_col="t", response="y",
            window=3, min_period=1, grouping=None, preserve_start=True
        )
        out = res["y_roll_mean"].loc[self.simple_df.index].to_list()
        expected = self._expected_by_t(self.simple_df, window=3, min_period=1, preserve_start=True)
        self.assertTrue(np.allclose(out, expected, equal_nan=False))

    def test_no_grouping_no_preserve(self):
        res = mva(
            self.simple_df, time_col="t", response="y",
            window=3, min_period=1, grouping=None, preserve_start=False
        )
        out = res["y_roll_mean"].loc[self.simple_df.index].to_list()
        expected = self._expected_by_t(self.simple_df, window=3, min_period=1, preserve_start=False)
        self.assertTrue(np.allclose(out, expected, equal_nan=False))

    def test_min_period_full_required_edges_nan(self):
        df = pd.DataFrame({"t": [1, 2, 3, 4, 5], "y": [1, 2, 3, 4, 5]})
        # With window=5 and min_period=5 and no preserve_start, only the center has value
        res = mva(df, time_col="t", response="y", window=5, min_period=5,
                  grouping=None, preserve_start=False)
        out = res["y_roll_mean"].to_list()
        self.assertTrue(math.isnan(out[0]) and math.isnan(out[1]))
        self.assertAlmostEqual(out[2], 3.0, places=7)
        self.assertTrue(math.isnan(out[3]) and math.isnan(out[4]))

    def test_grouping_two_levels_independent(self):
        # Two groups share the same pattern; each should smooth independently
        df = pd.DataFrame(
            {
                "Residue": ["Yes"] * 5 + ["No"] * 5,
                "Nitrogen": ["High"] * 5 + ["High"] * 5,
                "t": list(range(1, 6)) * 2,
                "y": [1, 2, 3, 4, 5] * 2,
            }
        )
        print(df)
        res = mva(df, time_col="t", response="y", window=3, grouping=("Residue", "Nitrogen"))
        expected = [1.0, 2.0, 3.0, 4.0, 4.5] * 2  # preserve_start=True by default
        self.assertTrue(np.allclose(res["y_roll_mean"].to_numpy(), np.array(expected), equal_nan=False))

    def test_nan_groups_are_retained(self):
        df = pd.DataFrame(
            {
                "G": ["A", np.nan, "A", np.nan, "B", "B"],
                "t": [1, 1, 2, 2, 1, 2],
                "y": [1.0, 10.0, 3.0, 30.0, 100.0, 200.0],
            }
        )
        res = mva(df, time_col="t", response="y", window=3, grouping="G", preserve_start=False)
        # No rows dropped
        self.assertEqual(len(res), len(df))
        # Rows in the NaN group should still get computed values (some may be NaN due to edges, but not all)
        idx_nan = df["G"].isna()
        self.assertTrue(idx_nan.any())
        self.assertTrue(res.loc[idx_nan, "y_roll_mean"].notna().any())

    def test_non_numeric_response_is_coerced(self):
        df = pd.DataFrame({"t": [1, 2, 3], "y": ["1", "x", "3"]})
        res = mva(df, time_col="t", response="y", window=3, min_period=1,
                  grouping=None, preserve_start=False)
        # After coercion: y -> [1, NaN, 3]; centered mean with partial windows
        out = res["y_roll_mean"].to_list()
        expected = [1.0, 2.0, 3.0]
        self.assertTrue(np.allclose(out, expected, equal_nan=False))

    def test_restores_original_row_order(self):
        original_idx = self.simple_df.index.to_list()
        res = mva(self.simple_df, time_col="t", response="y", window=3, grouping=None)
        self.assertEqual(res.index.to_list(), original_idx)

    # ---------- Validation / error handling ----------

    def test_raises_on_non_dataframe(self):
        with self.assertRaises(TypeError):
            mva([], time_col="t", response="y")  # type: ignore[arg-type]

    def test_raises_on_missing_columns(self):
        with self.assertRaises(KeyError):
            mva(self.simple_df.drop(columns=["t"]), time_col="t", response="y")

    def test_raises_on_missing_grouping_col(self):
        with self.assertRaises(KeyError):
            mva(self.simple_df, time_col="t", response="y", grouping="does_not_exist")

    def test_raises_on_invalid_window(self):
        with self.assertRaises(ValueError):
            mva(self.simple_df, time_col="t", response="y", window=0)

    def test_raises_on_invalid_min_period(self):
        with self.assertRaises(ValueError):
            mva(self.simple_df, time_col="t", response="y", window=3, min_period=0)
        with self.assertRaises(ValueError):
            mva(self.simple_df, time_col="t", response="y", window=3, min_period=4)


if __name__ == "__main__":
    unittest.main()
