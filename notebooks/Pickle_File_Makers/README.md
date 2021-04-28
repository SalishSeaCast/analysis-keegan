The Jupyter Notebooks in this directory are made by Keegan Flanagan
for sharing of python code techniques and notes.

The links below are to static renderings of the notebooks via
[nbviewer.jupyter.org](https://nbviewer.jupyter.org/).
Descriptions under the links below are from the first cell of the notebooks
(if that cell contains Markdown or raw text).

* ## [CTD_Pickle_Loader.ipynb](https://nbviewer.jupyter.org/github/SalishSeaCast/analysis-keegan/blob/master/notebooks/Pickle_File_Makers/CTD_Pickle_Loader.ipynb)  
    
    This notebook Loads the Washington Department of Ecology (WADE) CTD data and matches it to the model output. It then saves the newly created matched dataframe as a Pickle file.

* ## [Chlbot_Pickle_Loader.ipynb](https://nbviewer.jupyter.org/github/SalishSeaCast/analysis-keegan/blob/master/notebooks/Pickle_File_Makers/Chlbot_Pickle_Loader.ipynb)  
    
    This notebook Loads the Washington Department of Ecology (WADE) chlorophyll bottle data and matches it to the WADE CTD data and the model data. It then saves the newly created matched dataframe as a Pickle file.

* ## [Dockton_Data_loader.ipynb](https://nbviewer.jupyter.org/github/SalishSeaCast/analysis-keegan/blob/master/notebooks/Pickle_File_Makers/Dockton_Data_loader.ipynb)  
    
    This script is used to extract the King County moored data from Dockton. It loads in the King County data as as a pandas dataframe from an excel file. These excel files are not organized to work as Pandas dataframes, so a significant amount of cleaning is necessary. Several additional variables have been calculated from the data to assist in matching this data to the SalishSeaCast model output. 

* ## [PointWilliams_Data_Loader.ipynb](https://nbviewer.jupyter.org/github/SalishSeaCast/analysis-keegan/blob/master/notebooks/Pickle_File_Makers/PointWilliams_Data_Loader.ipynb)  
    
    This script is used to extract the King County moored data from PointWilliams. It loads in the King County data as a pandas dataframe from an excel file. These excel files are not organized to work as Pandas dataframes, so a significant amount of cleaning is necessary. Several additional variables have been calculated from the data to assist in matching this data to the SalishSeaCast model output. 

* ## [WADE_Pickle_Loader.ipynb](https://nbviewer.jupyter.org/github/SalishSeaCast/analysis-keegan/blob/master/notebooks/Pickle_File_Makers/WADE_Pickle_Loader.ipynb)  
    
    This notebook Loads the Washington Department of Ecology (WADE) nutrient bottle data and matches it to the WADE CTD data and the model data. It then saves the newly created matched dataframe as a Pickle file.

* ## [Zooplankton_Data_Loader.ipynb](https://nbviewer.jupyter.org/github/SalishSeaCast/analysis-keegan/blob/master/notebooks/Pickle_File_Makers/Zooplankton_Data_Loader.ipynb)  
    
    **Warning!**
    This script does not contain completed work since I did not have time to finish the Zooplankton evaluations before the end of the position. HOWEVER. It does contain a quick and easy way to convert from northing and easting to latitude and longitude. 

* ## [nutchl_pickle_loader.ipynb](https://nbviewer.jupyter.org/github/SalishSeaCast/analysis-keegan/blob/master/notebooks/Pickle_File_Makers/nutchl_pickle_loader.ipynb)  
    
    This notebook was almost entirely designed by Elise Olson. It does a lot of cleaning for the Washington Department of Ecology nutrient and chlorophyll bottle collections that occured for 2018 and 2019. It is very important to understand that these chlorophyll and nutrient observations are independent of the ones that are loaded using WADE_Pickle_Loader and Chlbot_Pickle_Loader.  


##License

These notebooks and files are copyright 2013-2021
by the Salish Sea MEOPAR Project Contributors
and The University of British Columbia.

They are licensed under the Apache License, Version 2.0.
https://www.apache.org/licenses/LICENSE-2.0
Please see the LICENSE file for details of the license.
