# ______________________________________________________________________________

import random
from collections import namedtuple
from pymoo.decomposition.asf import ASF
from itertools import combinations
import apsimx.apsimx2py
from Cypython import utils
from typing import Union
from apsimx.utils import load_from_numpy
import os, glob, time, random, sys, shutil, queue
from pprint import pprint
import apsimx.utils
import threading
from apsimx.utils import load_from_numpy
from apsimx.utils import organize_crop_rotations
from apsimx.utils import make_apsimx_clones
from apsimx.utils import get_data_element
from apsimx.utils import delete_simulation_files
from apsimx.utils import Cache, add_wheat, upload_weather, upload_apsimx_file, upload_apsimx_file_by_pattern
from apsimx import weather
from apsimx.apsimx2py import APSIMNG, detect_apsim_installation
from apsimx.apsimx2py import ApsimSoil
from os.path import join, dirname
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import queue
from apsimx.pollipy import PollinationBase
import matplotlib.pyplot as plt
from os.path import join as opj
import pandas as pd
import numpy as np

from apsimx import soilmanager
from apsimx.remote import apsimx_prototype, test, EXPERIMENT, EXPERIMENT_NT

import datetime
from apsimx import weather
from concurrent.futures import ThreadPoolExecutor, as_completed
import concurrent
import pythonnet
from apsimx.run_utils import load_apsimx_from_string
from apsimx.utils import collect_runfiles
try:
    if pythonnet.get_runtime_info() is None:
        pythonnet.load("coreclr")
except:
    print("dotnet not found ,trying alternate runtime")
    pythonnet.load()

import clr
sys.path.append(os.path.dirname(detect_apsim_installation()))

# Try to load from pythonpath and only then look for Model.exe
try:
    clr.AddReference("Models")
except:
    print("Looking for APSIM")
    apsim_path = shutil.which("Models")
    if apsim_path is not None:
        apsim_path = os.path.split(os.path.realpath(apsim_path))[0]
        sys.path.append(apsim_path)
    clr.AddReference("Models")
import Models
from Models.Core import Simulations
numpy_file = r'D:\wd\GIS\FB070801050305_resoln_500.csv'  # created by pollmapping module using geopandas
# ================================================================================================================
wd = r'D:\wd'
os.chdir(wd)
print(os.getcwd())
ptt = r'D:\ENw_data\creek.shp'
pm = PollinationBase(ptt, resoln=500, field="GenLU")
pol_object = pm.get_fishnets()
print("done")


# Get the current time
def completed_time():
    current_time = datetime.datetime.now()

    # Extract hours, minutes, and seconds
    hours = current_time.hour
    minutes = current_time.minute
    seconds = current_time.second
    # Print the time in HH:MM:SS format
    print(f"Cycle completed at: {hours:02}:{minutes:02}:{seconds:02}")


