""" Functions used to quickly graph evaluation plots for multiple stations and regions.
"""
import numpy as np
import numpy.polynomial.polynomial as poly
import matplotlib.pyplot as plt
import os
import math
import pandas as pd
import netCDF4 as nc
import datetime as dt
from salishsea_tools import evaltools as et, viz_tools
import gsw 
import matplotlib.gridspec as gridspec
import matplotlib as mpl
import matplotlib.dates as mdates
import cmocean as cmo
import scipy.interpolate as sinterp
import pickle
import cmocean
import json
import f90nml
from collections import OrderedDict
from matplotlib.colors import LogNorm

colors=('blue','green','firebrick','darkorange','darkviolet','fuchsia',
        'royalblue','darkgoldenrod','mediumspringgreen','deepskyblue')

def _deframe(x):
    # if array is pandas series or dataframe, return the values only
    if isinstance(x,pd.Series) or isinstance(x,pd.DataFrame):
        x=x.values.flatten()
    return x

def load_Pheo_data(year,datadir='/ocean/eolson/MEOPAR/obs/WADE/ptools_data/ecology'):
    """ This function automatically loads the chlorophyll bottle data from WADE for a 
        given year specified by the user. The output is a pandas dataframe with all of 
        the necessary columns and groups needed for matching to the model data. 
    """
    ## duplicate Station/Date entries with different times seem to be always within a couple of hours, 
    # so just take the first (next cell)
    dfTime=pd.read_excel('/ocean/eolson/MEOPAR/obs/WADE/WDE_Data/OlsonSuchyAllen_UBC_PDR_P003790-010721.xlsx',
                        engine='openpyxl',sheet_name='EventDateTime')
    test=dfTime.groupby(['FlightDate','SiteCode'])['TimeDown \n(Local - PST or PDT)'].count()
    # drop duplicate rows
    dfTime.drop_duplicates(subset=['FlightDate','SiteCode'],keep='first',inplace=True)
    print(dfTime.keys())
    dfTime['dtPac']=[dt.datetime.combine(idate, itime) for idate, itime \
             in zip(dfTime['FlightDate'],dfTime['TimeDown \n(Local - PST or PDT)'])]
    dfTime['dtUTC']=[et.pac_to_utc(ii) for ii in dfTime['dtPac']]
    # PROCESS STATION LOCATION INFO (based on Parker's code)
    sta_fn='/ocean/eolson/MEOPAR/obs/WADE/WDE_Data/OlsonSuchyAllen_UBC_PDR_P003790-010721.xlsx'
    sheetname='Site Info'
    sta_df =pd.read_excel(sta_fn,engine='openpyxl',sheet_name=sheetname)
    sta_df.dropna(how='any',subset=['Lat_NAD83 (deg / dec_min)','Long_NAD83 (deg / dec_min)','Station'],inplace=True)
    sta_df = sta_df.set_index('Station')
    # get locations in decimal degrees
    for sta in sta_df.index:
        lat_str = sta_df.loc[sta, 'Lat_NAD83 (deg / dec_min)']
        lat_deg = float(lat_str.split()[0]) + float(lat_str.split()[1])/60
        sta_df.loc[sta,'Lat'] = lat_deg
        #
        lon_str = sta_df.loc[sta, 'Long_NAD83 (deg / dec_min)']
        lon_deg = float(lon_str.split()[0]) + float(lon_str.split()[1])/60
        sta_df.loc[sta,'Lon'] = -lon_deg    
    sta_df.pop('Lat_NAD83 (deg / dec_min)');
    sta_df.pop('Long_NAD83 (deg / dec_min)');
    fn='/ocean/eolson/MEOPAR/obs/WADE/WDE_Data/OlsonSuchyAllen_UBC_PDR_P003790-010721.xlsx'
    sheetname='LabChlaPheo'
    chlPheo =pd.read_excel(fn,engine='openpyxl',sheet_name=sheetname)
    chlPheo.dropna(how='any',subset=['Date','Station','SamplingDepth'],inplace=True)
    # average over replicates
    chlPheo2=pd.DataFrame(chlPheo.groupby(['Date','Station','SamplingDepth'],as_index=False).mean())
    # join to station info (lat/lon)
    chlPheo3=pd.merge(left=sta_df,right=chlPheo2,how='right',
                     left_on='Station',right_on='Station')
    # join to date/time
    dfTime['dtUTC']=[et.pac_to_utc(dt.datetime.combine(idate,itime)) for idate,itime in \
                    zip(dfTime['FlightDate'],dfTime['TimeDown \n(Local - PST or PDT)'])]
    dfTime2=dfTime.loc[:,['FlightDate','SiteCode','dtUTC']]
    chlPheoFinal=pd.merge(left=chlPheo3,right=dfTime2,how='left',
                          left_on=['Date','Station'],right_on=['FlightDate','SiteCode'])
    #drop the 47 NA datetime values
    chlPheoFinal.dropna(how='any',subset=['dtUTC'],inplace=True)
    #Add extra columns for later use
    chlPheoFinal['Z']=chlPheoFinal['SamplingDepth']
    chlPheoFinal['Year']=[ii.year for ii in chlPheoFinal['dtUTC']]
    chlPheoFinal['YD']=et.datetimeToYD(chlPheoFinal['dtUTC'])
    chlPheoYear=pd.DataFrame(chlPheoFinal.loc[chlPheoFinal.Year==year])
    return chlPheoYear
    
