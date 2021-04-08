import papermill as pm
import re
import os

# PSF eval:
paramlistPSF=list()
year_range=range(2007,2020)
for y in year_range:
    year=y
    modver='nowcast-green.201905'
    PATH= '/results2/SalishSea/nowcast-green.201905/'
    nutribot_datadir='/ocean/kflanaga/MEOPAR/savedData/WADE_nutribot_pickles/'
    chlorobot_datadir='/ocean/kflanaga/MEOPAR/savedData/WADE_chlorobot_pickles/'

    paramlistPSF.append(dict(year=year,
                             modver=modver,
                             PATH=PATH,
                             chlorobot_datadir=chlorobot_datadir,
                             nutribot_datadir=nutribot_datadir))
                            

for idict in paramlistPSF:
    newfname=f'Timeseries_Individual_Years/{idict["year"]}_Timeseries_Puget_Evaluation.ipynb'
    print(newfname)
    if os.path.isfile(newfname):
        os.remove(newfname)
    try:
        pm.execute_notebook(
           'Timeseries_Base_Puget_Evaluation.ipynb',
           newfname,
           parameters=idict
            );
    except:
        print('----------------------------------------------------------')
        print(f"WARNING Failed to complete {newfname}")
        print('----------------------------------------------------------')






              
           
