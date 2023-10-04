import os, sys, time
from apsimx import apsimx2py
import apsimx.apsimx2py
from apsimx.soil2apsimx import ApsimSoil
import numpy as np
import glob
from multiprocessing import Queue
thickness = [150, 150, 200, 200, 200, 250, 300, 300, 400, 500]
base = os.path.dirname(__file__)
fil = os.path.join(base, 'basefiles')
apsimx_prototype = os.path.join(fil, 'corn_base.apsimx')
SWIM3 = os.path.join(fil, 'SWIM2.apsimx')
test = os.path.join(fil, 'testx.apsimx')
EXPERIMENT = os.path.join(fil, 'EXPERIMENT.apsimx')
EXPERIMENT_NT = os.path.join(fil, 'EXPERIMENT_NT.apsimx')
import multiprocessing
lonlat = [-93.620369, 42.034534], [-93.76944799,42.39200539], [-93.63052528,	42.39736169], [-93.68445637,	42.39704733]
#_______________________________________________________________________



path_files  = r'D:\wd\nf\Weather_APSIM_Files'
os.chdir(path_files)
aps_list = glob.glob1(path_files, '*_2py.apsimx')
aps_list = aps_list[:20]
def Worker(idx):
        try:

            aps = ApsimSoil(idx, copy =False)
            aps.run_edited_file(multithread=False)
            results =aps.results
            mean_n20 = np.mean(results['Annual']['TopN2O'])
            MineralN = np.mean(results['Annual']['MineralN'])
            MineralN = np.mean(results['Annual']['MineralN'])
            leached_N = np.mean(results['Annual']['CumulativeAnnualLeaching'])
            carbon = np.mean(results['Carbon']['changeincarbon']) * -1
            # MineralN = self.get_result_stat(self.results['Annual'], 'MineralN', 'mean')
            Myield = np.mean(results['MaizeR']['Yield'])
            prof_maize = Myield / 25.40 * 4.6650
            Total_prof = prof_maize
            Syield = None
            ghg_co2_co2eq = -1 * carbon * 44 / 128 * 1
            ghg_n02_co2eq = mean_n20 * 44 / 28 * 298
            co2_eq = ghg_co2_co2eq + ghg_n02_co2eq

            if "Soybean" in aps.extract_user_input('Simple Rotation')['Crops']:
                  Syield = np.array(results['SoybeanR']["Yield"])[-1]
                  if Syield:
                        Total_prof = prof_maize + Syield / 27.2155 * 13.6100
            data = idx, mean_n20, carbon * -1, MineralN, leached_N, Total_prof * -1, co2_eq, Myield * -1
            return data
        except Exception as e:
            print(f"{repr(e)} <<<<<>>>>>-has occurred\n<<<<<>>>>>\n")
            pass
queue = Queue()        
def my_task(x):
      queue.put_nowait(x)
      m = queue.get_nowait()
      ap = Worker(m)
      return ap

def process_pointx(x):
    queue.put(Worker(x))
    return x
if __name__ =='__main__':
    swim= SWIM3
    print(swim)
    os.chdir(r'D:\wd\weatherdata')
    try:
        apsim = ApsimSoil(swim , lonlat = None, thickness_values = thickness, run_all_soils =False)
        print(apsim, "\n..")
        sw_apsim = ApsimSoil(apsimx_prototype , lonlat = None, thickness_values = thickness, run_all_soils =False)
        ap = apsim.run_edited_file()
        #print(ap)
    except Exception as e:
        pass
    for i in lonlat:
        apsim.replace_soils(i, apsim.extract_simulation_name)
        start, end = apsim.extract_start_end_years()
        wp = apsim.get_weather_online(i, start, end)
        apsim.replace_met_file(wp, apsim.extract_simulation_name)
        sw_apsim.replace_soils(i, apsim.extract_simulation_name)
        apsim.plot_objectives('Year', 'SOC1', report="Annual")
        ap = apsim.run_edited_file()
        ty =apsim.summarize_output_variable(var_name="Yield", table_name="MaizeR", )
        start, end  = sw_apsim.extract_start_end_years()
        wp = sw_apsim.get_weather_online(i, start, end)
        sw_apsim.run_edited_file()
        sw_apsim.replace_met_file(wp, sw_apsim.extract_simulation_name)
        swt = sw_apsim.summarize_output_variable(var_name="Yield", table_name="MaizeR", )
        print("results for swim")
        print(ty)
        print ('results for soil water model')
        print(swt)
        break