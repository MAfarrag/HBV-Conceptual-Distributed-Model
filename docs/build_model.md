# Distributed Hydrological Model

After preparing all the meteorological, GIS inputs required for the model, and Extracting the parameters for the catchment 

## 1- Catchment Object
- Import the Catchment object which is the main object in the distributed model, to read and check the input data,  and when the model finish the simulation it stores the results and do the visualization


```

	class Catchment():

	    ======================
	       Catchment
	    ======================
	    Catchment class include methods to read the meteorological and Spatial inputs
	    of the distributed hydrological model. Catchment class also reads the data
	    of the gauges, it is a super class that has the run subclass, so you
	    need to build the catchment object and hand it as an inpit to the Run class
	    to run the model

	    methods:
	        1-ReadRainfall
	        2-ReadTemperature
	        3-ReadET
	        4-ReadFlowAcc
	        5-ReadFlowDir
	        6-ReadFlowPathLength
	        7-ReadParameters
	        8-ReadLumpedModel
	        9-ReadLumpedInputs
	        10-ReadGaugeTable
	        11-ReadDischargeGauges
	        12-ReadParametersBounds
	        13-ExtractDischarge
	        14-PlotHydrograph
	        15-PlotDistributedQ
	        16-SaveResults

	    def __init__(self, name, StartDate, EndDate, fmt="%Y-%m-%d", SpatialResolution = 'Lumped',
	                 TemporalResolution = "Daily"):
	        =============================================================================
	            Catchment(name, StartDate, EndDate, fmt="%Y-%m-%d", SpatialResolution = 'Lumped',
	                             TemporalResolution = "Daily")
	        =============================================================================
	        Parameters
	        ----------
	        name : [str]
	            Name of the Catchment.
	        StartDate : [str]
	            starting date.
	        EndDate : [str]
	            end date.
	        fmt : [str], optional
	            format of the given date. The default is "%Y-%m-%d".
	        SpatialResolution : TYPE, optional
	            Lumped or 'Distributed' . The default is 'Lumped'.
	        TemporalResolution : TYPE, optional
	            "Hourly" or "Daily". The default is "Daily".
```

- To instantiate the object you need to provide the `name`, `statedate`, `enddate`, and the `SpatialResolution`

```
		from Hapi.catchment import Catchment

		start = "2009-01-01"
		end = "2011-12-31"
		name = "Coello"

		Coello = Catchment(name, start, end, SpatialResolution = "Distributed")
```

## Read Meteorological Inputs

- First define the directory where the data exist

```
			PrecPath = "Hapi/Data/00inputs/meteodata/4000/calib/prec-CPC-NOAA" #
			Evap_Path = "Hapi/Data/00inputs/meteodata/4000/calib/evap"
			TempPath = "Hapi/Data/00inputs/meteodata/4000/calib/temp"
			FlowAccPath = "Hapi/Data/00inputs/GIS/4000/acc4000.tif"
			FlowDPath = "Hapi/Data/00inputs/GIS/4000/fd4000.tif"
			ParPathRun = "Hapi/Model/results/parameters/02lumped parameters/Parameter set-1/"
			SaveTo = "Hapi/Model/results/"
```

- Then use the each method in the object to read the coresponding data

```
			Coello.ReadRainfall(PrecPath)
			Coello.ReadTemperature(TempPath)
			Coello.ReadET(Evap_Path)
			Coello.ReadFlowAcc(FlowAccPath)
			Coello.ReadFlowDir(FlowDPath)
```

- To read the parameters you need to provide whether you need to consider the snow subroutine or not

```
			Snow = 0
			Coello.ReadParameters(ParPathRun, Snow)
```

### 2- Lumped Model
- Get the Lumpde conceptual model you want to couple it with the distributed routing module which in our case HBV 
	and define the initial condition, and catchment area.
```
			import Hapi.hbv_bergestrom92 as HBV

			CatchmentArea = 1530
			InitialCond = [0,5,5,5,0]
			Coello.ReadLumpedModel(HBV, CatchmentArea, InitialCond)
```
- If the Inpus are consistent in dimensions you will get a the following message

![check_inputs](../img/check_inputs.png)

- to check the performance of the model we need to read the gauge hydrographs

```
Coello.ReadGaugeTable("Hapi/Data/00inputs/Discharge/stations/gauges.csv", FlowAccPath)
GaugesPath = "Hapi/Data/00inputs/Discharge/stations/"
Coello.ReadDischargeGauges(GaugesPath, column='id', fmt="%Y-%m-%d")
```

