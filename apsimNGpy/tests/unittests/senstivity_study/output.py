from apsimNGpy.core_utils.database_utils import read_db_table, get_db_table_names
from main import DataBAse, soilPrefixes
from xlwings import view
tabs = get_db_table_names(DataBAse)
if __name__ == '__main__':
    sob = read_db_table(DataBAse,'SobolStatistics')
    result = (
                sob.groupby(['Parameter', 'ColumnName', 'Indices'])
                        .mean(numeric_only=True)
                        .unstack(['Indices', 'ColumnName'])
                    )
