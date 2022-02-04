The Jupyter Notebook “Notebook_Ground_Air_Speed” is a collection of Python3 scripts aimed at calculating the air speed of targets (mostly birds) detected by NL radars. Data from the Herwijnen radar (NLHRW) is used here as an example.

When running the notebook, be sure to have in your folder the file “odimh5_file.py”, which contains functions to process ‘h5’ files.

The methodology can be summarized in following steps:
- Extract wind speeds at several altitude levels from ERA5<1> (note: wind speeds come as u0 and v0 components along latitudinal and longitudinal directions, respectively)
- Interpolate wind speeds at 200m height intervals
- Extract radar Doppler radial velocity (VRAD) components u, v, and w. These are the components of ground speed
- Correct u, v components of radar VRAD for u0, v0 wind components. The resulting components are air speed components

<1> ERA5 is the latest climate reanalysis produced by the European Center for Medium Range Weather forecast (ECMWF), providing hourly data on many atmospheric, land-surface and sea-state parameters together with estimates of uncertainty.
ERA5 data are available in the Climate Data Store https://cds.climate.copernicus.eu/cdsapp#!/home on regular latitude-longitude grids at 0.25 deg x 0.25 deg resolution, with atmospheric parameters on 37 pressure levels.

In this notebook, data on wind components at several pressure levels are used. You can request such data at https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-pressure-levels?tab=form once you login into your Copernicus account. 
You can also get the same data with an API request using the file “ERA5_request_pressure_levels.py” that has been uploaded to this folder. When Python3 is installed in your machine and the file is in your working space, you can just type “python3 ERA5_request_pressure_levels.py”.
The data file with wind components at the requested pressure levels has been uploaded to the Data folder with name “pressure_levels_wind_NLHRW_20190420.nc”

The radar data used in this notebook is a volume file containing 15 scans of NLHRW on 20-04-2019 at 00:40. You can find the file “NLHRW_pvol_20190420T0040_6356.h5” in the Data folder, or you can download it from the MinIo Browser:
https://fnwi-s0.science.uva.nl:9001/minio/pvol/
