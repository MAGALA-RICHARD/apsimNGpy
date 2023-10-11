# ______________________________________________________________________________

import random
from collections import namedtuple
from pathlib import Path
from pymoo.decomposition.asf import ASF
from itertools import combinations
import apsimx.apsimx2py
from Cypython import utils
from typing import Union
from apsimx.utils import load_from_numpy
import os, glob, time, random, sys, shutil, queue
root = Path(os.path.dirname(os.path.realpath(__file__)))
path = Path(os.path.join(root, 'manager'))
path_utilities = os.path.join(root, 'utililies')
main_root = os.path.realpath(os.path.dirname(root))
sys.path.extend([path, path_utilities, root, main_root])
from utililies.utils import  organize_crop_rotations, upload_weather, upload_apsimx_file, upload_apsimx_file_by_pattern
from utililies.utils import load_from_numpy, collect_runfiles, get_data_element, add_wheat, delete_simulation_files, make_apsimx_clones
import apsimpy
from cropmanager import InsertCroppingSystems
import utils
import threading
from apsimx import weather
from apsimpy import APSIMNG, detect_apsim_installation, ApsimSoil
from os.path import join, dirname
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import queue
import matplotlib.pyplot as plt
from os.path import join as opj
import pandas as pd
import numpy as np
import soilmanager
import datetime
from tqdm import tqdm
import weather
import pythonnet
from run_utils import load_apsimx_from_string
COUNTER = 1
# Get the current time
def completed_time():
    current_time = datetime.datetime.now()
    # Extract hours, minutes, and seconds
    hours = current_time.hour
    minutes = current_time.minute
    seconds = current_time.second
    # Print the time in HH:MM:SS format
    print(f"Cycle completed at: {hours:02}:{minutes:02}:{seconds:02}")

class Data:
    def __init__(self, lonlats, site_id, tag, cropping  =None, **kwargs):
        """
        
        :param lonlats: location of the simulation sites
        :param site_id: could be names of the sites
        :param tag: can be like maize to represent a cropping system
        :param kwargs: 
        """
        self.locations = lonlats
        self.site_ids = site_id
        self.tag = tag
        self.crops = cropping