### 3-Run Object

- The `Run` object connects all the components of the simulation together, the `Catchment` object, the `Lake` object and the `distributedrouting` object
- import the Run object and use the `Catchment` object as a parameter to the `Run` object, then call the RunHapi method to start the simulation

```
			from Hapi.run import Run
			Run.RunHapi(Coello)
```

- the result of the simulation will be stored as attributes in the Catchment object as follow

Outputs:
    1-statevariables: [numpy attribute]
        4D array (rows,cols,time,states) states are [sp,wc,sm,uz,lv]
    2-qlz: [numpy attribute]
        3D array of the lower zone discharge
    3-quz: [numpy attribute]
        3D array of the upper zone discharge
    4-qout: [numpy attribute]
        1D timeseries of discharge at the outlet of the catchment
        of unit m3/sec
    5-quz_routed: [numpy attribute]
        3D array of the upper zone discharge  accumulated and
        routed at each time step
    6-qlz_translated: [numpy attribute]
        3D array of the lower zone discharge translated at each time step

### 4-Extract Hydrographs

- The final step is to extract the simulated Hydrograph from the cells at the location of the gauges to compare
- The `ExtractDischarge` method extracts the hydrographs, however you have to provide in the gauge file the coordinates of the gauges with the same coordinate system of the `FlowAcc` raster

```
			Coello.ExtractDischarge(Factor=Coello.GaugesTable['area ratio'].tolist())

			for i in range(len(Coello.GaugesTable)):
			    gaugeid = Coello.GaugesTable.loc[i,'id']
			    print("----------------------------------")
			    print("Gauge - " +str(gaugeid))
			    print("RMSE= " + str(round(Coello.Metrics.loc['RMSE',gaugeid],2)))
			    print("NSE= " + str(round(Coello.Metrics.loc['NSE',gaugeid],2)))
			    print("NSEhf= " + str(round(Coello.Metrics.loc['NSEhf',gaugeid],2)))
			    print("KGE= " + str(round(Coello.Metrics.loc['KGE',gaugeid],2)))
			    print("WB= " + str(round(Coello.Metrics.loc['WB',gaugeid],2)))
			    print("Pearson CC= " + str(round(Coello.Metrics.loc['Pearson-CC',gaugeid],2)))
			    print("R2 = " + str(round(Coello.Metrics.loc['R2',gaugeid],2)))
```

- The `ExtractDischarge` will print the performance metics


### 5-Visualization

- Firts type of visualization we can do with the results is to compare the gauge hydrograph with the simulatied hydrographs 
- Call the `PlotHydrograph` method and provide the period you want to visualize with the order of the gauge

```
		gaugei = 5
		plotstart = "2009-01-01"
		plotend = "2011-12-31"

		Coello.PlotHydrograph(plotstart, plotend, gaugei)
```

![hydrograph](../img/hydrograph.png) 


### 6-Animation

- the best way to visualize time series of distributed data is through visualization, for theis reason, The `Catchment` object has `PlotDistributedResults` method which can animate all the results of the model

