import datetime as dt
import subprocess
import numpy as np
import os
from salishsea_tools import places
import glob
import time
import sys

###!!! Alright, that is sorted know. 
#The 2015 data goes from 0101 to 0630 and from 0701 to 1231
# The 2016 data goes from 0101 to 1120 and from 1116 to 1231
# Note that for the 2016 data you need to make an alteration to the first glob. 
# by switching tm1 to te. 

maxproc=4
spath='/home/sallen/202007/202007C-p3/'
saveloc='/ocean/kflanaga/MEOPAR/savedData/202007_ptrc_data/'
dirname='HC202007'
year=2016

#Defining the locations 
plist=['Hoodsport','Twanoh','DabobBay','PointWells','CarrInlet','Hansville']
varNameDict={'Hoodsport':'Hoodsport','Twanoh':'Twanoh','DabobBay':'DabobBay', 'PointWells':'PointWells',
             'CarrInlet':'CarrInlet', 'Hansville':'Hansville'}

#defining the timespan and time resoltuon
t0=dt.datetime(year,1,1)
tm1=dt.datetime(year,11,15)
tm2=dt.datetime(year,11,16)
te=dt.datetime(year,12,31)
fdur=1 # length of each results file in days

#defining the model variables to extract from ptrc
evars=('diatoms','ciliates','flagellates','nitrate')

def setup():
    ffmt='%Y%m%d'
    stencilp='SalishSea_1d_{0}_{1}_ptrc_T_{2}-{2}.nc'
    fnum=int(((te-t0).days+1)/fdur)#fnum=18 # number of results files per run
    runlen=fdur*fnum # length of run in days
    fnames={'ptrc_T':dict(),'tempBase':dict()}
    iits=t0
    ind=0
    while iits<=tm1:
        iite=iits+dt.timedelta(days=(fdur-1)) 
        iitn=iits+dt.timedelta(days=fdur)
        try:
            iifstr=glob.glob(spath+stencilp.format(t0.strftime(ffmt),te.strftime(ffmt),iits.strftime(ffmt),iite.strftime(ffmt)),recursive=True)[0]
            fnames['ptrc_T'][ind]=iifstr
        except:
            print('file does not exist: '+spath+stencilp.format(iits.strftime(ffmt),iite.strftime(ffmt)))
            raise
        fnames['tempBase'][ind]=saveloc+'temp/ptrc'+iits.strftime(ffmt)+'_'+iite.strftime(ffmt)
        iits=iitn
        ind=ind+1
    while iits<=te:
        iite=iits+dt.timedelta(days=(fdur-1)) 
        iitn=iits+dt.timedelta(days=fdur)
        try:
            iifstr=glob.glob(spath+stencilp.format(tm2.strftime(ffmt),te.strftime(ffmt),iits.strftime(ffmt),iite.strftime(ffmt)),recursive=True)[0]
            fnames['ptrc_T'][ind]=iifstr
        except:
            print('file does not exist: '+spath+stencilp.format(iits.strftime(ffmt),iite.strftime(ffmt)))
            raise
        fnames['tempBase'][ind]=saveloc+'temp/ptrc'+iits.strftime(ffmt)+'_'+iite.strftime(ffmt)
        iits=iitn
        ind=ind+1
    return spath,fnum,runlen,fnames


def runExtractptrc():
    pids=dict()
    for ii in range(0,fnum):
        # copy ptrc
        f0=fnames['tempBase'][ii]+'.nc'
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

# Hmmmm. I think that Join locs ran effectively. However, it appears that extract locs did not so it never actually concatenated anything. 

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


#pids= runExtractPtrc();
#
#pids= runAddE3t();
#
#pids= runAddA();
#
#pids= runExtractLocs();
#
#pids = runJoinLocs();
#
#pids = runMultAll();
#
#pids = runSumAll();
#
#pids = combAll();

if __name__ == "__main__":
    spath,fnum,runlen,fnames=setup();
    print('done setup')
    pids = runExtractptrc();
    print('done extract ptrc')
    pids = runExtractLocs();
    print('done extract')
    pids = runJoinLocs();
    print('done join')