def interpCTDvar(sta,yr,yd,ztarget,ctdvar):
    ctdlocs=(dfCTD.Station==sta)&(dfCTD.Year==yr)&(dfCTD.YD==yd)
    if np.sum(ctdlocs)==0:
        print(f'Warning: Station {sta}, Year {yr}, year day {yd} not found in dfCTD')
        return np.nan
    else:
        val=np.interp(ztarget,dfCTD.loc[ctdlocs,['Z']].values.flatten(),
                  dfCTD.loc[ctdlocs,[ctdvar]].values.flatten())
        return val

def load_WADE_data(year,datadir='/ocean/eolson/MEOPAR/obs/WADE/ptools_data/ecology'):
    """ This function automatically loads the nutrient bottle data from WADE for a given year
        specified by the user. The output is a pandas dataframe with all of te necessary 
        columns and groups needed for matching to the model data. 
    """
    dfSta=pickle.load(open(os.path.join(datadir,'sta_df.p'),'rb'))
    dfBot=pickle.load(open(os.path.join(datadir,f'Bottles_{str(year)}.p'),'rb'))
    df=pd.merge(left=dfSta,right=dfBot,how='right',
             left_on='Station',right_on='Station')
    try:
        len(df.loc[pd.isnull(df['Latitude'])]) == 0
    except:
        pass
        print('Warning!, Stations found without Latitude or Longitude value!')
    try:
        len(df) == len(dfBot)
    except:
        pass
        print(f'Warning!, Merge completed incorrectly. length of bottle data = {len(dfBot)} length of merged data = {len(df)}')
    # where no time is provided, set time to midday Pacific time = ~ 20:00 UTC
    df['UTCDateTime']=[iiD+dt.timedelta(hours=20) if pd.isnull(iiU) \
                    else iiU for iiU,iiD in \
                    zip(df['UTCDateTime'],df['Date'])]
    df.rename(columns={'UTCDateTime':'dtUTC','Latitude':'Lat','Longitude':'Lon'},inplace=True)
    df['Z']=-1*df['Z']
    df.head()
    df['NO23']=df['NO3(uM)D']+df['NO2(uM)D'] # the model does not distinguish between NO2 and NO3
    df['Amm']=df['NH4(uM)D']
    df['Si']=df['SiOH4(uM)D']
    df['Year']=[ii.year for ii in df['dtUTC']]
    df['YD']=et.datetimeToYD(df['dtUTC'])
    return(df)
   
    
def load_CTD_data(year,datadir='/ocean/eolson/MEOPAR/obs/WADE/ptools_data/ecology'):
    """ Returns a dataframe containing CTD data for a given year merged with station data
    """
    dfSta=pickle.load(open(os.path.join(datadir,'sta_df.p'),'rb'))
    dfCTD0=pickle.load(open(os.path.join(datadir,f'Casts_{str(year)}.p'),'rb'))
    dfCTD=pd.merge(left=dfSta,right=dfCTD0,how='right',
             left_on='Station',right_on='Station')
    try:
        dfCTD.groupby(['Station','Year','YD','Z']).count()==[1]
    except:
        pass
        print('Only one cast per CTD station per day')
    # where no time is provided, set time to midday Pacific time = ~ 20:00 UTC
    dfCTD['dtUTC']=[iiD+dt.timedelta(hours=20) for iiD in dfCTD['Date']] #Does this mean it also has that flaw where we are not sure when the data was collected?
    dfCTD.rename(columns={'Latitude':'Lat','Longitude':'Lon'},inplace=True)
    dfCTD['Z']=-1*dfCTD['Z']
    # Calculate Absolute (Reference) Salinity (g/kg) and Conservative Temperature (deg C) from 
    # Salinity (psu) and Temperature (deg C):
    press=gsw.p_from_z(-1*dfCTD['Z'],dfCTD['Lat'])
    dfCTD['SA']=gsw.SA_from_SP(dfCTD['Salinity'],press,
                           dfCTD['Lon'],dfCTD['Lat'])
    dfCTD['CT']=gsw.CT_from_t(dfCTD['SA'],dfCTD['Temperature'],press)
    dfCTD['Year']=[ii.year for ii in dfCTD['dtUTC']]
    dfCTD['YD']=et.datetimeToYD(dfCTD['dtUTC'])
    return(dfCTD)

