"""
This code is used to calibrate the model

-   you have to make the root directory to the examples folder to enable the code
    from reading input files

"""
#%links
from IPython import get_ipython   # to reset the variable explorer each time
get_ipython().magic('reset -f')
#import os
#os.chdir("C:/Users/Mostafa/Desktop/My Files/thesis/My Thesis/Data_and_Models/Model/Code/colombia")
#import sys
#sys.path.append("C:/Users/Mostafa/Desktop/My Files/thesis/My Thesis/Data_and_Models/Interface/Distributed_Hydrological_model/HBV_distributed/function")
#path="C:/Users/Mostafa/Desktop/My Files/thesis/My Thesis/Data_and_Models/Data/05new_model/00inputs/"
#path="C:/Users/Mostafa/Desktop/My Files/thesis/My Thesis/Data_and_Models/Data/colombia/00inputs/" #GIS/4000/

#%library
import numpy as np
import pandas as pd
from datetime import datetime
import gdal
import time
#from pyOpt import Optimization, ALHSO,Optimizer

# functions
from Hapi.calibration import RunCalibration
import Hapi.hbv as HBV
#import Wrapper
#import Hapi.GISpy as GIS
import Hapi.giscatchment as GC
import Hapi.distparameters as DP
import Hapi.performancecriteria as PC
#import Inputs
#%%

### Meteorological & GIS Data
# resolution of input data is 4km*4km
PrecPath = prec_path="data/meteodata/4000/calib/prec"
Evap_Path = evap_path="data/meteodata/4000/calib/evap"
TempPath = temp_path="data/meteodata/4000/calib/temp"
#DemPath = path+"GIS/4000/dem4000.tif"
FlowAccPath = "data/GIS/4000/acc4000.tif"
FlowDPath = "data/GIS/4000/fd4000.tif"
Paths=[PrecPath, Evap_Path, TempPath, FlowAccPath, FlowDPath, ]

#ParPathCalib = path+"meteodata/4000/"+"parameters.txt"
#ParPathRun = path+"meteodata/4000/parameters"

###  Boundaries, p2
p2=[24, 1530]
#[sp,sm,uz,lz,wc]
init_st=[0,5,5,5,0]
snow=0
UB=np.loadtxt("data/UB.txt", usecols=0)
LB=np.loadtxt("data/LB.txt", usecols=0)

Basic_inputs=dict(p2=p2, init_st=init_st, UB=UB, LB=LB, snow=snow)


### spatial variability function
"""
define how generated parameters are going to be distributed spatially
totaly distributed or totally distributed with some parameters are lumped
for the whole catchment or HRUs or HRUs with some lumped parameters
for muskingum parameters k & x include the upper and lower bound in both
UB & LB with the order of Klb then kub
function inside the calibration algorithm is written as following
par_dist=SpatialVarFun(par,*SpatialVarArgs,kub=kub,klb=klb)

"""
SpatialVarFun=DP.par3dLumped
raster=gdal.Open(FlowAccPath)
no_parameters=12
SpatialVarArgs=[raster,no_parameters]

### Objective function
# stations discharge
Sdate='2009-01-01'
Edate='2011-12-31'
Qobs = pd.read_csv("data/Discharge/Headflow.txt",header=0 ,delimiter="\t", skiprows=11,
                   engine='python',index_col=0)
ind=[datetime(int(i.split("/")[0]),int(i.split("/")[1]),int(i.split("/")[2]))  for i in Qobs.index.tolist()]
Qobs.index=ind
Qobs =Qobs.loc[Sdate:Edate]

# outlet discharge
Qobs[6] =np.loadtxt("data/Discharge/Qout_c.txt")
Qobs=Qobs.as_matrix()

stations=pd.read_excel("data/Discharge/stations/4000/Q.xlsx",sheet_name="coordinates",convert_float=True)
coordinates=stations[['id','x','y','weight']][:]

# calculate the nearest cell to each station
coordinates.loc[:,["cell_row","cell_col"]]=GC.NearestCell(raster,coordinates)

acc=gdal.Open(FlowAccPath )
acc_A=acc.ReadAsArray()
# define the objective function and its arguments
OF_args=[coordinates]

"""
OF is the objective function used for the calibration
OF function locates each station and extract the UZ and LZ discharge for each
station and sum both then calculate the error based on RMSE and gives a weight
for each station (weights are given in the excel sheet read in
the variable stations)

This function only takes available data in a flow series for the calibration process,
since many times observed data have gaps.

"""
def OF(Qobs,Qout,q_uz_routed,q_lz_trans,coordinates):
    print('Starts OF', time.ctime())
    all_errors=[]
    for station_id in Qobs:
        Quz = np.reshape(q_uz_routed[int(coordinates.loc[station_id, "cell_row"]),int(coordinates.loc[station_id, "cell_col"]),:-1],len(Qobs))
        Qlz = np.reshape(q_lz_trans[int(coordinates.loc[station_id, "cell_row"]),int(coordinates.loc[station_id, "cell_col"]),:-1],len(Qobs))
        Q = Quz + Qlz
        #CREATE DATAFRAME WITH AVAILABLE QOBS DATA AND DATE INDEXING
        Qobs_inner_station = pd.notnull(Qobs[station_id])
        dates_Qobs_avail = Qobs[Qobs_inner_station].index.tolist()
        Qobs_avail_df = Qobs.loc[dates_Qobs_avail,str(station_id)].to_frame()
        #CREATE DATAFRAME WITH CALCULATED Q AND DATE INDEXING
        Qcal_df = pd.DataFrame(Q, columns=["Qcal"], index=pd.date_range(start=Sdate, end=Edate))
        #MERGE BOTH TO COMPARE Q ONLY IN THE DATES GIVEN BY THE AVAILABLE DATA
        Q_compared = pd.merge(left=Qobs_avail_df, left_index=True, right=Qcal_df, right_index=True, how='inner')
        error = PC.RMSE(Q_compared.loc[:,station_id].values,Q_compared.loc[:,'Qcal'].values)*coordinates.loc[station_id,'weight']
        all_errors.append(error)
    print(all_errors)
    error = np.nansum(all_errors)
    print('Ends OF', time.ctime())
    return error

### Optimization
store_history=1
history_fname="par_history.txt"
OptimizationArgs=[store_history,history_fname]
#%%
# run calibration
cal_parameters=RunCalibration(HBV, Paths, Basic_inputs,
                              SpatialVarFun, SpatialVarArgs,
                              OF,OF_args,Qobs,
                              OptimizationArgs,
                              printError=1)
#%% convert parameters to rasters
ParPath = "par15_7_2018.txt"
par=np.loadtxt(ParPath)
klb=0.5
kub=1
Path="parameters/"

#DP.SaveParameters(SpatialVarFun, raster, par, no_parameters,snow ,kub, klb,Path)
