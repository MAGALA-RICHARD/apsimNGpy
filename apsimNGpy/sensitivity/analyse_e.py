from apsimNGpy.core_utils.database_utils import read_db_table, get_db_table_names
from pathlib import Path

db = Path(r"D:\sensitivity_study\Data\fast_results.db")
df = read_db_table(db, 'fast_raw_results')
stats = read_db_table(db, 'fast_statistics')
stat = read_db_table(db, )
df =df[df['Yield']!=0]
# calculate normalize prediction range
stats.groupby(['names', 'Nrate'])[['S1', 'ST']].mean()