# delete_simulation_files(opj(os.getcwd(),'weatherdata'))
class PreProcessor():

    def __init__(self, path2apsimx, pol_object=pol_object, resoln=500, field="GenLU",
                  wp='D:\wd\weather_files0305\weatherdata', layer_file = None, thickness_values =None):
        assert os.path.isfile(path2apsimx), "please make sure the file is loaded properly"
        assert path2apsimx.endswith(
            ".apsimx"), "file path is missing apsimx extention. did you forget to include .apsimx extension"
        self.named_tuple = load_apsimx_from_string(path2apsimx)
        if  not thickness_values:
          self.thickness_values = [150, 150, 200, 200, 200, 250, 300, 300, 400, 500]
        self.weather_path = wp
        self.rotations = organize_crop_rotations(pol_object.record_array['CropRotatn'])
        if layer_file:
          self.layer = 'D:\\ENw_data\\creek.shp'
        self.apsimx_folder_path = r'D:\wd\APSIM_Files'

    def sample_indices(self, percentage, *args, **kwargs):
        total_indices = len(pol_object.record_array['Shape'])
        num_indices_to_select = int(total_indices * (percentage / 100))
        sampled_indices = np.random.choice(total_indices, size=num_indices_to_select, replace=False)
        return sampled_indices

    def sample_OBJECTID(self, percentage, *args, **kwargs):
        total_indices = len(pol_object.record_array['Shape'])
        num_indices_to_select = int(total_indices * (percentage / 100))
        sampled_indices = random.choices(list(self.rotations.keys()), k=num_indices_to_select)
        return sampled_indices

    def add_cover_crop(self, percent):
        ditx = self.rotations.copy()
        prop = self.sample_OBJECTID(percent)
        for i in prop:
            crops = ditx[i]
            if isinstance(crops, str):
                cover = add_wheat(crops)
                cover = ', '.join(cover)
                ditx[i] = cover
        self.rotations = ditx
        return self

    def populate_cover_crop(self, percent):
        ditx = self.rotations.copy()
        prop = self.sample_OBJECTID(percent)
        for i in prop:
            crops = ditx[i]
            if isinstance(crops, str):
                cover = add_wheat(crops)
                cover = ', '.join(cover)
                ditx[i] = cover
        self.rotations = ditx
        return self

    def check_for_missing_metfile(self, path):
        for i in list(self.rotations):
            upload_weather(path, i)

    def load_apsimx_object(self):
        try:
            self.apsim_object = ApsimSoil(self.named_tuple.path)
        except Exception as e:
            print(
                f"{e} has occured reading apsimx from the cloned apsimx file and using from from file method\n--------------\nignore eror and proceed")
            return self

    def replace_apsim_file_with_mets(self, path2weather_files, filename = None):
        print(self.weather_path)
        aps = os.path.join(os.getcwd(), 'Weather_APSIM_Files')
        if not os.path.exists(aps):
            os.mkdir(aps)
        print("cloning apsimx file")
        [shutil.copy (self.named_tuple.path, os.path.join(aps, f"spatial_{i}_need_met.apsimx")) for i in list(self.rotations)]
        for i in list(self.rotations):
            if not filename:
              fn = "spatial_ap_" + str(i) + '.apsimx'
            else:
                fn  =filename + '.apsimx'
            fname = os.path.join(aps, fn)
            wp = upload_weather(path2weather_files, i)
            ff = collect_runfiles(aps, pattern=f"*_{i}_need_met.apsimx")[0]
            apsim_object = ApsimSoil(model=ff, copy=False, lonlat=None, thickness_values=self.thickness_values,\
                                     out_path=None)
            apsim_object.replace_met_file(wp, apsim_object.extract_simulation_name)
            apsim_object.out_path = fname
            apsim_object.save_edited_file()
            print(f"met replacement for {ff} is complete apsimx files are found in: {aps}", end = "\r")
        return aps
        print("weather replacement succeeded")
    def dict_generator(self, my_dict):
        for key, value in my_dict.items():
            yield key, value

    def idex_excutor(self, x, lock):  # We supply x from the rotations idex which inherits objectid
        try:
            a = time.perf_counter()
            print(f"downloading for: {x}", end = '\r')
            data_dic = {}
            fn = "daymet_wf_" + str(x) + '.met'
            cod = pol_object.record_array["Shape"][x]

            filex = weather.daymet_bylocation_nocsv(cod, start=1998, end=2020, cleanup=False, filename=fn)
            return filex
        except Exception as e:
            # raise
            print(e, "has occured")
            try:
                print("trying again")
                filex = weather.daymet_bylocation_nocsv(cod, start=1998, end=2000, cleanup=True, filename=fn)
                return filex
            except:
              print("unresolved errors at the momentt try again")
    def weather_excutor(self, queue, lock):
        '''Process files from the queue.'''
        for args in iter(queue.get, None):
            try:
                self.idex_excutor(args, lock)
            except Exception as e:
                print ('{0} failed: {1}'.format(args, e))

    def threaded_weather_download(self, wd = None, iterable  = None):
        if wd:
            os.chdir(wd)
        threads = []
        listable  = None
        if iterable:
            listable = iterable
        else:
            listable =  list(self.rotations.keys())
        q = queue.Queue()
        for idices in listable:
            q.put_nowait(idices)

            # run .apsim files and start threads to convert
        self._lock = threading.RLock()
        lock = threading.RLock()
        threads = [threading.Thread(target=self.weather_excutor, args=(q, self._lock)) for _ in range(12)]
        for t in threads:
            t.daemon = False  # program quits when threads die
            t.start()
        for _ in threads: q.put_nowait(None)  # signal no more files
        for t in threads: t.join()  # wait for com
        return os.getcwd()

    def weather_process_point(self, queue, result_queue):
        while True:
            try:
                index_id = queue.get(block=False)
                simulated_results = self.idex_excutor(index_id)
                result_queue.put(simulated_results)
                queue.task_done()
            except queue.Empty:
                break

    def download_weather_in_parallel(self, num_threads=16, rerun=False, rerun_list=None):
        results = []
        if not rerun:
            iter_ids = list(self.rotations.keys())
        else:
            iter_ids = rerun_list
        # iter_ids = random.sample(iter_ids, 1)
        queue_points = queue.Queue()
        result_queue = queue.Queue()
        for index_id in iter_ids:
            queue_points.put(index_id)
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            # _______________________________________________________
            # we go for Threadpool excutor other than process
            for _ in range(num_threads):
                executor.submit(self.weather_process_point, queue_points, result_queue)
        queue_points.join()
        while not result_queue.empty():
            simulated_results = result_queue.get()
            results.append(simulated_results)
        return results

    def download_weather_first(self, number_threads=16, start=1990, end=2020, watershed="trial"):
        """

        :param number_threads: numbe rof thread according to cpu specifications
        :param start: start year beginning the weather download
        :param end: end year for weahter download
        :return: a gennerator of value pairs for the weather path. keys are the objectId's
        """
        wd = 'weather_files' + watershed
        curdir = os.getcwd()
        wf = os.path.join(os.getcwd(), wd)
        if not os.path.exists(wf):
            os.mkdir(wf)
        indices = list(self.rotations.keys())
        print(f"length of idices  is :{len(indices)}")
        os.chdir(wf)
        with concurrent.futures.ThreadPoolExecutor(max_workers=number_threads) as executor:
            # Submit download tasks to the executor
            future_to_url = {executor.submit(self.idex_excutor, url): url for url in indices}
            # Wait for all tasks to complete
            concurrent.futures.wait(future_to_url)
        os.chdir(curdir)
        return self

    def has_numbers(self, input_string):
        for char in input_string:
            if char.isdigit():
                return True
        return False

    def all_digits(self, input_string):
        return all(char.isdigit() for char in input_string)

    def split_file_names(self, fn):
        sp = fn.split("_")[-1]
        sp2 = sp.split(".")[0]
        if self.all_digits(sp2):
            sp3 = int(sp2)
            return sp3

    def return_missing_weather_index(self, path):  # this one evaluates any missing download due to first computation of the paralled procsin
        import concurrent
        path = path  # r'D:\wd\weather_files0305\weatherdata'
        curdir = os.getcwd()
        print(len(os.listdir(path)))
        simulated = [self.split_file_names(i) for i in os.listdir(path)]
        os.chdir(curdir)
        not_simualted = [nt for nt in list(self.rotations) if nt not in simulated]
        return not_simualted
        # with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        #     # Submit download tasks to the executor
        #     future_to_url = {executor.submit(self.idex_excutor, url): url for url in not_simualted}
        #     # Wait for all tasks to complete
        #     concurrent.futures.wait(future_to_url)
        # #self.download_weather_first(self, number_threads=4, start=1990, end=2020, watershed="0305")
        # #self.download_weather_in_parallel(num_threads=4, rerun = True, rerun_list = not_simualted)

    def check_met(self, path):
        pp = path
        try:
            dmett = pd.read_csv(pp, delimiter=' ', skiprows=5)
            df = dmett.drop(0)
            year = np.array(df['year'], dtype=np.float64)
            mn = year.min()
            mx = (year.max())
            if mx < 2020.0:
                os.remove(pp)
                print("remooving: ", pp)
                return True
        except:
            pass

    def soil_downloader(self, x):
        # print(f"downloading for: {x}")
        data_dic = {}
        cod = list(get_data_element(pol_object.record_array, "Shape", x))
        try:
            data_table = soilmanager.DownloadsurgoSoiltables(cod, select_componentname='domtcp')
            self.soil_profile = soilmanager.OrganizeAPSIMsoil_profile(data_table,
                                                                      thickness_values=self.thickness_values,
                                                                      thickness=20)
            data_dic[
                x] = self.soil_profile.cal_missingFromSurgo()  # returns a list of physical, organic and cropdf each in a data frame

            return data_dic
        except Exception as e:
            print(repr(e))
    @staticmethod
    def download_soil_table_first(iterator = None, cordnates = None, number_threads=16):
        """

        :param iterator: array or list
        :param number_threads:
        :cordnates CORDNATE FOR DOWNLOADING THE SOILS IF NOT SPECIFYIED THE DEFAULT FROM THE LAYER WILL BE USED
        :return: dictionary of SSURGO SOIL TABLES
        """
        print("Downloading SSURGO soil tables")
        a = time.perf_counter()
        if iterator:
            indices = iterator
        else:
            print("iterable missing")

        def soil_excutor(x):
            data_dic = {}
            if  cordnates:
                cod =  cordnates[x]
            else:
                cod = list(get_data_element(pol_object.record_array, "Shape", x))
            data_table = soilmanager.DownloadsurgoSoiltables(cod, select_componentname='domtcp')
            self.soil_profile = soilmanager.OrganizeAPSIMsoil_profile(data_table,
                                                         thickness_values=self.thickness_values,
                                                                      thickness=20)
            data_dic[
                x] = self.soil_profile.cal_missingFromSurgo()  # returns a list of physical, organic and cropdf each in a data frame

            return data_dic
            # physical_calculated = missing_properties[0]
            # self.organic_calcualted = missing_properties[1]
            # self.cropdf = missing_properties[2]

        datap = []
        with ThreadPoolExecutor(max_workers=number_threads) as executor:
            # List to store futures
            futures = []

            # Submit tasks using executor.submit
            for index in indices:
                future = executor.submit(soil_excutor, index)
                futures.append(future)
            # Collect results as they complete
            results = []
            for future in futures:
                result = future.result()  # This blocks until the result is available
                results.append(result)
        merged_dict = {k: v for d in results for k, v in d.items()}
        self.merged_soil_list = merged_dict
        b = time.perf_counter()
        print(f"downloading SSURGO soil tables took {b - a} seconds")
        return self
    class PreSoilReplacement(ApsimSoil):
        def __init__(self, model, thickness_values=None):
            super().__init__(model)
            if not thickness_values:
                self.thickness_values = [150, 150, 200, 200, 200, 250, 300, 300, 400, 500]
    def replace_downloaded(self,x, file_path):
            ap = PreProcessor.PreSoilReplacement(file_path)
            data_dict = self.soil_downloader(x)
            ap.replace_downloaded_soils(data_dict[x], ap.extract_simulation_name)
            ap.save_edited_file()

            print(f"{x} succeeded", end = '\r')
            return self
    def threaded_soil_replacement(self, wd, iterable =None):
        #pattern = f'spatial_ap_{specific_number}.apsimx'
        assert os.path.exists(wd), "path does not exists"
        listable = None
        if iterable:
            listable = iterable
        else:
            listable = list(self.rotations.keys())
        os.chdir(wd)
        threads = []
        for idices in listable:
            file  = collect_runfiles(wd, pattern =  f"*_ap_{idices}.apsimx")[0]
            thread = threading.Thread(target=self.replace_downloaded, args=(idices, file))
            threads.append(thread)
            thread.daemon = False
            thread.start()
        # Wait for all threads to finish
        print("waiting for all workers to complete their jobs")
        for thread in threads:
            thread.join()
        print("Threaded soil  download and replacement completed successfully-s-s-s--s-")
        return wd

    def replace_management_threaded(self):
        threads = []
        for idices in list(self.rotations.keys()):
            thread = threading.Thread(target=self.insert_historical_rotations, args=(idices,))
            threads.append(thread)
            thread.start()
        thread.join()

    def prepare_simulation(self, wd, watershed_name=None, skip_initial=False):
        """

        #:param watershed_name: name of the watershed or simulation area canceled passs a complete wd of the watershed or areaname
        :param skip_initial: false if cecking whether everything is complete
        :return: path to the pre-simulated apsimx files populated with weather data
        """
        if os.getcwd() != wd:
            os.chdir(wd)
        print("downloading weather file")
        wpath = self.threaded_weather_download(wd = wd)
        absolute_path = os.path.join(wpath, 'weatherdata')
        print("First weather dwonlaod completed checking if rerun is needed")
        not_simulated = self.return_missing_weather_index( absolute_path)
        if len(not_simulated) == 0:
            print("weather download complete")
        else:
            print(f'rerunnung missing indices: {not_simulated}')
            not_simulated = self.threaded_weather_download(wpath, iterable = not_simulated)
        if len(not_simulated) == 0:
            print("Done****8")
        else:
            print(f"print some downloads idices: {not_simulated} __________failed")
        # enxt we create the apsimx file
        print('downloading weather done')
        print("creating apsimx files")
        self.weather_path = wd
        pathfs = self.replace_apsim_file_with_mets(absolute_path)
        print("replacing weather complete proceed to simulation")
        print("now replacing soils")

        self.apsim_directory = self.threaded_soil_replacement(pathfs)
        return self.apsim_directory
paths = (r'D:\wd\nf\EXPERIMENT\T\CC', r'D:\wd\nf\EXPERIMENT\T\CW')
if __name__ == "__main__":
        # test the functions
        ap = PreProcessor(EXPERIMENT_NT)
        path = r'D:\wd\New folder\Weather_APSIM_Files' # maize wheat
        path = r'D:\wd\nf\EXPERIMENT\NT\CW' # continous corn
        #ap.threaded_soil_replacement(path)
        th = ap.prepare_simulation(paths[1])
        print(th)




