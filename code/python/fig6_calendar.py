"""Figure 6: decision calendar. One row per country: typical month of peak reported cases (case-weighted circular mean
across provinces, with the interquartile range of province peaks), the months whose temperature anomaly is associated
with the peak (lags in which the pooled +1°C anomaly lag-specific RR has a lower 95% bound above 1), and the cumulative
RR per +1°C anomaly from the country's own anomaly model."""
import pandas as pd, numpy as np, matplotlib as mpl, matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
mpl.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 7.2, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.spines.left': False, 'axes.edgecolor': '#c3c2b7', 'xtick.color': '#52514e'})
INK, SEC, GRID, SURF, ACC, PK = '#0b0b0b', '#52514e', '#e1e0d9', '#ffffff', '#7a4fb3', '#d2561f'
NM = {'BRA': 'Brazil', 'COL': 'Colombia', 'IDN': 'Indonesia', 'NIC': 'Nicaragua', 'PER': 'Peru', 'THA': 'Thailand'}
P = pd.read_csv('data/province_metrics.csv')
LA = pd.read_csv('out/curves_lag_v2_anomaly.csv'); la = LA[(LA.exposure == 'temperature') & (LA.point.astype(str).str.lstrip('+') == '1')]
la = la[np.isclose(la.lag % 1, 0)]; inf_lags = la[la.lo > 1].lag.astype(int).tolist()
STRONG = la[la.RR >= la.RR.max() - .002].lag.astype(int).tolist()
A = pd.read_csv('out/anomaly_by_fit.csv').set_index('label'); FSu = pd.read_csv('out/fit_summary_v2.csv').set_index('label')
dot = lambda s: s.replace('.', '·')
def circ(m, w):
    a = 2 * np.pi * (np.asarray(m) - 1) / 12; z = np.sum(w * np.exp(1j * a)) / np.sum(w); return (np.angle(z) / (2 * np.pi) * 12) % 12 + 1
rows = []
for c in NM:
    d = P[P.iso3 == c]; pk = circ(d.peak_case, d.cases_per_year)
    dev = ((d.peak_case - pk + 6) % 12) - 6; q1, q3 = np.percentile(dev, [25, 75])
    rows.append((c, pk, q1, q3))
fig, ax = plt.subplots(figsize=(7.4, 3.3)); X0 = 0.5
XL = min(r[1] for r in rows) + 12 - max(inf_lags) - 1.2; XR = max(r[1] for r in rows) + 12 + 2.2;
mlab = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'] * 2
for i, (c, pk, q1, q3) in enumerate(rows):
    y = len(rows) - 1 - i; shift = 12                         # draw on a 24-month strip so windows don't wrap
    pkx = pk + shift
    for L in inf_lags: ax.add_patch(Rectangle((pkx - L - .5, y - .28), 1, .56, color=ACC, alpha=.42 if L in STRONG else .16, lw=0))
    ax.plot([pkx + q1, pkx + q3], [y, y], color=PK, lw=3, alpha=.35, solid_capstyle='round')
    ax.plot(pkx, y, 'o', ms=7, color=PK, mec=SURF, mew=1)
    lab = f'an_{c}'; rr = (dot(A.loc[lab, 'cum_plus1']) + ('†' if not FSu.loc[lab, 'pdHess'] else '')) if lab in A.index else 'pending'
    ax.text(XR + .3, y, rr, va='center', fontsize=6.8, color=INK)
    ax.text(XL - .2, y, NM[c], va='center', ha='right', fontsize=7.5, fontweight='bold', color=INK)
ax.set_xlim(XL, XR + 2.6); ax.set_ylim(-.7, len(rows) - .3); ax.set_yticks([])
tk = [x for x in range(1, 25) if XL <= x <= XR]; ax.set_xticks(tk); ax.set_xticklabels([mlab[x - 1] for x in tk], fontsize=6.5)
ax.axvline(12.5, color=GRID, lw=.8); ax.text(12.6, len(rows) - .35, 'January', fontsize=6, color=SEC)
ax.text(XR + .3, len(rows) - .35, 'Cumulative RR per\n+1°C anomaly (95% CI)', fontsize=6, color=SEC, va='bottom')
ax.grid(axis='x', color=GRID, lw=.4); ax.spines['bottom'].set_visible(False); ax.tick_params(axis='x', length=0); ax.set_axisbelow(True)
from matplotlib.lines import Line2D
h = [Line2D([], [], marker='o', ls='', color=PK, ms=6, label='Typical case peak (IQR across provinces)'),
     Rectangle((0, 0), 1, 1, color=ACC, alpha=.16, label=f'Anomaly associated with the peak (lags {min(inf_lags)}–{max(inf_lags)})'),
     Rectangle((0, 0), 1, 1, color=ACC, alpha=.42, label=f'Strongest association (lags {min(STRONG)}–{max(STRONG)})')]
ax.legend(handles=h, frameon=False, fontsize=6.2, loc='upper center', bbox_to_anchor=(.45, -.1), ncol=3)
fig.savefig('out/Figure6_decision_calendar.png', dpi=300, bbox_inches='tight', facecolor=SURF)
fig.savefig('out/Figure6_decision_calendar.pdf', bbox_inches='tight', facecolor=SURF)
print('informative lags', inf_lags, [(c, round(p, 2), round(q1, 1), round(q3, 1)) for c, p, q1, q3 in rows])
