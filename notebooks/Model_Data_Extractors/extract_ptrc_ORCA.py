import datetime as dt
import subprocess
import numpy as np
import os
from salishsea_tools import places
import glob
import time
import sys

maxproc=4
saveloc='/ocean/kflanaga/MEOPAR/savedData/201905_ptrc_data/'
dirname='HC201905'
year=2013

#Defining the locations 
plist=['Hoodsport','Twanoh','DabobBay','PointWells','CarrInlet','Hansville']
varNameDict={'Hoodsport':'Hoodsport','Twanoh':'Twanoh','DabobBay':'DabobBay', 'PointWells':'PointWells',
             'CarrInlet':'CarrInlet', 'Hansville':'Hansville'}

#defining the timespan and time resoltuon
t0=dt.datetime(year,1,1)
te=dt.datetime(year,12,31)
fdur=1 # length of each results file in days

#defining the model variables to extract from ptrc
evars=('diatoms','ciliates','flagellates','nitrate')


def setup():
    spath='/results2/SalishSea/hindcast.201905/'
    ffmt='%Y%m%d'
    dfmt='%d%b%y'
    stencilp='{0}/SalishSea_1d_{1}_{1}_ptrc_T.nc'
    stencile='{0}/SalishSea_1d_{1}_{1}_carp_T.nc'
    fnum=int(((te-t0).days+1)/fdur)#fnum=18 # number of results files per run
    runlen=fdur*fnum # length of run in days
    fnames={'ptrc_T':dict(),'tempBase':dict()}
    iits=t0
    ind=0
    while iits<=te:
        iite=iits+dt.timedelta(days=(fdur-1)) # why is it minus one?
        iitn=iits+dt.timedelta(days=fdur)
        try:
            iifstr=glob.glob(spath+stencilp.format(iits.strftime(dfmt).lower(),iits.strftime(ffmt),iite.strftime(ffmt)),recursive=True)[0]
            fnames['ptrc_T'][ind]=iifstr
        except:
            print('file does not exist:  '+spath+stencilp.format(iits.strftime(dfmt).lower(),iits.strftime(ffmt),iite.strftime(ffmt)))
            raise
        fnames['tempBase'][ind]=saveloc+'temp/ptrc'+iits.strftime(ffmt)+'_'+iite.strftime(ffmt)
        iits=iitn
        ind=ind+1
    return spath,fnum,runlen,fnames

def runExtractPtrc():
    pids=dict()
    for ii in range(0,fnum):
        # copy ptrc
        f0=fnames['tempBase'][ii]+''+'.nc'
        if os.path.exists(f0):
            os.remove(f0)
        pids[ii]=subprocess.Popen('ncks -v '+','.join(evars)+' '+fnames['ptrc_T'][ii]+' '+f0, shell=True,
                                           stdout=subprocess.PIPE,  stderr=subprocess.PIPE)
        if ii%maxproc==(maxproc-1):
            for jj in range(0,ii):
                pids[jj].wait() # wait for the last one in set
    for jj in range(0,ii):
        pids[jj].wait()
    #pids[ii].wait() # wait for the last one
    # check that no others are still running, wait for them
    for ipid in pids.keys():
        while pids[ipid].poll() is None:
            time.sleep(30)
    for ipid in pids.keys():
        for line in pids[ipid].stdout:
            print(line)
        print(pids[ipid].returncode)
        pids[ipid].stdout.close()
        pids[ipid].stderr.close()
    print(pids)
    return pids

def runExtractLocs():
    # extract phyto at locs
    for pl in plist:
        pids=dict()
        for ii in range(0,fnum):
            f0=fnames['tempBase'][ii]+'.nc'
            fpl=fnames['tempBase'][ii]+varNameDict[pl]+'.nc'
            j,i=places.PLACES[pl]['NEMO grid ji']
            if os.path.exists(fpl):
                os.remove(fpl)
            pids[ii]=subprocess.Popen('ncks -v '+','.join(evars)+' -d x,'+str(i)+' -d y,'+str(j)+' '+f0+' '+fpl, shell=True,
                                           stdout=subprocess.PIPE,  stderr=subprocess.PIPE)
            if ii%maxproc==(maxproc-1):
                pids[ii].wait() # wait for the last one in set
        pids[ii].wait() # wait for the last one
        # check that no others are still running, wait for them
        for ipid in pids.keys():
            while pids[ipid].poll() is None:
                time.sleep(30)
        for ipid in pids.keys():
            for line in pids[ipid].stdout:
                print(line)
            pids[ipid].stdout.close()
            pids[ipid].stderr.close()
            print(pids[ipid].returncode)
    return pids

def runJoinLocs():
    pids=dict()
    jj=0
    for pl in plist:
        fpllist=list()
        f1=saveloc+'ts_'+dirname+'_'+str(year)+'_'+varNameDict[pl]+'.nc'
        if os.path.exists(f1):
            os.remove(f1)
        for ii in range(0,fnum):
            fpllist.append(fnames['tempBase'][ii]+varNameDict[pl]+'.nc')
        pids[jj]=subprocess.Popen('ncrcat '+' '.join(fpllist)+' '+f1, shell=True,
                                           stdout=subprocess.PIPE,  stderr=subprocess.PIPE)
        if jj%maxproc==(maxproc-1):
            pids[jj].wait() # wait for the last one in set
        jj+=1
    pids[jj-1].wait() # wait for the last one
    # check that no others are still running, wait for them
    for ipid in pids.keys():
        while pids[ipid].poll() is None:
            time.sleep(30)
    for ipid in pids.keys():
        for line in pids[ipid].stdout:
            print(line)
        print(pids[ipid].returncode)
        pids[ipid].stdout.close()
        pids[ipid].stderr.close()
    return pids

if __name__ == "__main__":
    spath,fnum,runlen,fnames=setup();
    print('done setup')
    pids = runExtractPtrc();
    print('done extract ptrc')
    pids = runExtractLocs();
    print('done extract')
    pids = runJoinLocs();
    print('done join')
