from subprocess import run
from os.path import join as opj
import os
import pandas as pd
import   sqlite3

import progressbar
import time
import logging
import subprocess


def create_connection(path):
    '''This function creates a conection to sql database file
    insert the the path to the database
    '''
    connection = None
    try:
        connection = sqlite3.connect(path)
    except Error as e:
        print(f"The error '{e}' occurred")

    return connection

# function to autodetect apsim installation path
from os.path import join as opj
def detectAPSIMX():
  try:
      directory = r'C:\Program Files'
      apasim_folder =[]
      fdir = []
      for rr, folder, files in os.walk(directory):
         for i in folder:
            if i.startswith("APSIM"):
              apasim_folder.append(opj(rr, i))
      if len(apasim_folder) > 1:
           print("multiple apsim next generation installed on your computer")
      elif len(apasim_folder) ==0:
           print("no apsim installation detected on your computer")
      else:
          for rr, sb, ff  in os.walk(apasim_folder[0]):
              for files in ff:
                 if files.endswith("Models.exe"):
                    fdir.append(opj(rr, files))
      extString = fdir[0].split('C:\\Program Files\\')[1]
  # APSIM next generation root directory regsitry
      apregistry = 'C:/PROGRA~1'
      path  = opj(apregistry, extString)
      pslit = path.split("\\")[1]
      pp= pslit
      if not os.path.isfile(path):
        print("APSIM not detected")
      #print('APSIM next generation version: ', pp, 'detected at: ', 'at', path)
      else:
        return(path)
  except Error as e:
        print(f"The error '{e}' occurred")  
"----------------------------------------------------------------------------"
# Function to read apsimx database
def read_simdb(path, file):
    '''
    Reads and a return multple dataframes after apsim simulation run in python window
    
    Paramters
    ----------
    path: This is the path string for the apsim simulation results database
    file: The name of the simulation database. note that it has the same name as the original apsimx file but with .db extention
    
    Returns
    ----------
    A dictionary of data frames
    '''
    widgets = ['Iterating through APSIM output database now: ', progressbar.BouncingBar(marker='', left='|', right='|', fill=' ', fill_left=True)]
    bar = progressbar.ProgressBar().start()
    if file.endswith('.db') ==False:
        print('*** Warning: \n The file name: {0}  is not a data base file did you forget to add .db extension?'.format(file))
    else:
           pth  = opj(path, file)
           if    os.path.isfile(pth) == False:
                print('*** Warning: {0} does not exist.'.format(pth))
           else:
                if os.path.isfile(pth) == True:
                # create connection using the wrote fucntion
                    conn = create_connection(pth)
                    cursor = conn.cursor()

                 # reading all table names
                    bar.update()
                    table_names = [a for a in cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]

                    table_list =[]
                    for i in table_names:
                         table_list.append(i[0])
              # start selecting tables
                    select_template = 'SELECT * FROM {table_list}'
    
             #create data fram dictionary to keep all the tables
                    dataframe_dict = {}
                    bar.update((1/3)*100)
                    for tname in table_list:
                           query = select_template.format(table_list = tname)
                           dataframe_dict[tname] = pd.read_sql(query, conn)
       # close the connection cursor
                    conn.close()
                    bar.finish()
                    dfl = len(dataframe_dict)
                    if len(dataframe_dict) == 0:
                        print("the data dictionary is empty. no data has been returned")
                    #else:
                        # remove elements 
                        #print(f"{dfl} data frames has been returned")
                    return dataframe_dict
  
# function to run apsimx file
apsimloc = detectAPSIMX()
def runAPSIM(path, filename, apsimxlocal =apsimloc, readdb = True, select_report=None, ):
    print(apsimloc)
    print("_______________________")
    '''
    Runs an apsimx simulation file
    
    Paramters
    ----------
    path: this is the path string for the apsim simulation results database
    
    filename: the name of the simulation database. note that it should have the .apsimx file extension 
    
    readdb: specifies whether pyhton should connect to apsimx sql data base and read the output
      the default is True. If false nothin will be returned
    
    apsimxlocal: this the string location of your computer use function detectAPSIMX() to generate this input.
      This is important to avoide delays on your computer searching for the full directory when running multiple simulations
    
    select_report: if they are more than one report in the simulation tree, it is advisable to select the desired report name.
    the default is none. This returns all the reports.
    Returns
    ----------
    If readdb == python will connect cursor to apsim simulation data base and return the data
    
    '''
    try:
        start = time.perf_counter()
        if filename ==  '':
           print("filename is empty. did you forget to write the apsim filename?")
        elif filename.endswith('.apsimx') ==False:
           print('*** Warning: \n The file name: {0}  is not an apsimx file did you forget to add .apsimx extension?'.format(filename))
        else:
           apsimfilepath  = opj(path, filename)
           if os.path.isfile(apsimfilepath) == False:
                 print('*** Warning: {0} does not exist.'.format(apsimfilepath))
           
           else: 
                #apsim_regsitry = detectAPSIMX(). canceld to avoid delys while running multiple files
          
                #if apsim_regsitry:
                print("running APIMx file now...")
               # join the two directory strings
                excutionString = f"{apsimxlocal} {apsimfilepath}"
                #print(excutionString)
                resultMessage = run(excutionString, check = True, shell= True)
                print(resultMessage)
                if readdb:
                   newfilenamedb = filename.split("apsimx")[0] + "db"
                   print('Reading database file.................')
                   data = read_simdb(path, newfilenamedb)
                   # remove  other data frames
                   remove_list = ['_Units', '_Messages','_Simulations','_InitialConditions', '_Checkpoints']
                   [data.pop(key) for key in remove_list]
                   if select_report:
                     data = data[select_report]
                   else:
                     data = data
                   print("****Done**************************")
                   return data
                else:
                     print("no data has been returned")
                     print("****Done**************************")
                    
    except subprocess.CalledProcessError as e:
        print(f"The error '{e.output}' occurred")
    finally:
       end = time.perf_counter()
       print(f'Execution took: {end-start} seconds')
