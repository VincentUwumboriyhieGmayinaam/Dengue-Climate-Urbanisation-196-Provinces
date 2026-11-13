"""Supplementary figures S1–S6."""
import pandas as pd, numpy as np, matplotlib as mpl, matplotlib.pyplot as plt, geopandas as gpd
mpl.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 7.5, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.edgecolor': '#c3c2b7', 'axes.linewidth': .6, 'xtick.color': '#52514e', 'ytick.color': '#52514e'})
INK, SEC, GRID, SURF, BLUE, ORG, PUR = '#0b0b0b', '#52514e', '#e1e0d9', '#ffffff', '#2a78d6', '#d2561f', '#7a4fb3'
NM = {'BRA': 'Brazil', 'COL': 'Colombia', 'IDN': 'Indonesia', 'NIC': 'Nicaragua', 'PER': 'Peru', 'THA': 'Thailand'}
O = 'out/'; save = lambda f, n: [f.savefig(f'{O}FigureS{n}.{e}', dpi=300, bbox_inches='tight', facecolor=SURF) for e in ('png', 'pdf')]
# S1 PIT
p = pd.read_csv(O + 'v2_primary_pit.csv'); f, ax = plt.subplots(figsize=(3.6, 2.6))
ax.bar(p.bin, p.share, width=.095, color=BLUE, alpha=.8); ax.axhline(.1, color=SEC, ls=(0, (3, 2)), lw=.9)
ax.set_xlabel('Probability integral transform', color=SEC); ax.set_ylabel('Share of province-months', color=SEC); ax.set_xlim(0, 1); save(f, 4)
# S2 ACF and Moran
a = pd.read_csv(O + 'v2_primary_acf_by_province.csv'); m1 = pd.read_csv(O + 'v2_primary_moran_by_month.csv'); m2 = pd.read_csv(O + 'v2_ctrymonth_moran_by_month.csv')
f, ax = plt.subplots(1, 2, figsize=(7.2, 2.7), gridspec_kw={'width_ratios': [1, 1.6]})
ax[0].boxplot([a.acf1.dropna(), a.acf12.dropna()], tick_labels=['Lag 1', 'Lag 12'], widths=.5, medianprops=dict(color=ORG), flierprops=dict(ms=2))
ax[0].axhline(0, color=SEC, lw=.7); ax[0].set_ylabel('Residual autocorrelation', color=SEC); ax[0].set_title('A  Within-province autocorrelation', loc='left', fontsize=8, fontweight='bold')
for d, lab, c in [(m1, 'Primary model (BYM2)', BLUE), (m2, 'With country-by-month effect', SEC)]:
    d = d.sort_values(['year', 'month']); x = d.year + (d.month - .5) / 12; ax[1].plot(x, d.I, color=c, lw=1, label=lab)
ax[1].axhline(0, color=SEC, lw=.6); ax[1].axhline(.2, color=SEC, lw=.6, ls=(0, (2, 2))); ax[1].set_ylabel("Moran's I", color=SEC)
ax[1].legend(frameon=False, fontsize=6.5); ax[1].set_title("B  Residual spatial autocorrelation by month", loc='left', fontsize=8, fontweight='bold'); f.tight_layout(); save(f, 5)
# S3 BYM2 province effect map
b = pd.read_csv(O + 'bym2_province_effect.csv'); G = gpd.read_file('zip://data/boundaries/P3_provinces_ADM1_shapefile.zip!P3_provinces_ADM1.shp').merge(b, on='shapeID')
f, axs = plt.subplots(2, 3, figsize=(7.4, 4.6)); lim = np.nanmax(np.abs(b.effect))
for ax, c in zip(axs.flat, NM):
    g = G[G.iso3 == c]; g.plot(column='effect', cmap='RdBu_r', vmin=-lim, vmax=lim, ax=ax, edgecolor='white', linewidth=.2)
    ax.set_title(NM[c], fontsize=8, fontweight='bold'); ax.axis('off')
