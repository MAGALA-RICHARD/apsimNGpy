from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core_utils.database_utils import write_results_to_sql
from pathlib import Path

DATABAse = str(Path('test_custom.db').resolve())


@write_results_to_sql(DATABAse, table='Report', if_exists='append')
def worker(nitrogen_rate, model):
    out_path = Path(f"_{nitrogen_rate}.apsimx").resolve()
    model = ApsimModel(model, out_path=out_path)
    model.edit_model("Models.Manager", model_name='Fertilise at sowing', Amount=nitrogen_rate)
    model.run(report_name="Report")
    df = model.results
    # we can even create a column for each simulation
    df['nitrogen rate'] = nitrogen_rate

    model.clean_up()
    return df
