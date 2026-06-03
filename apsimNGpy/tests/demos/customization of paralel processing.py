from pathlib import Path
from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core_utils.database_utils import read_db_table
from apsimNGpy.parallel.process import custom_parallel
import pandas as pd
from sqlalchemy import create_engine


DATABAse = str(Path('test_custom.db').resolve())

# define function to insert insert results
def insert_results(db_path, results, table_name):
    """
    Insert a pandas DataFrame into a SQLite table.

    Parameters
    ----------
    db_path : str or Path
        Path to the SQLite database file.
    results : pandas.DataFrame
        DataFrame to insert into the database.
    table_name : str
        Name of the table to insert the data into.
    """
    if not isinstance(results, pd.DataFrame):
        raise TypeError("`results` must be a pandas DataFrame")

    engine = create_engine(f"sqlite:///{db_path}")
    results.to_sql(table_name, con=engine, if_exists='append', index=False)


def worker(nitrogen_rate, model):
    out_path = Path(f"_{nitrogen_rate}.apsimx").resolve()
    model = ApsimModel(model, out_path=out_path)
    model.edit_model("Models.Manager", model_name='Fertilise at sowing', Amount=nitrogen_rate)
    model.run(report_name="Report")
    df = model.results
    # we can even create column for each simulation
    df['nitrogen rate'] = nitrogen_rate
    insert_results(DATABAse, df, 'Report')
    model.clean_up()


if __name__ == '__main__':

    for _ in custom_parallel(worker, range(0, 400, 10), 'Maize', n_cores=6, use_threads=False):
        pass
    # get the results
    data = read_db_table(DATABAse, report_name="Report")
