import papermill as pm
import re
import os

# PSF eval:
saveloc='201905_Hindcast' 
paramlistPSF=list()
year_range=range(2013,2020)
mooring_list=('CarrInlet','Hoodsport','PointWells','Twanoh','Hansville','DabobBay')
modver='HC201905' #HC202007 is the other option.
ptrcloc='/ocean/kflanaga/MEOPAR/savedData/201905_ptrc_data'
gridloc='/ocean/kflanaga/MEOPAR/savedData/201905_grid_data'
ORCAloc='/ocean/kflanaga/MEOPAR/savedData/ORCAData'
for m in mooring_list:
    mooring=m
    for y in year_range:
        year=y
        paramlistPSF.append(dict(year=year,
                                modver=modver,
                                mooring=mooring,
                                ptrcloc=ptrcloc,
                                gridloc=gridloc,
                                ORCAloc=ORCAloc))

for idict in paramlistPSF:
    newfname=f'{idict["mooring"]}/{saveloc}/{idict["year"]}_{idict["mooring"]}_Evaluations.ipynb'
    print(newfname)
    if os.path.isfile(newfname):
        os.remove(newfname)
    try:
        pm.execute_notebook(
           'Base_All_Depths.ipynb',
           newfname,
           parameters=idict
            );
    except:
        print('----------------------------------------------------------')
        print(f"WARNING Failure for in {newfname}")
        print('----------------------------------------------------------')






              
           
