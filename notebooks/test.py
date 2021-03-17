import datetime as dt
import subprocess
import numpy as np
import os
from salishsea_tools import places
import glob
import time
import sys

def test():
    pids=dict()
    pids[0]= subprocess.Popen('ncks -v diatoms,ciliates,flagellates /results2/SalishSea/hindcast.201905/14apr09/SalishSea_1h_20090414_20090414_ptrc_T.nc /ocean/kflanaga/MEOPAR/ptrc_extractions/ptrc20090414-20090414.nc'
    ,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return pids
                    
if __name__ == "__main__":
    pids = test();
    print('done test')