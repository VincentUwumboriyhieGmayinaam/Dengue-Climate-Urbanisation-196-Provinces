import pandas as pd, numpy as np, matplotlib as mpl, matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
mpl.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.edgecolor':'#c3c2b7','axes.labelcolor':'#52514e',
 'xtick.color':'#52514e','ytick.color':'#52514e','axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':0.6})
INK,SEC,MUT,GRID='#0b0b0b','#52514e','#898781','#e1e0d9'
S1,S2,S3='#2a78d6','#eb6834','#1baf7a'
D=pd.read_csv('data/P3_dengue_admin1_month_climate.csv')
D=D[D.year.between(2010,2022)&(D.iso3!='AUS')]
obs=D.groupby('shapeID').dengue_cases.apply(lambda s:s.notna().mean()); A=D[D.shapeID.isin(obs[obs>=.8].index)]
NM={'BRA':'Brazil','COL':'Colombia','IDN':'Indonesia','NIC':'Nicaragua','PER':'Peru','THA':'Thailand'}
order=['BRA','COL','PER','NIC','THA','IDN']
fig=plt.figure(figsize=(7.2,9.4))
gs=fig.add_gridspec(3,1,height_ratios=[2.5,2.2,1.7],hspace=.55,top=.875,bottom=.06)
# ---------- A: seasonal profiles, indexed 0-1
gA=gs[0].subgridspec(2,3,hspace=.7,wspace=.18)
M=['J','F','M','A','M','J','J','A','S','O','N','D']
for k,c in enumerate(order):
    ax=fig.add_subplot(gA[k//3,k%3]); X=A[A.iso3==c]
    cm=X.groupby(['year','month']).dengue_cases.sum().reset_index()
    cm['sh']=cm.dengue_cases/cm.groupby('year').dengue_cases.transform('sum')
    cs=cm.groupby('month').sh.median()
    t=X.groupby('month').power_tmean_c.mean(); r=X.groupby('month').power_precip_mm.mean()
    idx=lambda s:(s-s.min())/(s.max()-s.min())
    for s,col,lab,ls in [(idx(r),S3,'Rainfall','-'),(idx(t),S2,'Temperature','-'),(idx(cs),S1,'Dengue cases','-')]:
        ax.plot(range(1,13),s.values,color=col,lw=2 if lab=='Dengue cases' else 1.6,ls=ls,solid_capstyle='round',label=lab,zorder=3 if lab=='Dengue cases' else 2)
        pk=s.idxmax(); ax.plot(pk,1,'o',ms=4.5,color=col,mec='#fcfcfb',mew=1,zorder=4)
    ax.set_xticks(range(1,13)); ax.set_xticklabels(M,fontsize=6.5); ax.set_ylim(-.05,1.12); ax.set_yticks([0,.5,1])
    ax.set_yticklabels(['min','','max'] if k%3==0 else [],fontsize=6.5); ax.tick_params(length=0)
    ax.grid(axis='y',color=GRID,lw=.5); ax.set_axisbelow(True)
    lagm=(cs.idxmax()-r.idxmax())%12
    ax.set_title(f'{NM[c]}',fontsize=8.5,color=INK,loc='left',fontweight='bold',pad=11)
    ax.text(1,1.02 if k else 1.02,'',transform=ax.transAxes)
    ax.text(0,1.005,f'{t.min():.1f}–{t.max():.1f} °C · {r.min():.0f}–{r.max():.0f} mm'.replace('.','·'),transform=ax.transAxes,ha='left',va='bottom',fontsize=6,color=SEC)
    if k==0: hA=ax.get_legend_handles_labels()
fig.legend(hA[0][::-1],hA[1][::-1],loc='upper left',bbox_to_anchor=(.08,.952),ncol=3,frameon=False,fontsize=7.5,handlelength=1.8)
fig.text(.06,.96,'A',fontsize=11,fontweight='bold',color=INK)
fig.text(.09,.962,'Seasonal profiles: each series scaled to its own monthly minimum–maximum (dots mark the peak month)',fontsize=7.5,color=SEC)
# ---------- B: epidemic calendar + ONI
gB=gs[1].subgridspec(2,1,height_ratios=[.55,3],hspace=.08)
oni=A.groupby(['year','month']).oni_anomaly.first().reset_index(); oni['t']=np.arange(len(oni))
ax0=fig.add_subplot(gB[0]); cl=np.where(oni.oni_anomaly>=0,'#e34948','#2a78d6')
ax0.bar(oni.t,oni.oni_anomaly,color=cl,width=1,lw=0); ax0.axhline(0,color='#c3c2b7',lw=.6)
for h in (.5,-.5): ax0.axhline(h,color=GRID,lw=.5,ls=(0,(2,2)))
ax0.set_xlim(-.5,len(oni)-.5); ax0.set_xticks([]); ax0.tick_params(labelbottom=False); ax0.set_yticks([-1.5,0,1.5]); ax0.tick_params(length=0,labelsize=6)
ax0.spines['bottom'].set_visible(False); ax0.set_ylabel('ONI',fontsize=6.5,rotation=0,ha='right',va='center')

ax1=fig.add_subplot(gB[1])
ax1.set_xlim(-.5,len(oni)-.5)
cmap=LinearSegmentedColormap.from_list('d',['#1c5cab','#86b6ef','#f0efec','#f2a48c','#e34948','#8f1d1c'])
Z=[];INC=[]
for c in order:
    X=A[A.iso3==c]; g=X.groupby(['year','month'])
    s_=g.dengue_cases.mean(); inc=g.dengue_cases.apply(lambda v:v.isna().all())
    df=pd.DataFrame({'c':s_,'inc':inc}).reindex(pd.MultiIndex.from_frame(oni[['year','month']]))
    med=df.groupby(level='month').c.transform('median')
    Z.append(np.log2((df.c+1)/(med+1)).values); INC.append(df.inc.fillna(True).values)
Z=np.array(Z,dtype=float)
ax1.set_facecolor('#fcfcfb')
im=ax1.imshow(Z,aspect='auto',cmap=cmap,vmin=-3,vmax=3,interpolation='nearest',extent=(-.5,len(oni)-.5,len(order)-.5,-.5))
from matplotlib.patches import Rectangle
for i,row in enumerate(INC):
    for j,v in enumerate(row):
        if v: ax1.add_patch(Rectangle((j-.5,i-.5),1,1,fill=False,hatch='////',ec='#898781',lw=0))
ax1.set_yticks(range(len(order))); ax1.set_yticklabels([NM[c] for c in order],fontsize=7); ax1.tick_params(length=0)
for i in range(1,len(order)): ax1.axhline(i-.5,color='#fcfcfb',lw=2)
yrs=oni.groupby('year').t.min(); ax1.set_xticks(yrs.values+5.5); ax1.set_xticklabels(yrs.index,fontsize=6.5)
for v in yrs.values[1:]: ax1.axvline(v-.5,color='#fcfcfb',lw=.8)
for s in ax1.spines.values(): s.set_visible(False)
p=ax1.get_position(); cax=fig.add_axes([p.x1-.2,p.y0-.045,.2,.007]); cb=fig.colorbar(im,cax=cax,orientation='horizontal',ticks=[-3,-1,0,1,3])
cb.ax.set_xticklabels(['⅛×','½×','usual','2×','8×'],fontsize=6); cb.outline.set_visible(False); cb.ax.text(-.04,.5,'Cases per reporting province vs usual level for that calendar month   (hatched = not reported)',transform=cb.ax.transAxes,ha='right',va='center',fontsize=6.3,color='#52514e'); cb.ax.tick_params(length=0)
p=ax0.get_position(); fig.text(.06,p.y1+.04,'B',fontsize=11,fontweight='bold',color=INK)
fig.text(.09,p.y1+.032,'Epidemic calendar: mean cases per reporting province relative to the median for the same calendar month (seasonality removed),\nwith the Oceanic Niño Index (ONI, °C: red = El Niño side, blue = La Niña side; dotted lines ±0·5)',fontsize=7.5,color=SEC,va='bottom')
# ---------- C: temperature support
ax2=fig.add_subplot(gs[2])
ax2.axvspan(26,29,color='#fdeee7',zorder=0); 
for i,c in enumerate(order):
    v=A[A.iso3==c].power_tmean_c.dropna(); q=v.quantile([.05,.1,.5,.9,.95]).values
    ax2.plot([q[0],q[4]],[i,i],color='#c3c2b7',lw=1.2,solid_capstyle='round'); ax2.plot([q[1],q[3]],[i,i],color=S1,lw=5,solid_capstyle='round',alpha=.9)
    ax2.plot(q[2],i,'o',ms=5,color='#fcfcfb',mec=INK,mew=1.1,zorder=3)
    XX=A[A.iso3==c]; wv=XX.groupby('shapeID').power_tmean_c.agg(lambda u:u.quantile(.9)-u.quantile(.1)).median(); hv=(XX.power_tmean_c>29).mean()*100
    ax2.text(37.8,i,f'{wv:.1f} °C   {hv:.1f}%'.replace('.','·'),ha='right',va='center',fontsize=6.2,color=SEC)
P=A.power_tmean_c.quantile([.1,.5,.9]).values
for p,l,dy in zip(P,['P10','P50','P90'],[-.75,-1.25,-.75]): ax2.axvline(p,color=MUT,lw=.7,ls=(0,(3,2))); ax2.text(p+(.2 if l=='P90' else (-.2 if l=='P50' else 0)),dy,f'pooled {l} {p:.1f}'.replace('.','·'),ha='left' if l=='P90' else ('right' if l=='P50' else 'center'),va='bottom',fontsize=5.8,color=SEC,bbox=dict(fc='#fcfcfb',ec='none',pad=.6))
ax2.set_yticks(range(len(order))); ax2.set_yticklabels([NM[c] for c in order],fontsize=7); ax2.set_ylim(len(order)-.4,-1.1)
ax2.text(37.8,-.75,'within-province\nP10–P90 width   >29 °C',ha='right',va='bottom',fontsize=5.8,color=SEC)
ax2.set_xlim(13,38); ax2.set_xlabel('Monthly mean temperature, province-months (°C)   ·   thick bar 10th–90th percentile, thin 5th–95th, dot median',fontsize=6.5,color=SEC)
ax2.tick_params(length=0); ax2.grid(axis='x',color=GRID,lw=.5); ax2.set_axisbelow(True); ax2.spines['left'].set_visible(False)
p=ax2.get_position(); fig.text(.06,p.y1+.015,'C',fontsize=11,fontweight='bold',color=INK)
fig.text(.09,p.y1+.017,'Exposure support by country (shaded band: 26–29 °C, peak transmission in mechanistic models)',fontsize=7.5,color=SEC)
fig.savefig('out/Figure2_data_at_a_glance.png',dpi=300,bbox_inches='tight',facecolor='#fcfcfb'); fig.savefig('out/Figure2_data_at_a_glance.pdf',bbox_inches='tight',facecolor='#fcfcfb')
print('ok')