def byDepth(ax,df,obsvar,modvar,lims):
    ps=et.varvarPlot(ax,df,obsvar,modvar,'Z',(15,22),'z','m',('mediumseagreen','darkturquoise','navy'))
    l=ax.legend(handles=ps)
    ax.set_xlabel('Obs')
    ax.set_ylabel('Model')
    ax.plot(lims,lims,'k-',alpha=.5)
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_aspect(1)
    return ps,l

def byRegion(ax,df,datreg,obsvar,modvar,lims):
    ps=[]
    for ind, iregion in enumerate(df.Basin.unique()):
        ax.plot(datreg[iregion]['Lon'], datreg[iregion]['Lat'],'.',
                color = colors[ind], label=iregion)
        ps0=et.varvarPlot(ax,datreg[iregion],obsvar,modvar,
                        cols=(colors[ind],),lname=iregion)
        ps.append(ps0)
    l=ax.legend(handles=[ip[0][0] for ip in ps])
    ax.set_xlabel('Obs')
    ax.set_ylabel('Model')
    ax.plot(lims,lims,'k-',alpha=.5)
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_aspect(1)
    return ps,l

def byStation(ax,df,datstat,region,obsvar,modvar,lims):
    ps=[]
    for ind, istation in enumerate(df[df['Basin'] == region].Station.unique()):
        ax.plot(datstat[istation]['Lon'], datstat[istation]['Lat'],'.',
                    color = colors[ind], label=istation)
        ps0=et.varvarPlot(ax,datstat[istation],obsvar,modvar,
                        cols=(colors[ind],),lname=istation)
        ps.append(ps0)
    l=ax.legend(title='Stations',title_fontsize=20,handles=[ip[0][0] for ip in ps])
    ax.set_xlabel('Obs')
    ax.set_ylabel('Model')
    ax.plot(lims,lims,'k-',alpha=.5)
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_aspect(1)
    return ps,l

def bySeason(ax,seasons,obsvar,modvar,lims,season_titles=['Jan-Mar','Apr','May-Aug','Sep-Dec']):
    for axi in ax:
        axi.plot(lims,lims,'k-')
        axi.set_xlim(lims)
        axi.set_ylim(lims)
        axi.set_aspect(1)
        axi.set_xlabel('Obs')
        axi.set_ylabel('Model')
    ps=et.varvarPlot(ax[0],seasons[0],obsvar,modvar,cols=('crimson','darkturquoise','navy'))
    ax[0].set_title(season_titles[0])
    ps=et.varvarPlot(ax[1],seasons[1],obsvar,modvar,cols=('crimson','darkturquoise','navy'))
    ax[1].set_title(season_titles[1])
    ps=et.varvarPlot(ax[2],seasons[2],obsvar,modvar,cols=('crimson','darkturquoise','navy'))
    ax[2].set_title(season_titles[2])
    ps=et.varvarPlot(ax[3],seasons[3],obsvar,modvar,cols=('crimson','darkturquoise','navy'))
    ax[3].set_title(season_titles[3])
    return 

def hist2d(ax,fig,df,obsvar,modvar,lims,fontsize=12):
    ax.plot(lims,lims,'k-',alpha=.2)
    ii=(~np.isnan(df[obsvar]))&(~np.isnan(df[modvar]))
    counts, xedges, yedges, ps=ax.hist2d(df.loc[ii,[obsvar]].values.flatten(),
                                      df.loc[ii,[modvar]].values.flatten(),bins=25*3,norm=LogNorm())
    cb=fig.colorbar(ps,ax=ax,label='Count',shrink=0.5)
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_ylabel('Modeled',fontsize=fontsize)
    ax.set_xlabel('Observed',fontsize=fontsize)
    plt.tight_layout()
    return ps  

def bySeason_hist2d(ax,fig,seasons,obsvar,modvar,lims,season_titles=['Jan-Mar','Apr','May-Aug','Sep-Dec']):
    for axj in ax:
        for axi in axj:
            axi.plot(lims,lims,'k-')
            axi.set_xlim(lims)
            axi.set_ylim(lims)
            axi.set_aspect(1)
            axi.set_xlabel('Obs')
            axi.set_ylabel('Model')
    jp=hist2d(ax[0][0],fig,seasons[0],obsvar,modvar,lims)
    ax[0][0].set_title(season_titles[0])
    jp=hist2d(ax[0][1],fig,seasons[1],obsvar,modvar,lims)
    ax[0][1].set_title(season_titles[1])
    jp=hist2d(ax[1][0],fig,seasons[2],obsvar,modvar,lims)
    ax[1][0].set_title(season_titles[2])
    jp=hist2d(ax[1][1],fig,seasons[3],obsvar,modvar,lims)
    ax[1][1].set_title(season_titles[3])
    return 

