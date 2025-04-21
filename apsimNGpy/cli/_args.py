import argparse
from apsimNGpy.cli.set_ups import ColoredHelpFormatter
from apsimNGpy.cli.commands import change_mgt
parser = argparse.ArgumentParser(description='\033[91mRun a simulation of a given crop.\033[0m',
                                 formatter_class=ColoredHelpFormatter)

# Add arguments
parser.add_argument('-m', '--model', type=str, required=False,
                    help='Path  or name of the APSIM model file if path it should ends with .apsimx'
                         'defaults to maize from the default '
                         'simulations ', default='Maize')
parser.add_argument('-o', '--out', type=str, required=False, help='Out path for apsim file')
parser.add_argument('-mg', '--management', type=str, required=False, help=f'{change_mgt.__doc__}')
parser.add_argument('-p', '--preview', type=str, required=False, choices=('yes', 'no'), default='no',
                    help='Preview or start model in GUI')
parser.add_argument('-sv', '--save', type=str, required=False,
                    help='Out path for apsim file to save after making changes')
parser.add_argument('-t', '--table', type=str, required=False, help='Report table name. '
                                                                    'Defaults to "Report"')
parser.add_argument('-w', '--met_file', type=str, required=False, help="Path to the weather data file.")
parser.add_argument('-i', '--inspect', type=str, required=False, help=f"inspect your model to get the model paths.")
parser.add_argument('-sim', '--simulation', type=str, required=False, help='Name of the APSIM simulation to run')
parser.add_argument('-ws', '--wd', type=str, required=False, help='Working directory')
parser.add_argument('-l', '--lonlat', type=str, required=False, help='longitude and Latitude (comma-separated) '
                                                                     'for fetching weather data.')
parser.add_argument('-sm', '--save_model', type=str, required=False, help='File name for saving output data.')
parser.add_argument('-s', '--aggfunc', type=str, required=False, default='mean',
                    help='Statistical summary function (e.g., mean, median). Defaults to "mean". Useful for quick diagnostics,'
                         'but real data is stored in csf file')
parser.add_argument('-og', '--organic', type=str,
                    required=False,
                    help="Replace any soil data through a soil organic parameters and path specification"
                         " e.g, 'node_path=.Simulations.Simulation.Field.Soil, Carbon=[2.2]'")
parser.add_argument('-ph', '--physical', type=str,
                    required=False,
                    help="Replace any soil data through a soil physical parameters and path specification"
                         " e.g, 'node_path=.Simulations.Simulation.Field.Soil, BD=[1.2]'")
parser.add_argument('-ch', '--chemical', type=str,
                    required=False,
                    help="Replace any soil data through a soil chemical parameters and path specification"
                         " e.g, 'node_path=.Simulations.Simulation.Field.Soil, NH4=[2.2]'")

parser.add_argument('-fw', '--get_web_data', type=str, required=False, choices=['both', 's', 'w', 'no'],
                    default='no', help=' if lonlat arguments is provided, get soil or weather data'
                                       ' w flag get weather and s flag gets soil data while both will download both')
parser.add_argument('-e', '--experiment', type=str, required=False,
                    help="set experiment by providing the specification in the form of a string."
                         "Different specifications are seperated by a  full colon."
                         "Edits like changing management practices or soils variables will be made before creating the experiment ")
