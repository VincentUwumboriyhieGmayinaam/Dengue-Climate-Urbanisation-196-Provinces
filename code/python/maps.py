import geopandas as gpd, pandas as pd, numpy as np, matplotlib as mpl, matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm, Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import matplotlib.patheffects as pe
mpl.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 7.5})
INK, SEC, MUT, SURF = '#0b0b0b', '#52514e', '#898781', '#fcfcfb'
EQ = '+proj=eqearth +lon_0=0 +datum=WGS84 +units=m +no_defs'
G = gpd.read_file('zip://data/boundaries/P3_provinces_ADM1_shapefile.zip!P3_provinces_ADM1.shp')
G = G[G.iso3 != 'AUS']
M = pd.read_csv('data/province_metrics.csv')
G = G.merge(M, on=['shapeID', 'iso3'], how='left').to_crs(EQ)
G['included'] = G.cases_per_year.notna()
REG = {'Latin America': ['BRA', 'COL', 'PER', 'NIC', 'BOL'], 'Southeast Asia': ['THA', 'IDN']}
NM = {'BRA': 'Brazil', 'COL': 'Colombia', 'PER': 'Peru', 'NIC': 'Nicaragua', 'BOL': 'Bolivia', 'THA': 'Thailand', 'IDN': 'Indonesia'}
cyc = mpl.colormaps['twilight_shifted']
div = LinearSegmentedColormap.from_list('d', ['#1c5cab', '#86b6ef', '#f0efec', '#f2a48c', '#c4383a'])
seqo = LinearSegmentedColormap.from_list('o', ['#fdeee7', '#f2a48c', '#eb6834', '#b8481f', '#7a2d0e'])

fig = plt.figure(figsize=(7.2, 10.2))
gs = fig.add_gridspec(4, 2, width_ratios=[1.0, 1.25], hspace=0.28, wspace=0.04, left=0.02, right=0.86, top=0.93, bottom=0.03)
rows = [('A', 'Analytic sample and reported dengue', None),
        ('B', 'Month of peak dengue cases', None),
        ('C', 'Months from the rainfall peak to the case peak', None),
        ('D', 'Synchrony with El Niño: correlation of deseasonalised cases with ONI three months earlier', None)]

def base(ax, sub, alpha=1):
    sub.plot(ax=ax, color='#f3f2ee', edgecolor='#c3c2b7', linewidth=0.25)
    sub[~sub.included].plot(ax=ax, facecolor='#f3f2ee', edgecolor='#c3c2b7', hatch='/////', linewidth=0.25)

for r, (lab, title, _) in enumerate(rows):
    for c, (reg, isos) in enumerate(REG.items()):
        ax = fig.add_subplot(gs[r, c]); ax.set_axis_off()
        sub = G[G.iso3.isin(isos)]; inc = sub[sub.included]
        base(ax, sub)
        if r == 0:
            inc.plot(ax=ax, color='#e6f0fc', edgecolor='#86b6ef', linewidth=0.3)
            pts = inc.copy(); pts['geometry'] = inc.representative_point()
            ax.scatter(pts.geometry.x, pts.geometry.y, s=np.sqrt(pts.cases_per_year) / 4.5, color='#2a78d6', alpha=.75,
                       edgecolor=SURF, linewidth=.4, zorder=3)
            for iso in isos:
                g = sub[sub.iso3 == iso]
                if len(g):
                    p = g.dissolve().representative_point().iloc[0]
                    off = {'BRA': (0, -8e5), 'BOL': (0, 0), 'PER': (-5e5, -2e5), 'COL': (-4e5, 3e5), 'NIC': (-2.5e5, 3e5), 'THA': (-9e5, 2e5), 'IDN': (0, -9e5)}.get(iso, (0, 0))
                    ax.text(p.x + off[0], p.y + off[1], NM[iso] + (' (excluded)' if iso == 'BOL' else ''), fontsize=6.8,
                            color=INK if iso != 'BOL' else MUT, ha='center', fontweight='bold' if iso != 'BOL' else 'normal', zorder=5,
                            path_effects=[pe.withStroke(linewidth=2.2, foreground=SURF)])
        elif r == 1:
            inc.plot(ax=ax, column='peak_case', cmap=cyc, vmin=1, vmax=13, edgecolor=SURF, linewidth=0.25)
            weak = inc[inc.season_strength < 0.15]
            weak.plot(ax=ax, facecolor='none', edgecolor=MUT, hatch='....', linewidth=0)
        elif r == 2:
            ok = inc[inc.season_strength >= 0.15]
            ok.plot(ax=ax, column='lag_rain_to_case', cmap=div, norm=TwoSlopeNorm(0, -3, 3), edgecolor=SURF, linewidth=0.25)
            inc[inc.season_strength < 0.15].plot(ax=ax, facecolor='#f3f2ee', edgecolor=MUT, hatch='....', linewidth=0.25)
        else:
            inc.plot(ax=ax, column='r_oni_lag3', cmap=div, norm=TwoSlopeNorm(0, -0.6, 0.6), edgecolor=SURF, linewidth=0.25)
        if c == 0:
            ax.text(0, 1.06, lab, transform=ax.transAxes, fontsize=11, fontweight='bold', color=INK, va='bottom')
            ax.text(0.085, 1.065, title, transform=ax.transAxes, fontsize=8, color=SEC, va='bottom')