def byRegion_hist2d(datreg,regions,obsvar,modvar,lims):
    fig,ax=plt.subplots(math.ceil(len(regions)/2),2,figsize=(16,26))
    new_reg = [regions[i:i+2] for i in range(0, len(regions), 2)]
    for ri,axi in zip(new_reg,ax):
        for rj,axj in zip(ri,axi):
            axj.set_xlim(lims)
            axj.set_ylim(lims)
            axj.set_aspect(1)
            axj.set_xlabel('Obs')
            axj.set_ylabel('Model')    
            hist2d(axj,fig,datreg[rj],obsvar,modvar,lims)
            axj.set_title(str(rj))
    return ax

def ErrErr(df,fig,ax,obsvar1,modvar1,obsvar2,modvar2,lims1,lims2):
    m=ax.scatter(df[modvar1]-df[obsvar1],df[modvar2]-df[obsvar2],c=df['Z'],s=1,cmap='gnuplot')
    cb=fig.colorbar(m,ax=ax,label='Depth (m)')
    ax.set_xlim(lims1)
    ax.set_ylim(lims2)
    ax.set_aspect((lims1[1]-lims1[0])/(lims2[1]-lims2[0]))
    return m,cb

def multi_depreg_graph(df,datyear,years,obsvar,modvar,phyvar_name,lims,figsize):
    if type(years) == int:
        fig,ax=plt.subplots(1,2,figsize=figsize)
        ps,l=byDepth(ax[0],obsvar,modvar,lims,byyear=True,year=years)
        ax[0].set_title(f'{phyvar_name} (g kg$^-1$) By Depth for {years}')
        ps,l=byRegion(ax[1],obsvar,modvar,lims,year=years)
        ax[1].set_title(f'{phyvar_name} (g kg$^-1$) By Region for {years}');
    elif type(years) == list:
        fig,ax=plt.subplots(len(years),2,figsize=figsize)
        for d,Y in enumerate(years):
            ps,l=byDepth(ax[d][0],obsvar,modvar,lims,byyear=True,year=Y)
            ax[d][0].set_title(f'{phyvar_name} (g kg$^-1$) By Depth for {Y}')
            ps,l=byRegion(ax[d][1],obsvar,modvar,lims,year=Y)
            ax[d][1].set_title(f'{phyvar_name} (g kg$^-1$) By Region for {Y}');
    # put a raise exception thing into this. 
    plt.tight_layout()
    return ax
        
# This has been altered but it has not been finished or tested !!!!!!!!!!!!!!!
def multi_enverr_graph(df,datyear,years,obsvar,modvar,envvar,envvar_name,figsize,units='($\mu$M)'):
    if type(years) == int:
        fig,ax=plt.subplots(1,len(obsvar),figsize=figsize)
        for a,(o,m) in enumerate(zip(obsvar,modvar)):
            ps=ax[a].scatter(datyear[years][envvar],datyear[years][m]-datyear[years][o],c=datyear[years]['Z'],s=1,cmap='gnuplot') 
            cb=fig.colorbar(ps,ax=ax[a],label='Depth (m)')
            ax[a].set_xlabel(f'Obs {envvar_name}',fontsize=12)
            ax[a].set_ylabel(f'{o} Error {units}',fontsize=12)
            ax[a].set_title(str(years))
    elif type(years) == list:
        fig,ax=plt.subplots(len(years),len(obsvar),figsize=figsize)
        for d,Y in zip(range(len(years)),years):
            for a,(o,m) in enumerate(zip(obsvar,modvar)):
                ps=ax[d][a].scatter(datyear[Y][envvar],datyear[Y][m]-datyear[Y][o],c=datyear[Y]['Z'],s=1,cmap='gnuplot') 
                cb=fig.colorbar(ps,ax=ax[d][a],label='Depth (m)')
                ax[d][a].set_xlabel(f'Obs {envvar_name}',fontsize=12)
                ax[d][a].set_ylabel(f'{o} Error {units}',fontsize=12)
                ax[d][a].set_title(str(Y))
    else:
        raise(TypeError('years must be of type list or int'))
    plt.tight_layout()
    return ax
        
