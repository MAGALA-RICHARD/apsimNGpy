import shutil
from contextlib import suppress
from pathlib import Path
import numpy as np
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.starter.starter import CLR
from uuid import uuid4

Models = CLR.Models
from apsimNGpy.core.sim_tools import get_root_model, create_factor_table
from typing import Any

NAME = "ExperimentFromFile"


def _create_experiment_from_file(model, experiment_from_file, name_column, sheet=None, base_simulation=0,
                                 experiment_name=NAME):
    """
    Create an APSIM experiment from an existing factor spreadsheet.

    This is a private helper used internally by
    `create_experiment_from_file`. Refer to the public function for
    complete documentation and usage examples.

    Parameters
    ----------
    model : str, pathlib.Path, or ApsimModel
        APSIM model path or an existing ``ApsimModel`` instance.

    experiment_from_file : str or pathlib.Path
        Path to the CSV or Excel file containing the factorial treatments.

    name_column : str
        Name of the column used to identify each generated simulation.

    sheet : str, optional
        Name of the Excel worksheet. Ignored when the factor file is a CSV.

    base_simulation : int or str, default=0
        Name or index of the simulation used as the template for the
        factorial experiment.

    experiment_name : str
        Name assigned to the generated APSIM experiment.

    Returns
    -------
    ApsimModel
        The root APSIM simulations object containing the newly created
        experiment
    ==========================================================
    """
    obj = get_root_model(model, simulation_name=base_simulation)
    root, base_sim = obj["root"], obj["simulation"]
    exp = Models.Factorial.Experiment()
    exp.Name = experiment_name
    factor_holder_node = Models.Factorial.Factors()
    exp.Children.Add(factor_holder_node)
    exp.Children.Add(base_sim)
    root.Simulations.Children.Add(exp)
    try:
        FactorialFactorFromFile = Models.Factorial.FactorFromFile()
    except AttributeError as error:
        raise RuntimeError(
            "This APSIM Next Generation version does not support "
            "'Models.Factorial.FactorFromFile'. Upgrade to APSIM 2026.7 "
            "or a newer version."
        ) from error
    FactorialFactorFromFile.set_NameColumn(name_column)
    if Path(experiment_from_file).suffix != '.csv':
        if sheet is None:
            raise ValueError(f"Expected sheet name to be specified got {sheet} instead")
        FactorialFactorFromFile.Sheet = sheet
    FactorialFactorFromFile.FileName = str(Path(experiment_from_file).resolve())
    factor_holder_node.Children.Add(FactorialFactorFromFile)

    return root


def _test_params(candidates: dict, func, model, output, base_sim=0):
    """
               Vary any factor and keep another constant to test
               @return:
               """
    vaRs = dict(candidates)
    # vaRs['[Sow using a variable rule].Script.CultivarName'] = ['Cultivar', "Cultivar"]
    X = create_factor_table(**vaRs, name_column='FactorFromFile')
    csf_file_name = f'tmp_{uuid4()}.csv'
    if isinstance(output, tuple):
        output = list(output)
    try:
        NAME_COLUMN = 'FactorFromFile'
        Path(csf_file_name).unlink(missing_ok=True)
        X.to_csv(csf_file_name)
        experiment = func(model, experiment_from_file=csf_file_name, base_simulation=base_sim,
                          name_column=NAME_COLUMN)
        experiment.run()
        res = experiment.results
        final = res.merge(X, how='inner', on=NAME_COLUMN)
        factor_levels = X["FactorFromFile"].nunique(dropna=False)
        output_columns = [output] if isinstance(output, str) else list(output)

        group_means = (
            final.groupby(NAME_COLUMN, dropna=False)[output_columns]
            .mean()
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

        return {
            "params": candidates,
            "passed": bool(changed_outputs),
            "changed_outputs": changed_outputs,
        }
    finally:
        with suppress(PermissionError):
            Path(csf_file_name).unlink(missing_ok=True)


def _pre_experiment_test(
        params: dict[str, tuple[Any, ...]] | list[dict[str, tuple[Any, ...]]],
        base_model: str | Path,
        outputs,
        base_simulation: int | str = 0,
        func=_create_experiment_from_file,
        use_threads: bool = True,
):
    """
    Test parameter paths before creating a large-scale experiment.

    Each parameter is tested against the base APSIM model to identify valid
    and invalid parameter paths.

    **params** : dict[str, tuple[Any, ...]] | list[dict[str, tuple[Any, ...]]]
        Parameter paths mapped to the values that should be tested.

    **base_model** : str | Path | object
        Base APSIM model or path to the model file.

    **base_simulation** : int, default=0
        Index of the simulation used for parameter testing.

    **func** : callable, default=_create_experiment_from_file
        Function used to create the experiment model.

    **use_threads** : bool, default=True
        Whether to use threads for parallel parameter testing.

    Returns
    -------
    dict
        A dictionary containing ``passed`` and ``failed`` parameter lists.
    """
    from pydantic import BaseModel, Field
    from apsimNGpy.parallel.process import custom_parallel

    class Params(BaseModel):
        params: list[dict[str, tuple[Any, ...]]] = Field(default_factory=list)

    if isinstance(params, dict):
        params = [{key: value} for key, value in params.items()]

    validated_params = Params(params=params)
    passed = []
    failed = []

    for result in custom_parallel(
            _test_params,
            validated_params.params,
            func,
            base_model,
            outputs,
            base_simulation,
            use_thread=use_threads,
    ):
        if result["passed"]:
            passed.append(result["params"])
        else:
            failed.append(result["params"])

    return {"passed": passed, "failed": failed}


def test_factor_from_file(*, rue, population):
    case1, case2 = tuple(rue), tuple(population)
    """
       Vary any factor and keep other constant to test
       @return:
       """
    vaRs = {"[Maize].Leaf.Photosynthesis.RUE.FixedValue": [*case1],
            '[Sow using a variable rule].Script.Population': [*case2]}
    X = create_factor_table(**vaRs, name_column="FactorFromFile")

    X.to_csv('data.csv')
    experiment = _create_experiment_from_file('Maize', experiment_from_file='data.csv', name_column='FactorFromFile')
    experiment.run()
    res = experiment.results
    final = res.merge(X, how='inner', on='FactorFromFile')
    mn = final.groupby('FactorFromFile')['Yield'].mean()
    assert len(mn) == len(X['FactorFromFile'].unique())

    assert not np.equal(*mn), f"Values {mn}  match"

    with experiment:
        pass


if __name__ == '__main__':

    vals = {"[Maize].Leaf.Photosynthesis.RUE.FixedValue": (1, 3, 2.5),
            '[Sow using a variable rule].Script.Population': (1, 12, 6)}
    out = _pre_experiment_test(vals, 'Maize', outputs=['Yield', 'Maize.Grain.Wt'])


    def clean(*args, **kwargs):
        from pathlib import Path
        from contextlib import suppress
        p = Path(kwargs.get('wd', '.')).resolve()
        import shutil
        for suffix in args:
            for i in p.rglob(f'*{suffix}'):
                if i.suffix == suffix:
                    with suppress(PermissionError, FileNotFoundError):
                        if i.is_dir():
                            shutil.rmtree(i)
                        else:
                            i.unlink()
                        print('removed {}'.format(i))


    clean('.db', '.apsimx', 'db-wal', '.met', '.scratch', '.csv')
