import papermill as pm
import re
import os

# PSF eval:
modver='201905_Hindcast'
paramlistPSF=list()
year_range=range(2011,2019)
mooring_list=('CarrInlet','Hoodsport','PointWells','Twanoh')
ptrcloc='/ocean/kflanaga/MEOPAR/ptrc_extractions'
gridloc='/ocean/kflanaga/MEOPAR/grid_extractions'
ORCAloc='/ocean/kflanaga/MEOPAR/ORCAData'
for m in mooring_list:
    mooring=m
    for y in year_range:
        year=y
        paramlistPSF.append(dict(year=year,
                                mooring=mooring,
                                ptrcloc=ptrcloc
                                gridloc=gridloc
                                ORCAloc=ORCAloc))

for idict in paramlistPSF:
    newfname=f'{idict["mooring"]}/{modver}/{idict["year"]}_{idict["mooring"]}_Evaluation.ipynb'
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






              
           
