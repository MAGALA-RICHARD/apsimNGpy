import numpy as np
from apsimNGpy.core.apsim import ApsimModel


def test_experiment(*, experiment: ApsimModel, outputs, name_column, agg_func='sum'):
    try:
        NAME_COLUMN = name_column
        experiment.run()
        res = experiment.results

        factor_levels = res[NAME_COLUMN].nunique(dropna=False)
        output_columns = [outputs] if isinstance(outputs, str) else list(outputs)

        group_means = (
            getattr(res.groupby(NAME_COLUMN, dropna=False)[output_columns], agg_func)()

        )

        if len(group_means) != factor_levels:
            raise ValueError(
                f"Expected {factor_levels} factor groups, but found "
                f"{len(group_means)}."
            )

        # Compare every factor level with the first level for each output.
        is_unchanged = np.all(
            np.isclose(
                group_means.to_numpy(dtype=float),
                group_means.iloc[0].to_numpy(dtype=float),
                rtol=1e-5,
                atol=1e-8,
                equal_nan=True,
            ),
            axis=0,
        )

        changed_outputs = [
            column
            for column, unchanged in zip(output_columns, is_unchanged)
            if not unchanged
        ]

        with experiment:
            pass
        return changed_outputs

    finally:
        ...


def build_test_results(candidates, changed_outputs, outputs):
    ch = {
        "params": candidates,
        "passed": bool(changed_outputs),
        "changed_outputs": changed_outputs,
    }
    if isinstance(outputs, str):
        outputs = [outputs]
    unchanged = set(outputs) - set(ch['changed_outputs'])
    ch['failed_outputs'] = list(unchanged)
    return ch
