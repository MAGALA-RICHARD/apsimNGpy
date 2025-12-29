from pathlib import Path
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core_utils.database_utils import write_results_to_sql
from apsimNGpy.exceptions import ApsimRuntimeError

aggs = {'sum', 'mean', 'max', 'min', 'median', 'std'}


def _runner(model: str,
            agg_func: str,
            incomplete_jobs: set | list,
            db, if_exists='append',
            table_prefix = '__'):
    @write_results_to_sql(db_path=db, if_exists=if_exists)
    def _inside_runner():
        """
        This is the worker for each simulation.

        The function performs two things; runs the simulation and then inserts the simulated data into a specified
        database.

        :param model: str, dict, or Path object related .apsimx json file

        returns None
        """
        # initialize the apsimNGpy model simulation engine
        with ApsimModel(model) as _model:
            table_names = _model.inspect_model('Models.Report', fullpath=False)
            # we want a unique report for each crop, because they are likely to have different database schemas
            crops = _model.inspect_model('Models.PMF.Plant', fullpath=False)
            crop_table = [f"{a}_{b}" for a, b in zip(table_names, crops)]
            tables = '_'.join(crop_table)
            tables = f'{table_prefix}_{tables}'
            # run the model. without specifying report names, they will be detected automatically
            try:
                _model.run()
                # aggregate the data using the aggregated function
                if agg_func:
                    if agg_func not in aggs:
                        raise ValueError(f"unsupported aggregation function {agg_func}")
                    dat = _model.results.groupby('source_table')  # if there are more than one table, we do not want to
                    # aggregate them together
                    out = dat.agg(agg_func, numeric_only=True)

                    out['source_name'] = Path(model).name

                else:
                    out = _model.results
                # track the model id
                out['source_name'] = Path(model).name
                # return data in a format that can be used by the decorator writing data to sql

                return {'data': out, 'table': tables}

            except ApsimRuntimeError:
                if isinstance(incomplete_jobs, list):
                    incomplete_jobs.append(_model.path)
                elif isinstance(incomplete_jobs, set):
                    incomplete_jobs.add(_model.path)
    _inside_runner()
