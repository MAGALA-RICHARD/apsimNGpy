from sqlalchemy import create_engine

from apsimNGpy.core.apsim import ApsimModel
from typing import List, Iterable, Any

from apsimNGpy.core._tiny_core import _assemble_simulations, _run_batch_simulations, _SimulationDescription


class SimulationDescription(_SimulationDescription):
    """
        Description of an APSIM simulation and its optional model edits (payload).

        Parameters
        ----------
        model : str
            Name or path of the base APSIM model used to create the simulation.

        ID : int
            Unique identifier assigned to the simulation description.

        payload : list[dict[str, Any]], default=[]
            A collection of parameter-edit dictionaries applied to the simulation.

            Each payload dictionary may contain strings, numbers, lists, nested
            dictionaries, or other values required by the APSIM editing methods.
            When no edits are required, this field defaults to an empty list.

        Examples:
        ------------
        Create a simulation description containing one model edits:
            .. code-block:: python

            description = SimulationDescription(
                model="Maize",
                ID=1,
                payload=[
                    {
                        "model_name": "Fertilise at sowing",
                        "model_type": "Models.Manager",
                        "Amount": 100,
                    }
                ],
            )

        Nested dictionaries are also accepted:

        .. code-block:: python

            description = SimulationDescription(
                model="Maize",
                ID=2,
                payload=[
                    {
                        "model_name": "Sowing",
                        "model_type": "Models.Manager",
                        "parameters": {
                            "population": 8.5,
                            "depth": 50,
                            "cultivar": "Pioneer",
                        },
                    }
                ],
            )

        A description may also be created without a payload:

        .. code-block:: python

            description = SimulationDescription(
                model="Maize",
                ID=3,
            )

            print(description.payload)
            # []

        """


def assemble_simulations(
        simulations: List[ApsimModel],
        max_workers: int = 20,
        show_progress: bool = True,
) -> ApsimModel:
    """
    Assemble multiple APSIM simulations into one model.

    Parameters
    ----------
    simulations : iterable
        APSIM Simulation objects to add to the combined model.
    max_workers : int, default=20
        Maximum number of worker threads used during assembly.
    show_progress : bool, default=True
        Whether to display assembly progress.

    Returns
    -------
    ApsimModel
        The assembled APSIM model. Simulations are not executed.
    """
    return _assemble_simulations(simulations, max_workers, show_progress)


def run_batch_simulations(
        simulation_descriptions: Iterable[
            SimulationDescription | dict[str, Any]
            ],
        max_worker: int = 20,
        reports: Iterable = None,
        show_progress: bool = True,
):
    """
    Run a batch of APSIM simulations aggregated in a single .apsimx file and return their results.

    Parameters
    ----------
    simulation_descriptions : iterable of dict
        Definitions used to create and configure the simulations.
    max_worker : int, default=20
        Maximum number of workers used during assembly and execution.
    reports : str or sequence of str, optional
        APSIM report table name or names to retrieve.
    show_progress : bool, default=True
        Whether to display simulation-assembly progress.

    Returns
    -------
    pandas.DataFrame
        Results from the completed batch.

    # Examples
    ----------------
    .. code-block:: python

         from apsimNGpy.core.tiny_core import run_batch_simulations, SimulationDescription

    Create a simulation description

     .. code-block:: python

        def plod(i):
            return {'model_name': "Fertilise at sowing", "model_type": "Models.Manager",
                    'Amount': i}
        p_loads = [
            SimulationDescription(**{"model": "Maize", "ID": i, 'payload': [plod(i)]})
            for i in list(range(1, 81, 1))]
        df = run_batch_simulations(simulation_descriptions=p_loads, )
        df_mean = (df.groupby("SimName")["Yield"]
            .mean()
            .sort_index(ascending=True))

    The SimulationDescription class is used only to validate inputs. Users may still pass a list of dictionaries,
    and the program will validate and convert each dictionary internally.

    """
    return _run_batch_simulations(simulation_descriptions, max_worker, reports, show_progress)


def save_batch_simulations(simulation_descriptions: Iterable[ SimulationDescription | dict[str, Any]],  db_path: str,
                           max_worker: int = 20,
                           reports: Iterable = None,
                           show_progress: bool = True, table_prefix='batch' ):
    df = run_batch_simulations(simulation_descriptions,
                               max_worker,
                               reports,
                               show_progress)
    engine = create_engine(f"sqlite:///{str(db_path)}")
    shape = int(df.shape[0]/3)
    with engine.begin():
        df.to_sql(f"{table_prefix}Batch", engine, if_exists="append", chunksize=shape, method="multi", index=False)


if __name__ == '__main__':
    def lod(i):
        return {'model_name': "Fertilise at sowing", "model_type": "Models.Manager",
                'Amount': i}


    ploads = [
        SimulationDescription(**{"model": "Maize", "ID": i, 'payload': [lod(i)]})
        for i in list(range(1, 81, 1))
    ]

    op = run_batch_simulations(simulation_descriptions=ploads, )
    op_mean = (
        op.groupby("SimName")["Yield"]
        .mean()
        .sort_index(ascending=True)
    )