def multi_station_graph(df,datstat,obsvar,modvar,regions,lims,figsize=(14,40),units='($\mu$M)'):
    """ A function that creates a series of scatter plots and maps for each region
        And shows the stations within each region colored on the graph and map. 
    
    :arg df: A dataframe which data will be drawn from
    :type :pandas dataframe
    
    :arg datstat: A dictionary which contains data on each seperate station
    :type :dict
    
    :arg obsvar,modvar: The name of the observed and model variables you wish to compare to each other.
    :type :string
    
    :are regions: The names of all of the basins you wish to look at 
    :type : list of strings
    
    :arg lims: A pair of values that will decide the range of the graph. Should always
                    should always be larger than the maximum value of the variable.
    :type : tuple
    
    :arg down: A number which should be equal to the number of regions you are looking at
    :type : integer
    
    :arg figsize: a pair of values that decide the size of the entire figure
    :type : tuple
    """
    fig, ax = plt.subplots(len(regions),2,figsize = figsize)
    for d,r in zip(range(len(regions)),regions):
        ps=byStation(ax[d][0],df,datstat,r,obsvar,modvar,lims)
        ax[d][0].set_title(f'{obsvar} {units} in {r} by Station');

        with nc.Dataset('/data/vdo/MEOPAR/NEMO-forcing/grid/bathymetry_201702.nc') as grid:
            viz_tools.plot_coastline(ax[d][1], grid, coords = 'map',isobath=.1)

        for ind, istation in enumerate(df[df['Basin'] == r].Station.unique()):
            ax[d][1].plot(datstat[istation]['Lon'], datstat[istation]['Lat'],'.',
                color = colors[ind], label=istation)
        ax[d][1].set_ylim(47, 49)
        ax[d][1].legend(bbox_to_anchor=[1,.6,0,0])
        ax[d][1].set_xlim(-124, -122);
        ax[d][1].set_title(f'Observation Locations for {r}'); 
    return ax

def logt(x):
    return np.log10(x+.001)
    
def multi_meanerr_graph(df,datyear,years,obsvar,modvar,down,figsize,units='($\mu$M)'):
    fig,ax=plt.subplots(down,1,figsize=figsize)
    for d,Y in zip(range(down),years):
            meanerr=datyear[Y].groupby(by='dtUTC').mean()
            m=ax[d].plot(datyear[Y]['dtUTC'].unique(),meanerr[modvar]-meanerr[obsvar],'c-') 
            ax[d].set_xlabel(f'Date',fontsize=20)
            ax[d].set_ylabel(f'{obsvar} Error {units}',fontsize=20)
            ax[d].set_title(str(Y), fontsize=22)
            yearsFmt = mdates.DateFormatter('%d %b')
            ax[d].xaxis.set_major_formatter(yearsFmt)
    plt.tight_layout()
    return ax
    
def multi_timerror_graph(df,datyear,years,obsvar,modvar,figsize,units='($\mu$M)'):
    if type(years) == int:
        fig,ax=plt.subplots(1,1,figsize=figsize)
        m=ax.scatter(datyear[years]['dtUTC'],datyear[years][modvar]-datyear[years][obsvar],s=8,cmap='gnuplot') 
        ax.set_xlabel(f'Date',fontsize=20)
        ax.set_ylabel(f'{obsvar} Error {units}',fontsize=20)
        ax.set_title(str(years), fontsize=22)
        yearsFmt = mdates.DateFormatter('%d %b')
        ax.xaxis.set_major_formatter(yearsFmt)
    elif type(years) == list:
        fig,ax=plt.subplots(len(years),1,figsize=figsize)
        for d,Y in zip(range(len(years)),years):
            m=ax[d].scatter(datyear[Y]['dtUTC'],datyear[Y][modvar]-datyear[Y][obsvar],s=8,cmap='gnuplot') 
            ax[d].set_xlabel(f'Date',fontsize=20)
            ax[d].set_ylabel(f'{obsvar} Error {units}',fontsize=20)
            ax[d].set_title(str(Y), fontsize=22)
            yearsFmt = mdates.DateFormatter('%d %b')
            ax[d].xaxis.set_major_formatter(yearsFmt)
    plt.tight_layout()
    return ax
    
def multi_timese_graph(df,years,obsvar,modvar,figsize,units='($\mu$M)'):
    if type(years) == int:
        fig,ax=plt.subplots(1,1,figsize=figsize)
        ps=tsertser_graph(ax,df,obsvar,modvar,dt.datetime(years,1,1),dt.datetime(years,12,31),'Z',(15,22),'z','m')
        ax.set_xlabel(f'Date',fontsize=20)
        ax.set_ylabel(f'{obsvar} {units}',fontsize=20)
        ax.set_title(str(years), fontsize=22)
        yearsFmt = mdates.DateFormatter('%d %b')
        ax.xaxis.set_major_formatter(yearsFmt)
        legend = plt.legend(handles=ps,bbox_to_anchor=[1,.6,0,0])
        plt.gca().add_artist(legend)
        return ax
    elif type(years) == list:  
        fig, ax=plt.subplots(len(years),1,figsize=figsize)
        for d,Y in zip(range(len(years)),years):
            ps=tsertser_graph(ax[d],df,obsvar,modvar,dt.datetime(Y,1,1),dt.datetime(Y,12,31),'Z',(15,22),'z','m')
            ax[d].set_xlabel(f'Date',fontsize=20)
            ax[d].set_ylabel(f'{obsvar} {units}',fontsize=20)
            ax[d].set_title(str(Y), fontsize=22)
            yearsFmt = mdates.DateFormatter('%d %b')
            ax[d].xaxis.set_major_formatter(yearsFmt)
            legend = plt.legend(handles=ps,bbox_to_anchor=[1,.6,0,0])
            plt.gca().add_artist(legend)
            return ax
    else:
        raise(TypeError('years must be of type list or int'))
    plt.tight_layout()

    
