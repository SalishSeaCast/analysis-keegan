import papermill as pm
import re
import os

# PSF eval:
paramlistPSF=list()
year_range=range(2010,2020)
for y in year_range:
    Mooring='Dockton'
    PATH= '/results2/SalishSea/nowcast-green.201905/'
    saveloc='/ocean/kflanaga/MEOPAR/mooredData'

    paramlistPSF.append(dict(saveloc=saveloc,
                             PATH=PATH,
                             year=y,
                             Mooring=Mooring))

for idict in paramlistPSF:
    newfname=f'{idict["Mooring"]}/{idict["year"]}_{idict["Mooring"]}_Timeseries.ipynb'
    print(newfname)
    if os.path.isfile(newfname):
        os.remove(newfname)
    try:
        pm.execute_notebook(
           'Dockton_Base_Timeseries.ipynb',
           newfname,
           parameters=idict
            );
    except:
        print('----------------------------------------------------------')
        print(f"WARNING Failure for in {newfname}")
        print('----------------------------------------------------------')






              
           
