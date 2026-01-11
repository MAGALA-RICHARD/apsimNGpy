from apsimNGpy.manager.weathermanager import get_nasa, get_weather, read_apsim_met
lonlat = [(-9.0, 36.6), (-9.30, 37.7)]

df = [get_weather(i, start = 1984, end = 2024, source='nasa', filename=f"nasa_{i}.met") for i in lonlat ]
names =  ['nasa_(-9.0, 36.6).met', 'nasa_(-9.3, 37.7).met']
columns = ["year", "day", "radn", "maxt", "mint", "rain"]

dm = [read_apsim_met(i, skip=6) for i in names]

for df, nam in zip(dm, names):
    saveto = nam.replace('met', 'csv')
    df.columns = columns
    df.to_csv(saveto)