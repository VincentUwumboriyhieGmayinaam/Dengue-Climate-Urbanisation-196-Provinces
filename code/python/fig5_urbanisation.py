"""Figure 5: cumulative exposure–response at the 25th and 75th percentiles of (log) built-up fraction, within the exposure
range shared by less and more built-up provinces, with the ratio of relative risks (P75/P25) at the 10th and 90th percentiles."""
import pandas as pd, numpy as np, matplotlib as mpl, matplotlib.pyplot as plt
mpl.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 7.2, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.edgecolor': '#c3c2b7', 'axes.linewidth': .6, 'xtick.color': '#52514e', 'ytick.color': '#52514e'})
INK, SEC, GRID, SURF = '#0b0b0b', '#52514e', '#e1e0d9', '#ffffff'
C = pd.read_csv('out/urban_curves_urban.csv'); R = pd.read_csv('out/urban_ratio_P75_P25_urban.csv')
COL = {'P25': '#3f9a62', 'P75': '#59575a'}; LAB = {'P25': 'Less built-up (25th percentile)', 'P75': 'More built-up (75th percentile)'}
dot = lambda v: f'{v:.2f}'.replace('.', '·')
fig, axes = plt.subplots(1, 3, figsize=(7.4, 3.0), gridspec_kw={'width_ratios': [1, 1, .9]})
for ax, ex, xl, t in zip(axes[:2], ['T', 'R'], ['Monthly mean temperature (°C)', 'Monthly rainfall (mm)'], ['A  Temperature', 'B  Rainfall']):
    for b in ['P25', 'P75']:
        d = C[(C.exposure == ex) & (C.built == b)].sort_values('value')
        ax.fill_between(d.value, d.lo, d.hi, color=COL[b], alpha=.15, lw=0); ax.plot(d.value, d.RR, color=COL[b], lw=1.8, label=LAB[b])
    ax.axhline(1, color='#898781', lw=.7); ax.set_yscale('log'); ax.minorticks_off()
    yt = [.1, .25, .5, 1, 2, 4]; lo, hi = ax.get_ylim(); ax.set_yticks([v for v in yt if lo <= v <= hi]); ax.set_yticklabels([str(v).replace('.', '·') for v in yt if lo <= v <= hi])
    ax.grid(axis='y', color=GRID, lw=.5); ax.set_axisbelow(True); ax.set_xlabel(xl, color=SEC); ax.set_title(t, loc='left', fontsize=8.5, fontweight='bold', color=INK)
    rr = R[R.exposure == ex]
    txt = '\n'.join(f"Ratio P75/P25 at {p.point}: {dot(p.ratio)} ({dot(p.lo)}–{dot(p.hi)})" + ('' if p.within_shared else '*') for p in rr.itertuples())
axes[0].set_ylabel('Cumulative RR, lags 0–6 (log)', color=SEC)
axes[1].legend(frameon=False, fontsize=6, loc='lower right', bbox_to_anchor=(1, .02))
TT = pd.read_csv('out/urban_tertiles.csv'); TT = TT[TT.tertile.astype(str).isin(['1', '2', '3'])]
ax = axes[2]; pts = [('T', 28.5, 'Warm month\n(28·5°C)'), ('R', 8.0, 'Dry month\n(8 mm)'), ('R', 304.0, 'Wet month\n(304 mm)')]
tc = {'1': '#3f9a62', '2': '#9a998f', '3': '#2c2b2d'}
for i, (ex, v, lab) in enumerate(pts):
    for k, t in enumerate(['1', '2', '3']):
        r = TT[(TT.exposure == ex) & np.isclose(TT.value, v) & (TT.tertile.astype(str) == t)].iloc[0]; y = i + (k - 1) * .22
        ax.plot([r.lo, r.hi], [y, y], color=tc[t], lw=1.3); ax.plot(r.RR, y, 'o', ms=4, color=tc[t], label=['Least', 'Middle', 'Most'][k] + ' built-up tertile' if i == 0 else None)
ax.axvline(1, color='#898781', lw=.7); ax.set_xscale('log'); ax.minorticks_off(); ax.set_xticks([.25, .5, 1, 2]); ax.set_xticklabels(['0·25', '0·5', '1', '2'])
ax.set_yticks(range(3)); ax.set_yticklabels([p[2] for p in pts], fontsize=6.5); ax.invert_yaxis(); ax.spines['left'].set_visible(False); ax.tick_params(axis='y', length=0)
ax.set_xlabel('Cumulative RR (log)', color=SEC); ax.set_title('C  Within-country tertiles', loc='left', fontsize=8.5, fontweight='bold', color=INK)
ax.grid(axis='x', color=GRID, lw=.5); ax.set_axisbelow(True); ax.legend(frameon=False, fontsize=5.8, loc='upper left', bbox_to_anchor=(-.35, -.2), ncol=3, columnspacing=.8, handletextpad=.2)
fig.tight_layout(w_pad=3.2)
for f in ('png', 'pdf'): fig.savefig(f'out/Figure7_urban.{f}', dpi=300, bbox_inches='tight', facecolor=SURF)
print('ok')
