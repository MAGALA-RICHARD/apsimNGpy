import argparse
from apsimNGpy.core_utils.utils import timer
from apsimNGpy.core.base_data import load_default_simulations
from apsimNGpy.settings import logger
from apsimNGpy.cli.model_desc import extract_models
import asyncio
from functools import lru_cache
from apsimNGpy.cli._args import parser
from apsimNGpy.cli.commands import (ApsimModel, os, sys, fetch_weather_data, replace_soil_from_web, create_experiment,replace_soil_data,pd,
                           np, print_msg, run_apsim_model, save_results, change_mgt )

async def main():
    # Create argument parser

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    # Parse arguments
    args = parser.parse_args()
    logger.info(f"Commands summary: '{args}'")
    if len(sys.argv) > 3:
        print_msg(msg='Processing in puts. Please wait!', normal=False)
    if  args.get_web_data !='no' and not args.lonlat:
        raise ValueError("attempting to fetch soil without supplying lonlat values")

    wd = args.wd or os.getcwd()
    os.makedirs(wd, exist_ok=True)

    met_form_loc = None

    if args.lonlat is not None:
        lonlat_tuple = tuple(map(float, args.lonlat.split(',')))
    else:
        lonlat_tuple = None

    if args.get_web_data == 'both' or args.get_web_data == 'w':

        met_form_loc = await fetch_weather_data(lonlat_tuple)




    file_name = args.save or f"out_{args.model.strip('.apsimx')}.csv"
    if args.lonlat and args.get_web_data == 's' or args.get_web_data == 'both':
        soilP = replace_soil_from_web(lonlat_tuple)

    if args.model.endswith('.apsimx'):
        model = ApsimModel(args.model, args.out, thickness_values=settings.SOIL_THICKNESS)
    else:
        model = load_default_simulations(crop=args.model, simulations_object=True, set_wd=wd)

    if args.inspect:
        print()
        # inspect returns after excecutions
        if args.inspect != 'file':
            model_type = args.inspect
            print_msg(model.inspect_model(model_type=model_type))

        else:
            model.tree()
        print()
        return

    model = await asyncio.to_thread(change_mgt, model, args)

    await asyncio.to_thread(replace_soil_data, model, args)
    met_data = args.met_file or met_form_loc
    if met_data:

        await asyncio.to_thread(model.replace_met_file, weather_file=met_data, simulations=args.simulation)
        msg = f'Successfully updated weather file with {met_data}'
        if args.lonlat:
            msg += f' from location: {args.lonlat}'
        print_msg(msg)

    if args.lonlat and args.get_web_data == 's' or args.get_web_data == 'both':
        await asyncio.to_thread(model.replace_downloaded_soils,soilP, model.simulation_names)
    if args.experiment:
        await create_experiment(model, args.experiment)
    # Run APSIM asynchronously
    model = await run_apsim_model(model, report_name=args.table)

    df = model.results

    if isinstance(df, pd.DataFrame):
        await save_results(df, file_name)
        numeric_df = df.select_dtypes(include=np.number)
        stati = getattr(numeric_df, args.aggfunc)()

        print_msg(stati)
    if args.save_model:
        model.save(args.save_model)
    if args.preview =='yes':
        model.preview_simulation()
    sys.exit(1)


@timer
def main_entry_point() -> None:
    asyncio.run(main())


# Run asyncio event loop
if __name__ == "__main__":

    main_entry_point()
    #-m maize -sf 'm.csv' --organic "node_path=.Simulations.Simulation.Field.Soil, Carbon=[1.2]"
