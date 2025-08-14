if True:

    from apsimNGpy.core.apsim import ApsimModel
    from pathlib import Path
    # instantiate the model
    model = ApsimModel(model='Maize', out_path = 'new_maize.apsimx')
    # change the planting density
    model.edit_model(model_type='Models.Manager', model_name='Sow using a variable rule', Population =12)
    # download and replace weather data automatically
    lonlat=  (-93.44, 41.1234)
    model.get_weather_from_web(lonlat = lonlat, start=1981, end=2022, source='daymet')
    # change the start and end date
    model.edit_model(model_type='Models.Clock', model_name='Clock', start="1990-01-01", end="2021-12-31",) # ISO 8601 format (YYYY-MM-DD)
    # run the model
    model.run(report_name="Report")
    # get results
    df = model.results
    # save the model
    filename = str(Path(f'my_edited_maize_model_at{lonlat}.apsimx').resolve())
    model.save(file_name=filename)