for c, reg in enumerate(REG):
    p = fig.axes[c].get_position(); fig.text(p.x0 + p.width / 2, 0.975, reg, ha='center', fontsize=9, fontweight='bold', color=INK)
# legends / colour bars at right of each row
def cbar(r, cmap, norm, ticks, labels, text):
    p = fig.axes[2 * r + 1].get_position()
    cax = fig.add_axes([0.885, p.y0 + p.height * 0.15, 0.012, p.height * 0.7])
    cb = mpl.colorbar.ColorbarBase(cax, cmap=cmap, norm=norm, ticks=ticks); cb.ax.set_yticklabels(labels, fontsize=6.3)
    cb.outline.set_visible(False); cb.ax.tick_params(length=0); cax.set_title(text, fontsize=6.3, color=SEC, loc='left', pad=14)
p = fig.axes[1].get_position()
for i, v in enumerate([1000, 10000, 100000]):
    fig.axes[1].scatter([], [], s=np.sqrt(v) / 4.5, color='#2a78d6', alpha=.75, label=f'{v:,}'.replace(',', ' '))
h, l = fig.axes[1].get_legend_handles_labels(); h.append(Patch(facecolor='#f3f2ee', edgecolor='#c3c2b7', hatch='/////')); l.append('Excluded\n(<80% of months\nreported)')
leg = fig.axes[1].legend(h, l, title='Mean cases per year', loc='center left', bbox_to_anchor=(1.0, 0.55), frameon=False, fontsize=6.3, title_fontsize=6.3, labelspacing=1.1)
fig.axes[1].legend_ = leg

cbar(1, cyc, Normalize(1, 13), [1, 4, 7, 10, 13], ['Jan', 'Apr', 'Jul', 'Oct', 'Jan'], 'Peak month')
cbar(2, div, TwoSlopeNorm(0, -3, 3), [-3, 0, 3], ['≥3 mo before', 'same month', '≥3 mo after'], 'Case peak vs\nrainfall peak')
cbar(3, div, TwoSlopeNorm(0, -0.6, 0.6), [-0.6, -0.3, 0, 0.3, 0.6], ['−0·6', '−0·3', '0', '0·3', '0·6'], 'Correlation r')
fig.text(0.885, fig.axes[2].get_position().y0 - 0.01, 'Dotted: weak\nseasonality', fontsize=6, color=SEC)
fig.savefig('out/Figure3_spatial_patterns.png', dpi=300, facecolor=SURF); fig.savefig('out/Figure3_spatial_patterns.pdf', facecolor=SURF)
print('ok')