# Why and how is the legend part of this broken???
def all_years(data,obsvar,modvar,title,units='($\mu$M)'):
    start_date=dt.datetime(2007,1,1)
    end_date=dt.datetime(2019,12,31)
    fig,ax=plt.subplots(1,1,figsize=(19,8))
    ps=tsertser_graph(ax,data,obsvar,modvar,start_date,end_date)
    ax.legend(handles=ps)
    ax.set_ylabel(f'{obsvar} {units}')
    ax.set_xlabel('Date')
    ax.set_title(title)
    plt.setp(ax.get_xticklabels(), rotation=30, horizontalalignment='right')
    M = 15
    xticks = mpl.ticker.MaxNLocator(M)
    ax.xaxis.set_major_locator(xticks)
    return ax
    
#ready for evaltools
def tsertser_graph(ax,df,obsvar,modvar,start_date,end_date,sepvar='',sepvals=([]),lname='',sepunits='',
                  ocols=('blue','darkviolet','teal','green','deepskyblue'),
                  mcols=('fuchsia','firebrick','orange','darkgoldenrod','maroon'),labels=''):
    """ Creates timeseries by adding scatter plot to axes ax with df['dtUTC'] on x-axis, 
        df[obsvar] and df[modvar] on y axis, and colors taken from a listas determined from 
        df[sepvar] and a list of bin edges, sepvals
    """
    if len(lname)==0:
        lname=sepvar
    ps=list()
    if len(sepvals)==0:
        obs0=et._deframe(df.loc[(df['dtUTC'] >= start_date)&(df['dtUTC']<= end_date),[obsvar]])
        mod0=et._deframe(df.loc[(df['dtUTC'] >= start_date)&(df['dtUTC']<= end_date),[modvar]])
        time0=et._deframe(df.loc[(df['dtUTC'] >= start_date)&(df['dtUTC']<= end_date),['dtUTC']])
        p0,=ax.plot(time0,obs0,'.',color=ocols[0],label=f'Observed {lname}')
        ps.append(p0)
        p0,=ax.plot(time0,mod0,'.',color=mcols[0],label=f'Modeled {lname}')
        ps.append(p0)
    else:
        obs0=et._deframe(df.loc[(df[obsvar]==df[obsvar])&(df[modvar]==df[modvar])&(df[sepvar]==df[sepvar])&(df['dtUTC'] >= start_date)&(df['dtUTC']<= end_date),[obsvar]])
        mod0=et._deframe(df.loc[(df[obsvar]==df[obsvar])&(df[modvar]==df[modvar])&(df[sepvar]==df[sepvar])&(df['dtUTC'] >= start_date)&(df['dtUTC']<= end_date),[modvar]])
        time0=et._deframe(df.loc[(df[obsvar]==df[obsvar])&(df[modvar]==df[modvar])&(df[sepvar]==df[sepvar])&(df['dtUTC'] >= start_date)&(df['dtUTC']<= end_date),['dtUTC']])
        sep0=et._deframe(df.loc[(df[obsvar]==df[obsvar])&(df[modvar]==df[modvar])&(df[sepvar]==df[sepvar])&(df['dtUTC'] >= start_date)&(df['dtUTC']<= end_date),[sepvar]])
        sepvals=np.sort(sepvals)
                # less than min case:
        ii=0
        iii=sep0<sepvals[ii]
        if np.sum(iii)>0:
            #ll=u'{} < {} {}'.format(lname,sepvals[ii],sepunits).strip()
            if len(labels)>0:
                ll=labels[0]
            else:
                ll=u'{} $<$ {} {}'.format(lname,sepvals[ii],sepunits).strip()
            p0,=ax.plot(time0[iii],obs0[iii],'.',color=ocols[ii],label=f'Observed {ll}')
            ps.append(p0)
            p0,=ax.plot(time0[iii],mod0[iii],'.',color=mcols[ii],label=f'Modeled {ll}')
            ps.append(p0)
        # between min and max:
        for ii in range(1,len(sepvals)):
            iii=np.logical_and(sep0<sepvals[ii],sep0>=sepvals[ii-1])
            if np.sum(iii)>0:
                #ll=u'{} {} \u2264 {} < {} {}'.format(sepvals[ii-1],sepunits,lname,sepvals[ii],sepunits).strip()
                if len(labels)>0:
                    ll=labels[ii]
                else:
                    ll=u'{} {} $\leq$ {} $<$ {} {}'.format(sepvals[ii-1],sepunits,lname,sepvals[ii],sepunits).strip()
                p0,=ax.plot(time0[iii],obs0[iii],'.',color=ocols[ii],label=f'Observed {ll}')
                ps.append(p0)
                p0,=ax.plot(time0[iii],mod0[iii],'.',color=mcols[ii],label=f'Modeled {ll}')
                ps.append(p0)
        # greater than max:
        iii=sep0>=sepvals[ii]
        if np.sum(iii)>0:
            #ll=u'{} \u2265 {} {}'.format(lname,sepvals[ii],sepunits).strip()
            if len(labels)>0:
                ll=labels[ii+1]
            else:
                ll=u'{} $\geq$ {} {}'.format(lname,sepvals[ii],sepunits).strip()
            p0,=ax.plot(time0[iii],obs0[iii],'.',color=ocols[ii+1],label=f'Observed {ll}')
            ps.append(p0)
            p0,=ax.plot(time0[iii],mod0[iii],'.',color=mcols[ii+1],label=f'Modeled {ll}')
            ps.append(p0)
    yearsFmt = mdates.DateFormatter('%d %b %y')
    ax.xaxis.set_major_formatter(yearsFmt)
    return ps

