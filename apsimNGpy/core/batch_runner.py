from dataclasses import dataclass
from apsimNGpy.core.runner import _run_from_dir, get_matching_files
import pandas as pd
import polars as pl
from apsimNGpy.core_utils.database_utils import (read_db_table, get_db_table_names,custom_remove_file,
                                                 clear_all_tables, pl_save_todb)
from os.path import basename
from sqlalchemy import create_engine
from apsimNGpy.core_utils.utils import timer
from pathlib import Path
from datetime import datetime
import shutil, os, sys
from apsimNGpy.parallel.process import custom_parallel
from apsimNGpy.core.apsim import ApsimModel
DateTime =  datetime.now().strftime("%Y-%m-%d-%H%M%S")
@dataclass
class BatchRunner:
    path: str
    pattern: str = '*.apsimx'
    export_csv: bool = False
    recursive : bool = True
    verbose: bool = False
    results: pd.DataFrame = None
    def run(self, results = True):
        df = _run_from_dir(self.path, pattern=self.pattern, write_tocsv=self.export_csv,
                           verbose=self.verbose, recursive=self.recursive)
        self.results = list(df)
    def edit_run_model(self):
        find_files = []

        try:
            work_space = Path(self.path)/f'{DateTime}'
            # freshen work_space_exists:
            work_space.mkdir(parents=True, exist_ok=True)
            model = ApsimModel('Maize').replicate_file(k=200, path=work_space)
            try:
               find_files = get_matching_files(work_space, self.pattern)
            except FileNotFoundError:
                find_files = []
            if find_files:
                custom_parallel(custom_remove_file, find_files, progress_message='removing old files')
                print('success')
        finally:
            tl = custom_parallel(custom_remove_file, find_files, void = False, progress_message='Removing old files')
            list(tl)
            shutil.rmtree(work_space)
            ex = os.path.exists(work_space)
            print(ex)

        ...
    @timer
    def export_all_todb(self,database:str):
            database= database if database.endswith('.db') else database + '.db'
            pattern  =self.pattern.replace('.apsimx','.csv')
            csvs = get_matching_files(self.path, pattern, self.recursive)
            if  csvs:
                base_names = [Path(i).stem.split(".")[-1] for i in csvs]
                print(base_names)
                dfs = [pl.read_csv(c) for c in csvs if c is not None]
                datas= [(k, v) for k, v in zip(base_names, dfs)]

                list(custom_parallel(pl_save_todb, datas, database, 'replace', void =True, progress_message="saving data to {}".format(database)))

                ...
            else:
                print('No results')

if __name__ == '__main__':
    from pathlib import Path
    mock_data = Path.home() / 'mock_data'  # As an example let's mock some data move the apsim files to this directory before runnning
    mock_data.mkdir(parents=True, exist_ok=True)
    from apsimNGpy.core.base_data import load_default_simulations
    path_to_model = load_default_simulations(crop='maize', simulations_object=True)  # get base model
    ap = path_to_model.replicate_file(k=10, path=mock_data) if not list(mock_data.rglob("*.apsimx")) else None
    # df = run_from_dir(str(mock_data), pattern="*.apsimx", verbose=True,
    #                        recursive=True)  # all files that matches that pattern
    Batch = BatchRunner(mock_data, pattern='*.apsimx', export_csv=True, recursive=False, verbose=True)
    Batch.export_all_todb('dd')
    #Batch.edit_run_model()