sm = mpl.cm.ScalarMappable(cmap='RdBu_r', norm=mpl.colors.Normalize(-lim, lim)); cb = f.colorbar(sm, ax=axs, shrink=.6, pad=.02); cb.set_label('BYM2 province effect (log scale)', color=SEC)
save(f, 3)
# S4 country anomaly curves
f, axs = plt.subplots(1, 6, figsize=(7.4, 2.2), sharey=True)
for ax, c in zip(axs, NM):
    C = pd.read_csv(f'{O}curves_cum_v2_an_{c}.csv'); C = C[(C.exposure == 'temperature') & C.value.between(-1.5, 1.5)].sort_values('value')
    ax.fill_between(C.value, C.lo.clip(.05, 20), C.hi.clip(.05, 20), color=PUR, alpha=.18, lw=0); ax.plot(C.value, C.RR, color=PUR, lw=1.5)
    ax.axhline(1, color=SEC, lw=.6); ax.axvline(0, color=GRID, lw=.6); ax.set_yscale('log'); ax.minorticks_off(); ax.set_title(NM[c], fontsize=7.5, fontweight='bold')
    ax.set_yticks([.25, .5, 1, 2, 4]); ax.set_yticklabels(['0.25', '0.5', '1', '2', '4']); ax.set_ylim(.2, 5); ax.set_xlabel('Anomaly (°C)', color=SEC, fontsize=6.5)
axs[0].set_ylabel('Cumulative RR (log)', color=SEC); f.tight_layout(w_pad=.3); save(f, 1)
# S5 forest plot of sensitivity analyses (temperature P90)
T = pd.read_csv(O + 'table2_v2.csv').set_index('label')
order = [('primary', 'Primary (BYM2)'), ('iid', 'Unstructured province effect'), ('noONI', 'Without ONI'), ('drop1516', 'Excluding 2015-16'), ('drop2021', 'Excluding 2020-21'),
         ('harm3', 'Three harmonic pairs'), ('rainlog', 'Log rainfall'), ('lag9', 'Lags 0-9'), ('lagdf4', 'Lag spline 4 df'), ('trend', 'Province trend, no offset'),
         ('ctrymonth', 'Country-by-month effect'), ('noBRA', 'Excluding Brazil')] + [(f'jk_{c}', f'Excluding {NM[c]}') for c in ['COL', 'IDN', 'NIC', 'PER', 'THA']]
order = [o for o in order if o[0] in T.index]
parse = lambda s: [float(x) for x in s.replace('(', ' ').replace(')', ' ').replace('–', ' ').split()]
f, ax = plt.subplots(figsize=(4.6, .26 * len(order) + .6))
for k, (lab, nm) in enumerate(order):
    e, lo, hi = parse(T.loc[lab, 'RR_T90']); y = len(order) - k
    ax.plot([lo, hi], [y, y], color=ORG if lab == 'primary' else SEC, lw=1.4); ax.plot(e, y, 'o', ms=4.5, color=ORG if lab == 'primary' else INK)
ax.set_yticks([len(order) - k for k in range(len(order))]); ax.set_yticklabels([o[1] for o in order], fontsize=6.8)
ax.axvline(1, color=SEC, lw=.7); ax.set_xscale('log'); ax.minorticks_off(); ax.set_xticks([1, 1.5, 2, 3]); ax.set_xticklabels(['1', '1.5', '2', '3'])
ax.set_xlabel('Cumulative RR at 28.5°C vs 25.7°C (log)', color=SEC); ax.spines['left'].set_visible(False); ax.tick_params(axis='y', length=0); save(f, 2)
# S6 holdout observed vs predicted
Hh = pd.read_csv(O + 'holdout_country_month.csv'); f, axs = plt.subplots(2, 3, figsize=(7.4, 4.0))
for ax, c in zip(axs.flat, NM):
    d = Hh[Hh.iso3 == c].sort_values('ahead')
    ax.plot(d.ahead, d.observed, color=INK, lw=1.4, label='Observed'); ax.plot(d.ahead, d.climate, color=ORG, lw=1.1, label='With climate')
    ax.plot(d.ahead, d.baseline, color=BLUE, lw=1.1, ls=(0, (3, 2)), label='Without climate'); ax.set_title(NM[c], fontsize=8, fontweight='bold')
    ax.set_xticks([1, 7, 13, 19, 24]); ax.set_xticklabels(['Jan 21', 'Jul 21', 'Jan 22', 'Jul 22', 'Dec 22'], fontsize=6)
    ax.ticklabel_format(axis='y', style='plain'); ax.grid(axis='y', color=GRID, lw=.4)
axs[0, 0].legend(frameon=False, fontsize=6); axs[0, 0].set_ylabel('Reported cases per month', color=SEC); f.tight_layout(); save(f, 6)
print('supp figures ok')
