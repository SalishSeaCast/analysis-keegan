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
    saveloc='/ocean/kflanaga/MEOPAR/savedData'

    paramlistPSF.append(dict(year=year,
                             modver=modver,
                             PATH=PATH,
                             saveloc=saveloc))
                            

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






              
           