def ts_trendline(ax,df,obsvar,modvar,start_date,end_date,sepvar='',sepvals=([]),lname='',sepunits='',
                  ocols=('blue','darkviolet','teal','green','deepskyblue'),
                  mcols=('fuchsia','firebrick','orange','darkgoldenrod','maroon'),labels=''):
    """ Plots trendlines by adding line plots to axes ax with df['dtUTC'] on x-axis, 
        df[obsvar] and df[modvar] on y axis, and colors taken from a listas determined from 
        df[sepvar] and a list of bin edges, sepvals. Trendlines are calculated by fitting a 
        4 dimensional polynomial to the data. 
    """
    if len(lname)==0:
        lname=sepvar
    ps=list()
    df=df.sort_values(by='dtUTC')
    df=df.dropna(axis=0,subset=[obsvar,modvar,'dtUTC'])
    if len(sepvals)==0:
        yd=list()
        timepy=df.loc[(df['dtUTC'] >= start_date)&(df['dtUTC']<= end_date)].dtUTC.dt.to_pydatetime()
        obs0=et._deframe(df.loc[(df['dtUTC'] >= start_date)&(df['dtUTC']<= end_date),[obsvar]])
        mod0=et._deframe(df.loc[(df['dtUTC'] >= start_date)&(df['dtUTC']<= end_date),[modvar]])
        time0=et._deframe(timepy)
        for i in time0:
            yd.append((i - dt.datetime(i.year, 1, 1)).days + 1)
        coefso = poly.polyfit(yd,obs0,4)
        ffito = poly.polyval(yd, coefso)
        coefsm = poly.polyfit(yd,mod0,4)
        ffitm = poly.polyval(yd, coefsm)
        p0,=ax.plot(time0, ffito, color=ocols[0], label=f'Observed {lname}',alpha=0.7, linestyle='dashed')
        ps.append(p0)
        p0,=ax.plot(time0, ffitm, color=mcols[0], label=f'Modeled {lname}',alpha=0.7, linestyle='dashed')
        ps.append(p0)
    else:
        timepy=df.loc[(df[obsvar]==df[obsvar])&(df[modvar]==df[modvar])&(df[sepvar]==df[sepvar])&(df['dtUTC'] >= start_date)&(df['dtUTC']<= end_date)].dtUTC.dt.to_pydatetime()
        obs0=et._deframe(df.loc[(df[obsvar]==df[obsvar])&(df[modvar]==df[modvar])&(df[sepvar]==df[sepvar])&(df['dtUTC'] >= start_date)&(df['dtUTC']<= end_date),[obsvar]])
        mod0=et._deframe(df.loc[(df[obsvar]==df[obsvar])&(df[modvar]==df[modvar])&(df[sepvar]==df[sepvar])&(df['dtUTC'] >= start_date)&(df['dtUTC']<= end_date),[modvar]])
        time0=et._deframe(timepy)
        sep0=et._deframe(df.loc[(df[obsvar]==df[obsvar])&(df[modvar]==df[modvar])&(df[sepvar]==df[sepvar])&(df['dtUTC'] >= start_date)&(df['dtUTC']<= end_date),[sepvar]])
        sepvals=np.sort(sepvals)
                # less than min case:
        yd=list()
        ii=0
        iii=sep0<sepvals[ii]
        if np.sum(iii)>0:
            #ll=u'{} < {} {}'.format(lname,sepvals[ii],sepunits).strip()
            if len(labels)>0:
                ll=labels[0]
            else:
                ll=u'{} $<$ {} {}'.format(lname,sepvals[ii],sepunits).strip()
            for i in time0[iii]:
                yd.append((i - dt.datetime(i.year, 1, 1)).days + 1)
            coefso = poly.polyfit(yd,obs0[iii],4)
            ffito = poly.polyval(yd, coefso)
            coefsm = poly.polyfit(yd,mod0[iii],4)
            ffitm = poly.polyval(yd, coefsm)
            p0,=ax.plot(time0[iii], ffito, color=ocols[ii], label=f'Observed {ll}',alpha=0.4, linestyle='dashed')
            ps.append(p0)
            p0,=ax.plot(time0[iii], ffitm, color=mcols[ii], label=f'Modeled {ll}',alpha=0.4, linestyle='dashed')
            ps.append(p0)
        # between min and max:
        yd=list()
        for ii in range(1,len(sepvals)):
            iii=np.logical_and(sep0<sepvals[ii],sep0>=sepvals[ii-1])
            if np.sum(iii)>0:
                #ll=u'{} {} \u2264 {} < {} {}'.format(sepvals[ii-1],sepunits,lname,sepvals[ii],sepunits).strip()
                if len(labels)>0:
                    ll=labels[ii]
                else:
                    ll=u'{} {} $\leq$ {} $<$ {} {}'.format(sepvals[ii-1],sepunits,lname,sepvals[ii],sepunits).strip()
                for i in time0[iii]:
                    yd.append((i - dt.datetime(i.year, 1, 1)).days + 1)
                coefso = poly.polyfit(yd,obs0[iii],4)
                ffito = poly.polyval(yd, coefso)
                coefsm = poly.polyfit(yd,mod0[iii],4)
                ffitm = poly.polyval(yd, coefsm)
                p0,=ax.plot(time0[iii], ffito, color=ocols[ii], label=f'Observed {ll}',alpha=0.4, linestyle='dashed')
                ps.append(p0)
                p0,=ax.plot(time0[iii], ffitm, color=mcols[ii], label=f'Modeled {ll}',alpha=0.4, linestyle='dashed')
                ps.append(p0)
        # greater than max:
        yd=list()
        iii=sep0>=sepvals[ii]
        if np.sum(iii)>0:
            #ll=u'{} \u2265 {} {}'.format(lname,sepvals[ii],sepunits).strip()
            if len(labels)>0:
                ll=labels[ii+1]
            else:
                ll=u'{} $\geq$ {} {}'.format(lname,sepvals[ii],sepunits).strip()
            for i in time0[iii]:
                yd.append((i - dt.datetime(i.year, 1, 1)).days + 1)
            coefso = poly.polyfit(yd,obs0[iii],4)
            ffito = poly.polyval(yd, coefso)
            coefsm = poly.polyfit(yd,mod0[iii],4)
            ffitm = poly.polyval(yd, coefsm)
            p0,=ax.plot(time0[iii], ffito, color=ocols[ii+1], label=f'Observed {ll}',alpha=0.4, linestyle='dashed')
            ps.append(p0)
            p0,=ax.plot(time0[iii], ffitm, color=mcols[ii+1], label=f'Modeled {ll}',alpha=0.4, linestyle='dashed')
            ps.append(p0)
    yearsFmt = mdates.DateFormatter('%d %b %y')
    ax.xaxis.set_major_formatter(yearsFmt)
    return ps

