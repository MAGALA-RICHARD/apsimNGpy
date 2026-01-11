from apsimNGpy.core.apsim import ApsimModel
from apsimNGpy.core.config import load_crop_from_disk

with ApsimModel('Report') as model:
    sims = model.simulations_list
    print(sims)
    ['SimpleReportingSim', 'Annual Reporting In June', 'ContinuousWheatExample', 'Seasonal']
    print(model.tables_list)
    ['ReportSimple', 'ReportOnEvents', 'ReportOnSpecificDaysEveryYear', 'ReportOnSpecificDates', 'ReportArrays',
     'ReportDaily', 'ReportWeekly', 'ReportMonthly', 'ReportYearly', 'ReportSimulation', 'AnnualReporting',
     'MonthlyReporting', 'DailyReporting', 'ReportInCropAnnually', 'ReportGrainOnHarvesting', 'ReportGrainDaily',
     'ReportSpecificDates', 'SeasonalOverall', 'SeasonalByYear', 'SeasonalByYearWithOnKeyword']
    model.inspect_model('Models.Manager')
    ['.Simulations.SimpleReportingSim.Field.Sowing',
     '.Simulations.SimpleReportingSim.Field.Fertilise at sowing',
     '.Simulations.SimpleReportingSim.Field.Harvest',
     '.Simulations.SimpleReportingSim.Field.AutoIrrig',
     '.Simulations.SimpleReportingSim.Field.ReportHelper',
     '.Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Field.CutRotation',
     '.Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Field.AutomaticFertiliser',
     '.Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Field.FertiliseOnFixedDates',
     '.Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Field.AutomaticIrrigation',
     '.Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Field.ReportHelper',
     '.Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.Field.Sowing',
     '.Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.Field.Fertilise at sowing',
     '.Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.Field.Harvest',
     '.Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.Field.ReportHelper',
     '.Simulations.Grouping.Seasonal.ClimateController',
     '.Simulations.Grouping.Seasonal.Field.AutomaticIrrigation']
    model.inspect_model('Models.Clock')
    ['.Simulations.SimpleReportingSim.Clock',
     '.Simulations.More Reporting Examples.Perennial Crop Example.Annual Reporting In June.Clock',
     '.Simulations.More Reporting Examples.Annual Crop Example.ContinuousWheatExample.Clock',
     '.Simulations.Grouping.Seasonal.Clock']
    model.inspect_model_parameters_by_path('.Simulations.Grouping.Seasonal.Field.AutomaticIrrigation')
    model.edit_model_by_path('.Simulations.Grouping.Seasonal.Field.AutomaticIrrigation', returndays=3, maximumAmount=20)
    model.edit_model(model_type='Models.Manager', model_name='AutomaticIrrigation', simulations='Seasonal', returndays=3, maximumAmount=21)
from apsimNGpy.core.model_tools import ModelTools, CastHelper
import Models
with ApsimModel('Morris') as morris:

    mo = ModelTools.find_child(morris.Simulations, child_class= 'Models.Morris', child_name= 'FallowSensitivity')
    mo = CastHelper.CastAs[Models.Morris](mo)
    print(mo)
    for i in dir(mo):
        print(i)
    print(list(mo.get_Parameters()))
    ld = list(mo.get_Parameters())

