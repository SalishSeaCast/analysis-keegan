import papermill as pm
import re
import os

# PSF eval:
paramlistPSF=list()
year_range=range(2015,2017)
mooring_list=('CarrInlet','Hoodsport','PointWells','Twanoh','Hansville')
for m in mooring_list:
    mooring=m
    for y in year_range:
        year=y
        paramlistPSF.append(dict(year=year,
                                mooring=mooring))

for idict in paramlistPSF:
    newfname=f'{idict["mooring"]}/201905_202007_comparison/{idict["year"]}_{idict["mooring"]}_Comparisons.ipynb'
    print(newfname)
    if os.path.isfile(newfname):
        os.remove(newfname)
    try:
        pm.execute_notebook(
           'Base_model_comparison.ipynb',
           newfname,
           parameters=idict
            );
    except:
        print('----------------------------------------------------------')
        print(f"WARNING Failure for in {newfname}")
        print('----------------------------------------------------------')






              
           