def TsByRegion(datreg,regions,obsvar,modvar,year,loc='lower left',units='($\mu$M)',trendline=False):
    fig,ax=plt.subplots(math.ceil(len(regions)/2),2,figsize=(13,13))
    new_reg = [regions[i:i+2] for i in range(0, len(regions), 2)]
    for ri,axi in zip(new_reg,ax):
        for rj,axj in zip(ri,axi):
            ps=tsertser_graph(axj,datreg[rj],obsvar,modvar,dt.datetime(year,1,1),dt.datetime(year,12,31))
            axj.legend(handles=ps,prop={'size': 10},loc=loc)
            axj.set_xlabel(f'Date',fontsize=13)
            axj.set_ylabel(f'{obsvar} {units}',fontsize=13)
            axj.set_title(f'Time series for {rj}', fontsize=13)
            yearsFmt = mdates.DateFormatter('%d %b')
            axj.xaxis.set_major_formatter(yearsFmt)
            for tick in axj.xaxis.get_major_ticks():
                tick.label.set_fontsize(13)
            for tick in axj.yaxis.get_major_ticks():
                tick.label.set_fontsize(13)
            plt.tight_layout()
            plt.setp(axj.get_xticklabels(), rotation=30, horizontalalignment='right')
            if trendline == True:
                ts_trendline(axj,datreg[rj],obsvar,modvar,dt.datetime(year,1,1),dt.datetime(year,12,31))