```
				=============================================================================
				AnimateArray(Arr, Time, NoElem, TicksSpacing = 2, Figsize=(8,8), PlotNumbers=True,
				       NumSize= 8, Title = 'Total Discharge',titlesize = 15, Backgroundcolorthreshold=None,
				       cbarlabel = 'Discharge m3/s', cbarlabelsize = 12, textcolors=("white","black"),
				       Cbarlength = 0.75, Interval = 200,cmap='coolwarm_r', Textloc=[0.1,0.2],
				       Gaugecolor='red',Gaugesize=100, ColorScale = 1,gamma=1./2.,linthresh=0.0001,
				       linscale=0.001, midpoint=0, orientation='vertical', rotation=-90,IDcolor = "blue",
				          IDsize =10, **kwargs)
				=============================================================================
				Parameters
				----------
				Arr : [array]
				    the array you want to animate.
				Time : [dataframe]
				    dataframe contains the date of values.
				NoElem : [integer]
				    Number of the cells that has values.
				TicksSpacing : [integer], optional
				    Spacing in the colorbar ticks. The default is 2.
				Figsize : [tuple], optional
				    figure size. The default is (8,8).
				PlotNumbers : [bool], optional
				    True to plot the values intop of each cell. The default is True.
				NumSize : integer, optional
				    size of the numbers plotted intop of each cells. The default is 8.
				Title : [str], optional
				    title of the plot. The default is 'Total Discharge'.
				titlesize : [integer], optional
				    title size. The default is 15.
				Backgroundcolorthreshold : [float/integer], optional
				    threshold value if the value of the cell is greater, the plotted
				    numbers will be black and if smaller the plotted number will be white
				    if None given the maxvalue/2 will be considered. The default is None.
				textcolors : TYPE, optional
				    Two colors to be used to plot the values i top of each cell. The default is ("white","black").
				cbarlabel : str, optional
				    label of the color bar. The default is 'Discharge m3/s'.
				cbarlabelsize : integer, optional
				    size of the color bar label. The default is 12.
				Cbarlength : [float], optional
				    ratio to control the height of the colorbar. The default is 0.75.
				Interval : [integer], optional
				    number to controlthe speed of the animation. The default is 200.
				cmap : [str], optional
				    color style. The default is 'coolwarm_r'.
				Textloc : [list], optional
				    location of the date text. The default is [0.1,0.2].
				Gaugecolor : [str], optional
				    color of the points. The default is 'red'.
				Gaugesize : [integer], optional
				    size of the points. The default is 100.
				IDcolor : [str]
				    the ID of the Point.The default is "blue".
				IDsize : [integer]
				    size of the ID text. The default is 10.
				ColorScale : integer, optional
				    there are 5 options to change the scale of the colors. The default is 1.
				    1- ColorScale 1 is the normal scale
				    2- ColorScale 2 is the power scale
				    3- ColorScale 3 is the SymLogNorm scale
				    4- ColorScale 4 is the PowerNorm scale
				    5- ColorScale 5 is the BoundaryNorm scale
				    ------------------------------------------------------------------
				    gamma : [float], optional
				        value needed for option 2 . The default is 1./2..
				    linthresh : [float], optional
				        value needed for option 3. The default is 0.0001.
				    linscale : [float], optional
				        value needed for option 3. The default is 0.001.
				    midpoint : [float], optional
				        value needed for option 5. The default is 0.
				    ------------------------------------------------------------------
				orientation : [string], optional
				    orintation of the colorbar horizontal/vertical. The default is 'vertical'.
				rotation : [number], optional
				    rotation of the colorbar label. The default is -90.
				**kwargs : [dict]
				    keys:
				        Points : [dataframe].
				            dataframe contains two columns 'cell_row', and cell_col to
				            plot the point at this location

				Returns
				-------
				animation.FuncAnimation.

```

- choose the period of time you want to animate and the result (total discharge, upper zone discharge, soil moisture,...)

```
			plotstart = "2009-01-01"
			plotend = "2009-02-01"

			Anim = Coello.PlotDistributedResults(plotstart, plotend, Figsize=(9,9), Option = 1,threshold=160, PlotNumbers=True,
			                                TicksSpacing = 5,Interval = 200, Gauges=True, cmap='inferno', Textloc=[0.1,0.2],
			                                Gaugecolor='red',ColorScale = 1, IDcolor='blue', IDsize=25)
```

<!-- blank line -->
<figure class="video_container">
  <video controls="true" allowfullscreen="true" poster="../img/anim.gif">
    <source src="../img/anim.mp4" type="video/mp4">
  </video>
</figure>
<!-- blank line -->

- to save the animation

	- Please visit https://ffmpeg.org/ and download a version of ffmpeg compitable with your operating system 
	- Copy the content of the folder and paste it in the "c:/user/.matplotlib/ffmpeg-static/"
	or

	- define the path where the downloaded folder "ffmpeg-static" exist to matplotlib using the following lines 

	``` 
	import matplotlib as mpl
	mpl.rcParams['animation.ffmpeg_path'] = "path where you saved the ffmpeg.exe/ffmpeg.exe" 
	```

```
			Path = SaveTo + "anim.gif"
			Coello.SaveAnimation(VideoFormat="gif",Path=Path,SaveFrames=3)
```


### 7-Save the result into rasters

- To save the results as rasters provide the period and the path 

```
		StartDate = "2009-01-01"
		EndDate = "2010-04-20"
		Prefix = 'Qtot_'

		Coello.SaveResults(FlowAccPath, Result=1, StartDate=StartDate, EndDate=EndDate,
		                    Path="F:/02Case studies/Coello/Hapi/Model/results/", Prefix=Prefix)
```