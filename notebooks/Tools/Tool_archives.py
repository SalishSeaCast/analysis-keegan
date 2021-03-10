def ts_gsmooth_line(ax,df,obsvar,modvar,start_date,end_date,L=50,region='',station='',sepvar='',sepvals=([]),lname='',sepunits='', ocols=('blue','darkviolet','teal','green','deepskyblue'),
                          mcols=('fuchsia','firebrick','orange','darkgoldenrod','maroon'),labels=''):
    """ Plots the daily average value of df[obsvar] and df[modvar] against df[YD]. 
    """
    if len(lname)==0:
        lname=sepvar
    ps=list()
    df=df.dropna(axis=0,subset=['dtUTC',obsvar,modvar])
    if len(region) > 0:
        df=df[df['Basin'] == region]
    if len(station) > 0:
        df=df[df['Station'] == station]
    if len(sepvals)==0:
        obs0=et._deframe(df.loc[(df['dtUTC'] >= start_date)&(df['dtUTC']<= end_date),[obsvar]])
        mod0=et._deframe(df.loc[(df['dtUTC'] >= start_date)&(df['dtUTC']<= end_date),[modvar]])
        time0=et._deframe(df.loc[(df['dtUTC'] >= start_date)&(df['dtUTC']<= end_date),['YD']])
        ox0,ox2=gsmooth(time0,obs0,L)
        ps0,=ax.plot(ox0,ox2,'-',color=ocols[0], label=f'Observed {lname}',alpha=0.7, linestyle='dashed')
        ps.append(ps0)
        mx0,mx2=gsmooth(time0,mod0,L)
        ps0,=ax.plot(mx0,mx2,'-',color=mcols[0], label=f'Modeled {lname}',alpha=0.7, linestyle='dashed')
        ps.append(ps0)
    else:
        obs0=et._deframe(df.loc[(df[obsvar]==df[obsvar])&(df[modvar]==df[modvar])&(df[sepvar]==df[sepvar])&(df['dtUTC'] >= start_date)&(df['dtUTC']<= end_date),[obsvar]])
        mod0=et._deframe(df.loc[(df[obsvar]==df[obsvar])&(df[modvar]==df[modvar])&(df[sepvar]==df[sepvar])&(df['dtUTC'] >= start_date)&(df['dtUTC']<= end_date),[modvar]])
        time0=et._deframe(df.loc[(df[obsvar]==df[obsvar])&(df[modvar]==df[modvar])&(df[sepvar]==df[sepvar])&(df['dtUTC'] >= start_date)&(df['dtUTC']<= end_date),['YD']])
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
            ox0,ox2=gsmooth(time0[iii],obs0[iii],L)
            ps0,=ax.plot(ox0,ox2,'-',color=ocols[ii], label=f'Observed {ll}',alpha=0.7, linestyle='dashed')
            ps.append(ps0)
            mx0,mx2=gsmooth(time0[iii],mod0[iii],L)
            ps0,=ax.plot(mx0,mx2,'-',color=mcols[ii], label=f'Modeled {ll}',alpha=0.7, linestyle='dashed')
            ps.append(ps0)
        # between min and max:
        for ii in range(1,len(sepvals)):
            iii=np.logical_and(sep0<sepvals[ii],sep0>=sepvals[ii-1])
            if np.sum(iii)>0:
                #ll=u'{} {} \u2264 {} < {} {}'.format(sepvals[ii-1],sepunits,lname,sepvals[ii],sepunits).strip()
                if len(labels)>0:
                    ll=labels[ii]
                else:
                    ll=u'{} {} $\leq$ {} $<$ {} {}'.format(sepvals[ii-1],sepunits,lname,sepvals[ii],sepunits).strip()
                ox0,ox2=gsmooth(time0[iii],obs0[iii],L)
                ps0,=ax.plot(ox0,ox2,'-',color=ocols[ii], label=f'Observed {ll}',alpha=0.7, linestyle='dashed')
                ps.append(ps0)
                mx0,mx2=gsmooth(time0[iii],mod0[iii],L)
                ps0,=ax.plot(mx0,mx2,'-',color=mcols[ii], label=f'Modeled {ll}',alpha=0.7, linestyle='dashed')
                ps.append(ps0)
        # greater than max:
        iii=sep0>=sepvals[ii]
        if np.sum(iii)>0:
            #ll=u'{} \u2265 {} {}'.format(lname,sepvals[ii],sepunits).strip()
            if len(labels)>0:
                ll=labels[ii+1]
            else:
                ll=u'{} $\geq$ {} {}'.format(lname,sepvals[ii],sepunits).strip()
            ox0,ox2=gsmooth(time0[iii],obs0[iii],L)
            ps0,=ax.plot(ox0,ox2,'-',color=ocols[ii+1], label=f'Observed {ll}',alpha=0.7, linestyle='dashed')
            ps.append(ps0)
            mx0,mx2=gsmooth(time0[iii],mod0[iii],L)
            ps0,=ax.plot(mx0,mx2,'-',color=mcols[ii+1], label=f'Modeled {ll}',alpha=0.7, linestyle='dashed')
            ps.append(ps0)
    yearsFmt = mdates.DateFormatter('%d %b %y')
    ax.xaxis.set_major_formatter(yearsFmt)
    return ps

def gsmooth(YD,val,L,res=1):
# DD is input date in decimal days (ususally since 1900,1,1)
# val is values to be smoothed
# L is length scale of gaussian kernel- larger widens the window
# res can be changed to give a different resolution of output
    allt=np.arange(0,366+res,res)
    fil=np.empty(np.size(allt)) #ohhh this is cool. It automatically creates an empty array of the size you need.
    s=L/2.355
    for ind,t in enumerate(allt):
        diff=[min(abs(x-t),abs(x-t+365), abs(x-t-365)) for x in YD]
        weight=[np.exp(-.5*x**2/s**2) if x <= 3*L else 0.0 for x in diff]
        fil[ind]=np.sum(weight*val)/np.sum(weight)
    return allt,fil