"--------------------------------------------------------------------------------------"

def read_simdb2(completepath):
    '''
    Reads and a return multple dataframes after apsim simulation run in python window
    
    Paramters
    ----------
    path: This is the path string for the apsim simulation results database
    file: The name of the simulation database. note that it has the same name as the original apsimx file but with .db extention
    
    Returns
    ----------
    A dictionary of data frames
    '''
    if completepath.endswith('.db') ==False:
        print('*** Warning: \n The file name: {0}  is not a data base file did you forget to add .db extension?'.format(file))
    else:
           pth  = completepath
           if    os.path.isfile(pth) == False:
                print('*** Warning: {0} does not exist.'.format(pth))
           else:
                if os.path.isfile(pth) == True:
                # create connection using the wrote fucntion
                    conn = create_connection(pth)
                    cursor = conn.cursor()

                 # reading all table names
                  
                    table_names = [a for a in cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]

                    table_list = []
                    for i in table_names:
                         table_list.append(i[0])
                         # remove these
                    rm = ['_InitialConditions', '_Messages', '_Checkpoints', '_Units']
                    for i in rm:
                        if i in table_list:
                            table_list.remove(i)
              # start selecting tables
                    select_template = 'SELECT * FROM {table_list}'
    
             #create data fram dictionary to keep all the tables
                    dataframe_dict = {}
                 
                    for tname in table_list:
                           query = select_template.format(table_list = tname)
                           dataframe_dict[tname] = pd.read_sql(query, conn)
       # close the connection cursor
                    conn.close()
                  
                    dfl = len(dataframe_dict)
                    if len(dataframe_dict) == 0:
                        print("the data dictionary is empty. no data has been returned")
                    #else:
                        # remove elements 
                        #print(f"{dfl} data frames has been returned")
                    return dataframe_dict
       
def runAPSIM2(completepath,  apsimxlocal =apsimloc, readdb = True, select_report=None, ):
    '''
    Runs an apsimx simulation file
    
    Paramters
    ----------
    
    completepath: this is the path string for the apsim simulation results database
    
    filename: completefile path to apsimx file note that it should have the .apsimx file extension 
    
    readdb: specifies whether pyhton should connect to apsimx sql data base and read the output
      the default is True. If false nothin will be returned
    
    apsimxlocal: this the string location of your computer use function detectAPSIMX() to generate this input.
      This is important to avoide delays on your computer searching for the full directory when running multiple simulations
    
    select_report: if they are more than one report in the simulation tree, it is advisable to select the desired report name.
    the default is none. This returns all the reports.
    Returns
    ----------
    
    If readdb == python will connect cursor to apsim simulation data base and return the data
    
    '''
    try:
        start = time.perf_counter()
        apsimfilepath  = completepath
               # join the two directory strings
        excutionString = f"{apsimxlocal} {apsimfilepath}"
        print(excutionString)
        resultMessage = run(excutionString, check = True, shell= True)
        newfilenamedb = completepath.replace(".apsimx", ".db")
        # print(newfilenamedb)
        if readdb:
         data = read_simdb2(newfilenamedb)
           # remove  other data frames
         #remove_list = ['_Units', '_Messages','_Simulations','_InitialConditions', '_Checkpoints']
         #[data.pop(key) for key in remove_list]
         return data
    except subprocess.CalledProcessError as e:
        print(f"The error '{e}' occurred")
        raise
    finally:
       end = time.perf_counter()
       print(f'Execution took: {end-start} seconds')
"--------------------------------------------------------------------------------------"

