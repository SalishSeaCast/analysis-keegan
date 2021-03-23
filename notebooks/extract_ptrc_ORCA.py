import datetime as dt
import subprocess
import numpy as np
import os
from salishsea_tools import places
import glob
import time
import sys

#dirname='spring2015_lowMuNano'
#salish options:
################
maxproc=4
saveloc='/ocean/kflanaga/MEOPAR/ptrc_tests/'
#Aloc='/data/eolson/MEOPAR/SS36runs/calcFiles/comparePhytoN/Area_240.nc'
#meshpath='/ocean/eolson/MEOPAR/NEMO-forcing/grid/mesh_mask201702_noLPE.nc'
#ptrcexpath='/results2/SalishSea/hindcast/05jul15/SalishSea_1h_20150705_20150705_ptrc_T.nc'
plist=['Hoodsport','Twanoh','DabobBay','PointWells','CarrInlet','Hansville']
varNameDict={'Hoodsport':'Hoodsport','Twanoh':'Twanoh','DabobBay':'DabobBay', 'PointWells':'PointWells',
             'CarrInlet':'CarrInlet', 'Hansville':'Hansville'}
t0=dt.datetime(2015,1,1)
fdur=1 # length of each results file in days
dirname='HC201905_2015'
te=dt.datetime(2015,1,2)

evars=('diatoms','ciliates','flagellates','nitrate')

###cedar options:
#################
#maxproc=6
#saveloc='/scratch/eolson/results/calcs/'
#Aloc='/scratch/eolson/results/calcs/Area_240.nc'
##meshpath='/ocean/eolson/MEOPAR/NEMO-forcing/grid/mesh_mask201702_noLPE.nc'
##ptrcexpath='/data/eolson/results/MEOPAR/SS36runs/CedarRuns/spring2015_KhT/SalishSea_1h_20150206_20150804_ptrc_T_20150616-20150625.nc'
#spath='/scratch/eolson/results/'+dirname+'/'
######################

def setup():
    spath='/results2/SalishSea/hindcast.201905/'
    ffmt='%Y%m%d'
    dfmt='%d%b%y'
    stencilp='{0}/SalishSea_1h_{1}_{1}_ptrc_T.nc'
    # Ok, so this probably imputs the day month year as {0} and then the rest of the info goes into the next 
    # part. This filling in probably happens with the help of the the format. 
    # My only question now is why does it use carp? Should probably change to Grid. but why is grid filled up
    # with stuff from carp t? must ask Elise. 
    stencile='{0}/SalishSea_1h_{1}_{1}_carp_T.nc'
    fnum=int(((te-t0).days+1)/fdur)#fnum=18 # number of results files per run
    runlen=fdur*fnum # length of run in days
    fnames={'ptrc_T':dict(),'grid_T':dict(),'tempBase':dict()}
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
        try:
            iifstr=glob.glob(spath+stencile.format(iits.strftime(dfmt).lower(),iits.strftime(ffmt),iite.strftime(ffmt)),recursive=True)[0]
            fnames['grid_T'][ind]=iifstr
        except:
            print('file does not exist:  '+spath+stencile.format(iits.strftime(dfmt).lower(),iits.strftime(ffmt),iite.strftime(ffmt)))
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
        f1=saveloc+'ts_'+dirname+'_'+varNameDict[pl]+'.nc'
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
    pids = runExtractPtrc();
    print('done extract ptrc')
    pids = runExtractLocs();
    print('done extract')
    pids = runJoinLocs();
    print('done join')