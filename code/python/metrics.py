import pandas as pd, numpy as np
D=pd.read_csv('data/P3_dengue_admin1_month_climate.csv'); D=D[D.iso3!='AUS']
A=D[D.year.between(2010,2022)].copy()
obs=A.groupby('shapeID').dengue_cases.apply(lambda s:s.notna().mean()); inc=obs[obs>=.8].index
A=A[A.shapeID.isin(inc)].copy()
def circ_peak(g,col):
    m=g.groupby('month')[col].mean(); w=m.values/np.nansum(m.values); ang=2*np.pi*(m.index.values-1)/12
    z=np.nansum(w*np.exp(1j*ang)); return (np.angle(z)%(2*np.pi))/(2*np.pi)*12+1, abs(z)
R=[]
for sid,g in A.groupby('shapeID'):
    # case share per year, then circular mean across months
    g=g.copy(); g['sh']=g.dengue_cases/g.groupby('year').dengue_cases.transform('sum')
    pc,rc=circ_peak(g,'sh'); pr,rr=circ_peak(g,'power_precip_mm')
    lag=(pc-pr)%12; lag=lag-12 if lag>6 else lag
    g['ly']=np.log1p(g.dengue_cases); g['ly_d']=g.ly-g.groupby('month').ly.transform('mean')
    g=g.sort_values(['year','month']); oni3=g.oni_anomaly.shift(3)
    r_oni=g.ly_d.corr(oni3)
    R.append(dict(shapeID=sid,iso3=g.iso3.iloc[0],cases_per_year=g.dengue_cases.sum()/13,peak_case=pc,season_strength=rc,peak_rain=pr,lag_rain_to_case=lag,r_oni_lag3=r_oni,tmean=g.power_tmean_c.mean()))
R=pd.DataFrame(R); R.to_csv('data/province_metrics.csv',index=False)
print(R.describe().round(2).T[['mean','min','50%','max']])
print(R.groupby('iso3')[['lag_rain_to_case','r_oni_lag3','season_strength']].median().round(2))
