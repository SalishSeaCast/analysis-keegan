import papermill as pm
import re
import os

# PSF eval:
paramlistPSF=list()
year_range=range(2007,2019)
for y in year_range:
    years=[y,y+1]
    year=y+1
    modver='nowcast-green.201905'
    PATH= '/results2/SalishSea/nowcast-green.201905/'
    datadir='/ocean/kflanaga/MEOPAR/savedData/WADE_nutribot_pickles'

    paramlistPSF.append(dict(years=years,
                            year=year,
                            modver=modver,
                            PATH=PATH,
                            datadir=datadir))

for idict in paramlistPSF:
    newfname=f'WADE_Individual_year_evaluations/{idict["year"]}_Puget_Evaluation.ipynb'
    print(newfname)
    if os.path.isfile(newfname):
        os.remove(newfname)
    try:
        pm.execute_notebook(
           'WADE_Base_Puget_Evaluation.ipynb',
           newfname,
           parameters=idict
            );
    except:
        print('----------------------------------------------------------')
        print(f"WARNING Failure for in {newfname}")
        print('----------------------------------------------------------')






              
           
