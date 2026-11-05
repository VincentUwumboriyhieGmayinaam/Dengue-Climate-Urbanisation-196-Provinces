"""Figure 4 (revised): exposure–response (top) and lag–response (bottom) for absolute temperature, absolute rainfall and
temperature anomaly from the province's calendar-month climatology (within-province contrast)."""
import pandas as pd, numpy as np, matplotlib as mpl, matplotlib.pyplot as plt
mpl.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 7.2, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.edgecolor': '#c3c2b7', 'axes.linewidth': .6, 'xtick.color': '#52514e', 'ytick.color': '#52514e'})
INK, SEC, GRID, SURF = '#0b0b0b', '#52514e', '#e1e0d9', '#ffffff'
CT, CR, CA = '#d2561f', '#2a78d6', '#7a4fb3'
dot = lambda v: f'{v:.2f}'.replace('.', '·')
C = pd.read_csv('out/curves_cum_v2_primary.csv'); L = pd.read_csv('out/curves_lag_v2_primary.csv')
CN = pd.read_csv('out/curves_cum_v2_noONI.csv')
CA_ = pd.read_csv('out/curves_cum_v2_anomaly.csv'); LA = pd.read_csv('out/curves_lag_v2_anomaly.csv')
D = pd.read_csv('data/P3_dengue_admin1_month_climate.csv'); D = D[D.year.between(2010, 2022)]
fig = plt.figure(figsize=(7.4, 5.4)); gs = fig.add_gridspec(2, 3, height_ratios=[1.3, 1], hspace=.62, wspace=.32)

def cum_panel(ax, c, col, colr, pts, xl, title, sens=None, ref=None, unit=''):
    if col: lo_x, hi_x = D[col].quantile([.01, .99]); c = c[c.value.between(lo_x, hi_x)]
    ax.fill_between(c.value, c.lo, c.hi, color=colr, alpha=.18, lw=0); ax.plot(c.value, c.RR, color=colr, lw=1.9)
    if sens is not None:
        s = sens[sens.value.between(c.value.min(), c.value.max())]; ax.plot(s.value, s.RR, color=SEC, lw=1, ls=(0, (3, 2)), label='Without ONI')
        ax.legend(frameon=False, fontsize=6, loc='lower right')
    ax.axhline(1, color='#898781', lw=.7); ax.set_yscale('log')
    yt = [.1, .25, .5, 1, 2, 4]; lo_, hi_ = max(c.lo.min() * .8, .08), min(c.hi.max() * 1.5, 6)
    ax.set_ylim(lo_, hi_); ax.set_yticks([v for v in yt if lo_ <= v <= hi_]); ax.set_yticklabels([str(v).replace('.', '·') for v in yt if lo_ <= v <= hi_]); ax.minorticks_off()
    ax.grid(axis='y', color=GRID, lw=.5); ax.set_axisbelow(True); ax.set_xlabel(xl, color=SEC)
    for p, lab, dx, dy, ha in pts:
        r = c.iloc[(c.value - p).abs().argsort().iloc[0]]
        ax.plot(r.value, r.RR, 'o', ms=4.5, color=SURF, mec=colr, mew=1.3, zorder=4)
        ax.annotate(f'{lab}: {dot(r.RR)}\n({dot(r.lo)}–{dot(r.hi)})', (r.value, r.RR), textcoords='offset points', xytext=(dx, dy), ha=ha, fontsize=6.1, color=INK)
    if ref is not None: ax.axvline(ref, color='#c3c2b7', lw=.6, ls=(0, (2, 2)))
    if col:
        h, e = np.histogram(D[col].dropna().clip(lo_x, hi_x), bins=40); a2 = ax.inset_axes([0, 0, 1, .07])
        a2.bar(e[:-1], h, width=np.diff(e), align='edge', color='#c3c2b7', lw=0); a2.set_xlim(ax.get_xlim()); a2.axis('off')
    ax.set_title(title, loc='left', fontsize=8.3, fontweight='bold', color=INK)

def lag_panel(ax, l, colr, series, title, xl='Lag (months)'):
    for tag, lab, a, ls in series:
        d = l[l.point.astype(str).str.lstrip('+') == tag.lstrip('+')].sort_values('lag')
        ax.fill_between(d.lag, d.lo, d.hi, color=colr, alpha=.14 * a, lw=0); ax.plot(d.lag, d.RR, color=colr, lw=1.7, alpha=a, ls=ls)
        ax.text(6.15, d.RR.iloc[-1], lab, fontsize=6, color=colr, va='center')
    ax.axhline(1, color='#898781', lw=.7); ax.set_xlim(0, 7.9); ax.set_xticks(range(7)); ax.set_xlabel(xl, color=SEC)
    ax.grid(axis='y', color=GRID, lw=.5); ax.set_axisbelow(True); ax.set_title(title, loc='left', fontsize=8, fontweight='bold', color=INK)

t = C[C.exposure == 'temperature'].sort_values('value'); r = C[C.exposure == 'rainfall'].sort_values('value')
ax = fig.add_subplot(gs[0, 0]); cum_panel(ax, t, 'power_tmean_c', CT, [(21.0, 'P10', 6, -20, 'left'), (28.5, 'P90', -10, 4, 'right')],
    'Monthly mean temperature (°C)', 'A  Temperature', sens=CN[CN.exposure == 'temperature'].sort_values('value'), ref=25.7)
ax.set_ylabel('Cumulative RR, lags 0–6 (log)', color=SEC)
ax = fig.add_subplot(gs[0, 1]); cum_panel(ax, r, 'power_precip_mm', CR, [(8, 'P10', 8, -4, 'left'), (304, 'P90', -4, 12, 'right')],
    'Monthly rainfall (mm)', 'B  Rainfall', ref=126)
a = CA_[(CA_.exposure == 'temperature') & CA_.value.between(-2, 2)].sort_values('value')
ax = fig.add_subplot(gs[0, 2]); cum_panel(ax, a, None, CA, [(-1, '−1°C', 4, -20, 'left'), (1, '+1°C', -4, 12, 'right')],
    'Temperature anomaly (°C)', 'C  Temperature anomaly', ref=0)
ax = fig.add_subplot(gs[1, 0]); lag_panel(ax, L[L.exposure == 'temperature'], CT, [('P90', 'P90', 1, '-'), ('P10', 'P10', .55, (0, (4, 2)))], 'D  Temperature by lag')
ax.set_ylabel('RR at each lag', color=SEC)
ax = fig.add_subplot(gs[1, 1]); lag_panel(ax, L[L.exposure == 'rainfall'], CR, [('P90', 'P90', 1, '-'), ('P10', 'P10', .55, (0, (4, 2)))], 'E  Rainfall by lag')
ax = fig.add_subplot(gs[1, 2]); lag_panel(ax, LA[LA.exposure == 'temperature'], CA, [('+1', '+1°C', 1, '-'), ('-1', '−1°C', .55, (0, (4, 2)))], 'F  Anomaly by lag')
for f in ('png', 'pdf'): fig.savefig(f'out/Figure4_v2.{f}', dpi=300, bbox_inches='tight', facecolor=SURF)
print('ok')