# delete_simulation_files(opj(os.getcwd(),'weatherdata'))
class PreProcessor():

    def __init__(self, path2apsimx, data=None, number_threads =10,
                  wp=None, layer_file = None, thickness_values =None, use_threads = True):
        """

        :param path2apsimx: path to apsimx file
        :param data arrays or lists
        :param resoln: cell resolution
        :param field: field name containing the land use classess
        :param wp: path to keep the wather files
        :param layer_file: watershed layer
        :param thickness_values: soil thickness values
        """
        assert os.path.isfile(path2apsimx), "please make sure the file is loaded properly"
        assert path2apsimx.endswith(
            ".apsimx"), "file path is missing apsimx extention. did you forget to include .apsimx extension"
        self.named_tuple = load_apsimx_from_string(path2apsimx)
        if  not thickness_values:
          self.thickness_values = [150, 150, 200, 200, 200, 250, 300, 300, 400, 500]
        self.weather_path = wp
        assert isinstance(data, Data), "Please initiate Data class and supply the lonlats and the site_id"
        self.data = data
        self.number_threads = number_threads
        self.total = len(self.data.locations)
        self.use_threads = use_threads
        if not layer_file:
          self.layer = 'D:\\ENw_data\\creek.shp'

    def _callback(self, _lock):
        global COUNTER
        COUNTER +=1
        percent = COUNTER / self.total *100
        with _lock:
            print(f'{percent} completed ')
    def sample_indices(self, percentage, *args, **kwargs):
        total_indices = len(self.data.locations)
        num_indices_to_select = int(total_indices * (percentage / 100))
        sampled_indices = np.random.choice(total_indices, size=num_indices_to_select, replace=False)
        return sampled_indices


    def check_for_missing_metfile(self, path):
        for i in range(self.total):
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
        self._counter  =0
        aps = os.path.join(os.getcwd(), 'Weather_APSIM_Files')
        if not os.path.exists(aps):
            os.mkdir(aps)
        print("cloning apsimx file")


        [shutil.copy (self.named_tuple.path, os.path.join(aps, f"{self.data.tag[i]}_{site}_{i}_need_met.apsimx")) for i in range(self.total) for site in self.data.site_ids]
        for i, site in zip(range(self.total), self.data.site_ids):
            self._counter +=1
            if not filename:
              fn = "spatial_ap_" + str(i) + '.apsimx'
            else:
                fn  =filename + '.apsimx'
            fname = os.path.join(aps, fn)
            wp = upload_weather(path2weather_files, i)
            ff = collect_runfiles(aps, pattern=f"{self.data.tag[i]}_{site}_{i}_need_met.apsimx")[0]
            apsim_object = ApsimSoil(model=ff, copy=False, lonlat=None, thickness_values=self.thickness_values,\
                                     out_path=None)
            apsim_object.replace_met_file(wp, apsim_object.extract_simulation_name)
            rotation  = {"Name": "Simple Rotation", "Crops": self.data.crops[i]}
            if self.data.crops is not None:
                apsim_object.out_path = ff
                apsim_object.update_management_decissions(rotation, simulations=apsim_object.extract_simulation_name, reload=True)
                apsim_object.out_path = ff
            apsim_object.save_edited_file()
            ct =self._counter/self.total * 100
            print(f"{self._counter}/{self.total}  ({ct:3.0f} %) completed ", end = "\r")
        print(aps)
        return aps
    def dict_generator(self, my_dict):
        for key, value in my_dict.items():
            yield key, value

    def idex_excutor(self, x, lock):  # We supply x from the rotations idex which inherits objectid
        try:
            a = time.perf_counter()
            print(f"downloading for: {x}", end = '\r')
            data_dic = {}
            fn = "daymet_wf_" + str(x) + '.met'
            cod = self.data.locations[x]
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
                #self.results = None # we will collect these later
            except Exception as e: # catch exceptions to avoid exiting the thread prematurely
                print ('{0} failed: {1}'.format(args, e))#, file=sys.stderr
                #os.startfile(self.show_file_in_APSIM_GUI())

    def threaded_weather_download(self, wd = None, iterable  = None):
        if wd:
            os.chdir(wd)
        threads = []
        listable  = None
        if iterable:
            listable = iterable
        else:
            listable =  range(self.total)
        q = queue.Queue()
        for idices in listable:
            q.put_nowait(idices)
        self._lock = threading.RLock()
        lock = threading.RLock()
        threads = [threading.Thread(target=self.weather_excutor, args=(q, self._lock)) for _ in range(self.number_threads)]
        for t in threads:
            t.daemon = False  # program quits when threads die
            t.start()
        for _ in threads: q.put_nowait(None)  # signal no more files
        for t in threads: t.join()  # wait for com
        if wd:
            return wd
        else:
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

    def download_weather_in_parallel(self, rerun=False, rerun_list=None):
        num_threads = self.number_threads
        results = []
        if not rerun:
            iter_ids = range(self.total)
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

    def download_weather_first(self, start=1990, end=2020, watershed="trial"):
        """

        :param number_threads: numbe rof thread according to cpu specifications
        :param start: start year beginning the weather download
        :param end: end year for weahter download
        :return: a gennerator of value pairs for the weather path. keys are the objectId's
        """
        number_threads = self.number_threads
        wd = 'weather_files' + watershed
        curdir = os.getcwd()
        wf = os.path.join(os.getcwd(), wd)
        if not os.path.exists(wf):
            os.mkdir(wf)
        indices = range(self.total)
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
        path = path  # r'D:\wd\weather_files0305\weatherdata'
        curdir = os.getcwd()
        simulated = [self.split_file_names(i) for i in os.listdir(path)]
        os.chdir(curdir)
        not_simualted = [nt for nt in range(self.total) if nt not in simulated]
        return not_simualted

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
                print("removing: ", pp)
                return True
        except:
            pass

    def soil_downloader(self, x):
        # print(f"downloading for: {x}")
        data_dic = {}
        cod = self.data.locations[x]
        try:
            data_table = soilmanager.DownloadsurgoSoiltables(cod, select_componentname='domtcp')
            self.soil_profile = soilmanager.OrganizeAPSIMsoil_profile(data_table,
                                                                      thickness_values=self.thickness_values,
                                                                      thickness=20)
            data_dic[x] = self.soil_profile.cal_missingFromSurgo()  # returns a list of physical, organic and cropdf each in a data frame
            return data_dic
        except Exception as e:
            print(repr(e))

    def download_soil_table_first(self, iterator = None, cordnates = None):
        """

        :param iterator: array or list
        :cordnates CORDNATE FOR DOWNLOADING THE SOILS IF NOT SPECIFYIED THE DEFAULT FROM THE LAYER WILL BE USED
        :return: dictionary of SSURGO SOIL TABLES
        """
        print("Downloading SSURGO soil tables")
        number_threads = self.number_threads
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
                cod = self.data.locations[x]
            data_table = soilmanager.DownloadsurgoSoiltables(cod, select_componentname='domtcp')
            self.soil_profile = soilmanager.OrganizeAPSIMsoil_profile(data_table,
                                                         thickness_values=self.thickness_values,
                                                                      thickness=20)
            data_dic[
                x] = self.soil_profile.cal_missingFromSurgo()  # returns a list of physical, organic and cropdf each in a data frame

            return data_dic
        with ThreadPoolExecutor(max_workers=number_threads) as executor:
            futures = []
            for index in indices:
                future = executor.submit(soil_excutor, index)
                futures.append(future)
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
    def replace_downloaded(self,x, site, wd):
        try:
            file_path= collect_runfiles(wd, pattern=[f"{self.data.tag[x]}_{site}_{x}_need_met.apsimx"])[0]
            ap = PreProcessor.PreSoilReplacement(file_path)
            data_dict = self.soil_downloader(x)
            ap.replace_downloaded_soils(data_dict[x], ap.extract_simulation_name)
            ap.save_edited_file()
            return self
        except Exception as e:
            print(f"{x} ====may have issues \n")
            print(file_path)
            print(repr(e))
    def threaded_soil_replacement(self, wd, iterable =None):
        #pattern = f'spatial_ap_{specific_number}.apsimx'
        assert os.path.exists(wd), "path does not exists"
        listable = None
        if iterable:
            listable = iterable
        else:
            listable = range(self.total)
            print(listable)
        if not self.use_threads:
            a = time.perf_counter()
            with ProcessPoolExecutor(self.number_threads) as pool:
                futures = [pool.submit(self.replace_downloaded, i, site, wd) for i in listable for site in self.data.site_ids]
                progress = tqdm(total=len(futures), position=0, leave=True, bar_format='{percentage:3.0f}% completed')
                # Iterate over the futures as they complete
                for future in as_completed(futures):
                    future.result()  # retrieve the result (or use it if needed)
                    progress.update(1)
                progress.close()
            print(time.perf_counter() - a, 'seconds', f'to replace soils ')
        else:
            a = time.perf_counter()
            with ThreadPoolExecutor(self.number_threads) as tpool:
                futures = [tpool.submit(self.replace_downloaded, i, site, wd) for i in listable for site in self.data.site_ids]
                progress = tqdm(total=len(futures), position=0, leave=True, bar_format='{percentage:3.0f}% completed')
                # Iterate over the futures as they complete
                for future in as_completed(futures):
                    future.result()  # retrieve the result (or use it if needed)
                    progress.update(1)
                progress.close()
            print(time.perf_counter() - a, 'seconds', f'to replace soils')
        print("soil  download and replacement completed successfully-s-s-s--s-")
        return wd

    def replace_management_threaded(self):
        threads = []
        for idices in range(self.total):
            thread = threading.Thread(target=self.insert_historical_rotations, args=(idices,))
            threads.append(thread)
            thread.start()
        thread.join()

    def prepare_simulation(self, wd):
        """

        wd: desired working directory path
        :return: path to the pre-simulated apsimx files populated with weather data
        """
        os.chdir(wd)
        print("downloading weather data")
        wpath = self.threaded_weather_download(wd = wd)
        print(wpath)
        absolute_path = os.path.join(wpath, 'weatherdata')
        print("First weather downlaod completed checking if rerun is needed")
        not_simulated = self.return_missing_weather_index( absolute_path)
        if len(not_simulated) == 0:
            print("weather download complete")
        else:
            print(f'rerunnung missing indices: {not_simulated}')
            not_simulated = self.threaded_weather_download(wpath, iterable = not_simulated)
        if len(not_simulated) == 0:
            print("===========================================================")
        else:
            print(f"print some downloads with idices: {not_simulated} __________failed")
        print('downloading weather done')
        print("creating apsimx files")
        self.weather_path = wd
        pathfs = self.replace_apsim_file_with_mets(absolute_path)
        print("replacing weather complete proceed to simulation")
        print("now replacing soils")
        self.apsim_directory = self.threaded_soil_replacement(pathfs)
        return self.apsim_directory



