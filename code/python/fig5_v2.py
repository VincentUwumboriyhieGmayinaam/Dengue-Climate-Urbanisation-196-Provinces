"""Figure 5 (revised): country-specific curves with country knots, centred on each country's median, within its 5th–95th percentile."""
import pandas as pd, numpy as np, matplotlib as mpl, matplotlib.pyplot as plt
mpl.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 7, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.edgecolor': '#c3c2b7', 'axes.linewidth': .6, 'xtick.color': '#52514e', 'ytick.color': '#52514e'})
INK, SEC, GRID, SURF = '#0b0b0b', '#52514e', '#e1e0d9', '#ffffff'
COL = {'temperature': '#d2561f', 'rainfall': '#2a78d6'}
NM = {'BRA': 'Brazil', 'COL': 'Colombia', 'IDN': 'Indonesia', 'NIC': 'Nicaragua', 'PER': 'Peru', 'THA': 'Thailand'}
D = pd.read_csv('data/P3_dengue_admin1_month_climate.csv'); D = D[D.year.between(2010, 2022)]
T2 = pd.read_csv('out/table2_v2.csv').set_index('label')
var = {'temperature': 'power_tmean_c', 'rainfall': 'power_precip_mm'}
fig, axes = plt.subplots(2, 6, figsize=(7.4, 3.7), sharey='row')
for i, ex in enumerate(['temperature', 'rainfall']):
    for j, c in enumerate(NM):
        ax = axes[i, j]; d = D[D.iso3 == c][var[ex]]; lo, hi = d.quantile([.05, .95])
        C = pd.read_csv(f'out/curves_cum_v2_ck_{c}.csv'); C = C[(C.exposure == ex) & C.value.between(lo, hi)].sort_values('value')
        ax.fill_between(C.value, C.lo.clip(.05, 20), C.hi.clip(.05, 20), color=COL[ex], alpha=.18, lw=0)
        ax.plot(C.value, C.RR, color=COL[ex], lw=1.6)
        ref = T2.loc[f'ck_{c}', 'temp_ref' if ex == 'temperature' else 'rain_ref']; ax.axvline(ref, color='#9a998f', lw=.6, ls=(0, (1, 1.5)))
        ax.axhline(1, color='#898781', lw=.6); ax.set_yscale('log'); ax.set_ylim(.1, 10)
        ax.set_yticks([.1, .25, .5, 1, 2, 4, 10]); ax.set_yticklabels(['0·1', '0·25', '0·5', '1', '2', '4', '10']); ax.minorticks_off()
        ax.grid(axis='y', color=GRID, lw=.4); ax.set_axisbelow(True); ax.tick_params(labelsize=6)
        if i == 0: ax.set_title(NM[c], fontsize=7.5, fontweight='bold', color=INK)
        ax.set_xlabel('°C' if ex == 'temperature' else 'mm', color=SEC, fontsize=6.5)
    axes[i, 0].set_ylabel(('Temperature' if ex == 'temperature' else 'Rainfall') + '\ncumulative RR (log)', color=SEC)
fig.tight_layout(w_pad=.4, h_pad=1.2)
for f in ('png', 'pdf'): fig.savefig(f'out/Figure5_v2.{f}', dpi=300, facecolor=SURF)
print('ok')
