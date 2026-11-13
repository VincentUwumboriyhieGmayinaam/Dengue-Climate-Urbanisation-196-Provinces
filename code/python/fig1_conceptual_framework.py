# -*- coding: utf-8 -*-
"""Figure 1, layered 3D conceptual framework (oblique projection). Writes SVG; render.py makes PNG and PDF."""
import math
from PIL import ImageFont
FD = '/usr/share/fonts/truetype/liberation/LiberationSans-'
_f = {}
def font(size, bold=False, italic=False):
    k = (size, bold, italic)
    if k not in _f: _f[k] = ImageFont.truetype(FD + ('BoldItalic' if bold and italic else 'Bold' if bold else 'Italic' if italic else 'Regular') + '.ttf', size)
    return _f[k]
def tw(s, size, bold=False, italic=False, ls=0): return font(size, bold, italic).getlength(s) + ls * len(s)

W, H = 1800, 1384
K = 0.5                      # oblique projection: a point at depth d is drawn at (x + K d, y - d)
FF = "'Liberation Sans', Arial, Helvetica, sans-serif"
INK, SUB = '#14181F', '#4A5160'
ARROW, DASH, ORANGE, ORANGE_D = '#3A404A', '#7C828C', '#E2591B', '#A63F0F'
o = []
def add(s): o.append(s)
def esc(s): return s.replace('&', '&amp;').replace('<', '&lt;')
def pts(P): return ' '.join(f'{x:.1f},{y:.1f}' for x, y in P)
def poly(P, fill, stroke='none', sw=0, op=1, extra=''):
    add(f'<polygon points="{pts(P)}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round" opacity="{op}" {extra}/>')
def text(x, y, s, size=24, fill=INK, bold=False, italic=False, anchor='start', ls=0, halo=None, rot=None, op=1):
    st = f'font-family:{FF};font-size:{size}px;fill:{fill};' + ('font-weight:700;' if bold else '') + ('font-style:italic;' if italic else '') + (f'letter-spacing:{ls}px;' if ls else '')
    if halo: st += f'paint-order:stroke;stroke:{halo};stroke-width:6px;stroke-linejoin:round;'
    tr = f' transform="rotate({rot[0]} {rot[1]} {rot[2]})"' if rot else ''
    add(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" style="{st}" opacity="{op}"{tr}>{s}</text>')

# ------------------------------------------------------------------ defs
add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
add('''<defs>
<filter id="blur12" x="-30%" y="-60%" width="160%" height="220%"><feGaussianBlur stdDeviation="12"/></filter>
<filter id="blur5" x="-40%" y="-80%" width="180%" height="260%"><feGaussianBlur stdDeviation="4.5"/></filter>
<linearGradient id="gcard" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="#F1F3F6"/></linearGradient>
<linearGradient id="gcyl" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#0A2A55"/><stop offset=".35" stop-color="#1A4E93"/><stop offset=".7" stop-color="#103C76"/><stop offset="1" stop-color="#081F40"/></linearGradient>
<linearGradient id="gtowerF" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#FBD9C7"/><stop offset="1" stop-color="#F7C3A8"/></linearGradient>
<linearGradient id="gtowerR" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#EFA988"/><stop offset="1" stop-color="#F6C2A6"/></linearGradient>
<linearGradient id="gribbon" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#66758A"/><stop offset="1" stop-color="#2A6FC9"/></linearGradient>
</defs>''')
add(f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>')

# ------------------------------------------------------------------ primitives
def deck(x0, yf, Wd, D, tb, top, top2, band, side, title, num, gid):
    """Slab: front-left corner (x0, yf), width Wd, depth D, thickness tb."""
    T = [(x0, yf), (x0 + Wd, yf), (x0 + Wd + K * D, yf - D), (x0 + K * D, yf - D)]
    sh = [(x0 + 30, yf + tb + 34), (x0 + Wd + 20, yf + tb + 34), (x0 + Wd + K * D + 20, yf - D + tb + 60), (x0 + K * D + 30, yf - D + tb + 60)]
    poly(sh, '#1B2433', op=.16, extra='filter="url(#blur12)"')
    add(f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="0" y1="{yf}" x2="0" y2="{yf - D}"><stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{top2}"/></linearGradient>')
    poly([(x0 + Wd, yf), (x0 + Wd + K * D, yf - D), (x0 + Wd + K * D, yf - D + tb), (x0 + Wd, yf + tb)], side, side, 1.5)
    poly(T, f'url(#{gid})', band, 1.2)
    g = []                                                     # faint floor grid
    for d in range(50, int(D), 50): g.append(f'M{x0 + K * d:.1f},{yf - d} h{Wd}')
    for u in range(100, int(Wd), 100): g.append(f'M{x0 + u},{yf} l{K * D:.1f},{-D}')
    add(f'<path d="{" ".join(g)}" stroke="#FFFFFF" stroke-width="1.6" opacity=".75" fill="none"/>')
    add(f'<rect x="{x0}" y="{yf}" width="{Wd}" height="{tb}" fill="{band}" stroke="{band}" stroke-width="1.5" stroke-linejoin="round"/>')
    add(f'<path d="M{x0},{yf} h{Wd}" stroke="#FFFFFF" stroke-width="1.6" opacity=".55"/>')
    add(f'<rect x="{x0 + 12}" y="{yf + 7}" width="30" height="{tb - 14}" rx="6" fill="#FFFFFF" opacity=".95"/>')
    text(x0 + 27, yf + tb / 2 + 8.5, str(num), 24, band, bold=True, anchor='middle')
    text(x0 + 54, yf + tb / 2 + 8.5, esc(title), 24, '#FFFFFF', bold=True, ls=1.6)

def rrect(x, y, w, h, r, fill, stroke='none', sw=0, dash=None, op=1):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d} opacity="{op}"/>')

def block(x, yb, w, h, front='url(#gcard)', topc='#FFFFFF', sidec='#C9CED6', edge='#8D95A3', sw=1.8, dash=None, depth=14, r=10, shadow=True, fop=1):
    """Upright extruded card standing on a deck: front face (x, yb-h, w, h)."""
    y = yb - h; ex, ey = K * depth, -depth
    if shadow:
        poly([(x + 6, yb + 3), (x + w + 2, yb + 3), (x + w + 44, yb - 20), (x + 48, yb - 20)], '#1B2433', op=.30, extra='filter="url(#blur5)"')
    c, s = 0.894 * r, 0.447 * r
    tl = (x + r - c, y + r - s); p45 = (x + w - r + .707 * r, y + r - .707 * r); br = (x + w - r + c, yb - r + s)
    sh = lambda p: (p[0] + ex, p[1] + ey)
    poly([tl, (x + r, y), (x + w - r, y), p45, sh(p45), sh((x + w - r, y)), sh((x + r, y)), sh(tl)], topc, edge, 1.1, op=fop)
    poly([p45, sh(p45), sh((x + w, y + r)), sh((x + w, yb - r)), sh(br), br, (x + w, yb - r), (x + w, y + r)], sidec, edge, 1.1, op=fop)
    rrect(x, y, w, h, r, front, edge, sw, dash, op=fop)

def card(x, yb, w, h, title, subs, icon=None, accent='#5B6676', tint='#E9ECF1', edge=None, sw=1.8, dash=None, title_italic_first=False, **kw):
    block(x, yb, w, h, edge=edge or accent, sw=sw, dash=dash, **kw)
    y = yb - h; tx = x + 18
    if icon:
        ts = 58; ty = y + (h - ts) / 2
        rrect(x + 13, ty, ts, ts, 12, tint, accent, 1.4)
        icon(x + 13 + ts / 2, ty + ts / 2, accent)
        tx = x + 13 + ts + 14
    n = 1 + len(subs); lh_t, lh_s = 31, 28
    y0 = y + (h - (lh_t + lh_s * len(subs))) / 2 + 23
    if title_italic_first:
        a, b = title.split(' ', 1) if ' ' in title else (title, '')
        add(f'<text x="{tx:.1f}" y="{y0:.1f}" style="font-family:{FF};font-size:27px;fill:{INK};font-weight:700;"><tspan font-style="italic">{esc(a)}</tspan> {esc(b)}</text>')
    else: text(tx, y0, esc(title), 27, INK, bold=True)
    for i, s in enumerate(subs): text(tx, y0 + lh_t - 2 + lh_s * i, esc(s), 24, SUB)

def ghost(x, yb, w, h, title, subs, col='#6B7280'):
    """Flat dashed card: not observed or not in the main model."""
    y = yb - h
    rrect(x, y, w, h, 12, '#FFFFFF', col, 2, '8 6', op=1)
    add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="12" fill="#F4F5F7" opacity=".55"/>')
    lh_t, lh_s = 29, 27
    y0 = y + (h - (lh_t + lh_s * len(subs))) / 2 + 22
    text(x + 16, y0, esc(title), 25, '#3D4350', bold=True)
    for i, s in enumerate(subs): text(x + 16, y0 + lh_t - 2 + lh_s * i, esc(s), 24, '#555C69')

def head(p, ang, col, L=16, hw=7):
    x, y = p; ca, sa = math.cos(ang), math.sin(ang)
    bx, by = x - L * ca, y - L * sa
    poly([(x, y), (bx - hw * sa, by + hw * ca), (bx + hw * sa, by - hw * ca)], col)

def arrow(P, col=ARROW, sw=3.6, dash=None, r=26, heads=True, L=16, hw=7, halo=True, straight_last=True):
    """Polyline with rounded corners through points P; arrowhead at the end."""
    P = [tuple(map(float, p)) for p in P]
    x1, y1 = P[-1]; x0, y0 = P[-2]; ang = math.atan2(y1 - y0, x1 - x0)
    end = (x1 - (L - 2) * math.cos(ang), y1 - (L - 2) * math.sin(ang)) if heads else (x1, y1)
    Q = P[:-1] + [end]
    d = f'M{Q[0][0]:.1f},{Q[0][1]:.1f}'
    for i in range(1, len(Q) - 1):
        a, b, c = Q[i - 1], Q[i], Q[i + 1]
        la = math.hypot(b[0] - a[0], b[1] - a[1]); lc = math.hypot(c[0] - b[0], c[1] - b[1]); rr = min(r, la / 2, lc / 2)
        p1 = (b[0] - (b[0] - a[0]) / la * rr, b[1] - (b[1] - a[1]) / la * rr); p2 = (b[0] + (c[0] - b[0]) / lc * rr, b[1] + (c[1] - b[1]) / lc * rr)
        d += f' L{p1[0]:.1f},{p1[1]:.1f} Q{b[0]:.1f},{b[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}'
    d += f' L{Q[-1][0]:.1f},{Q[-1][1]:.1f}'
    da = f' stroke-dasharray="{dash}"' if dash else ''
    if halo: add(f'<path d="{d}" fill="none" stroke="#FFFFFF" stroke-width="{sw + 5}" stroke-linecap="round" opacity=".9"/>')
    add(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{sw}" stroke-linecap="butt" stroke-linejoin="round"{da}/>')
    if heads:
        if halo: poly([(x1 + 3 * math.cos(ang), y1 + 3 * math.sin(ang)), (x1 - (L + 2) * math.cos(ang) - (hw + 3) * math.sin(ang), y1 - (L + 2) * math.sin(ang) + (hw + 3) * math.cos(ang)),
                       (x1 - (L + 2) * math.cos(ang) + (hw + 3) * math.sin(ang), y1 - (L + 2) * math.sin(ang) - (hw + 3) * math.cos(ang))], '#FFFFFF', op=.9)
        head((x1, y1), ang, col, L, hw)

# ------------------------------------------------------------------ icons (centre cx, cy; about 44 px)
def ic_thermo(cx, cy, c):
    add(f'<rect x="{cx - 7}" y="{cy - 23}" width="14" height="33" rx="7" fill="#FFFFFF" stroke="{c}" stroke-width="2.6"/>')
    add(f'<circle cx="{cx}" cy="{cy + 13}" r="10.5" fill="{c}"/><rect x="{cx - 2.6}" y="{cy - 10}" width="5.2" height="20" rx="2.6" fill="{c}"/>')
    add(f'<path d="M{cx + 11},{cy - 16} h7 M{cx + 11},{cy - 8} h5 M{cx + 11},{cy} h7" stroke="{c}" stroke-width="2.4" stroke-linecap="round"/>')
def ic_rain(cx, cy, c):
    add(f'<path d="M{cx - 13},{cy + 1} a9,9 0 0 1 1,-17.8 a12,12 0 0 1 22.5,-2.2 a9.5,9.5 0 0 1 2.5,20 z" fill="{c}"/>')
    add(f'<path d="M{cx - 9},{cy + 8} l-4,10 M{cx + 1},{cy + 8} l-4,10 M{cx + 11},{cy + 8} l-4,10" stroke="{c}" stroke-width="3.2" stroke-linecap="round"/>')
def ic_cal(cx, cy, c):
    add(f'<rect x="{cx - 19}" y="{cy - 16}" width="38" height="35" rx="6" fill="#FFFFFF" stroke="{c}" stroke-width="2.6"/>')
    add(f'<path d="M{cx - 19},{cy - 6} h38" stroke="{c}" stroke-width="2.6"/><path d="M{cx - 9},{cy - 22} v9 M{cx + 9},{cy - 22} v9" stroke="{c}" stroke-width="3" stroke-linecap="round"/>')
    for i in range(3):
        for j in range(2): add(f'<rect x="{cx - 12.5 + i * 9.5}" y="{cy + j * 8.5}" width="5.5" height="5" rx="1" fill="{c}"/>')
def ic_wave(cx, cy, c):
    for k, dy in enumerate((-12, 0, 12)):
        add(f'<path d="M{cx - 21},{cy + dy} q5.25,-8 10.5,0 t10.5,0 t10.5,0 t10.5,0" fill="none" stroke="{c}" stroke-width="3" stroke-linecap="round" opacity="{1 if k != 1 else .65}"/>')
def ic_mosq(cx, cy, c):
    add(f'<g transform="rotate(-28 {cx} {cy})">')
    add(f'<path d="M{cx - 5},{cy - 7} l-13,-9 l-5,-9 M{cx - 6},{cy - 3} l-15,0 l-6,8 M{cx - 5},{cy + 1} l-12,9 l-2,10 M{cx + 5},{cy - 7} l13,-9 l5,-9 M{cx + 6},{cy - 3} l15,0 l6,8 M{cx + 5},{cy + 1} l12,9 l2,10" fill="none" stroke="{c}" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/>')
    add(f'<ellipse cx="{cx - 10}" cy="{cy + 6}" rx="5" ry="13" transform="rotate(32 {cx - 10} {cy + 6})" fill="#FFFFFF" stroke="{c}" stroke-width="1.6" opacity=".95"/>')
    add(f'<ellipse cx="{cx + 10}" cy="{cy + 6}" rx="5" ry="13" transform="rotate(-32 {cx + 10} {cy + 6})" fill="#FFFFFF" stroke="{c}" stroke-width="1.6" opacity=".95"/>')
    add(f'<ellipse cx="{cx}" cy="{cy + 10}" rx="4.2" ry="13.5" fill="{c}"/><ellipse cx="{cx}" cy="{cy - 5}" rx="6" ry="7" fill="{c}"/><circle cx="{cx}" cy="{cy - 14.5}" r="3.8" fill="{c}"/>')
    add(f'<path d="M{cx},{cy - 17} v-9.5" stroke="{c}" stroke-width="2" stroke-linecap="round"/>')
    add(f'<path d="M{cx - 4},{cy + 5} h8 M{cx - 4},{cy + 10.5} h8 M{cx - 3.6},{cy + 16} h7.2" stroke="#FFFFFF" stroke-width="1.7"/>')
    add('</g>')
def ic_virus(cx, cy, c):
    for k in range(8):
        a = k * math.pi / 4 + .2
        add(f'<path d="M{cx + 10 * math.cos(a):.1f},{cy + 10 * math.sin(a):.1f} L{cx + 18.5 * math.cos(a):.1f},{cy + 18.5 * math.sin(a):.1f}" stroke="{c}" stroke-width="2.6"/><circle cx="{cx + 20 * math.cos(a):.1f}" cy="{cy + 20 * math.sin(a):.1f}" r="3.3" fill="{c}"/>')
    add(f'<circle cx="{cx}" cy="{cy}" r="11.5" fill="#FFFFFF" stroke="{c}" stroke-width="2.8"/><circle cx="{cx - 3.5}" cy="{cy - 3}" r="2.4" fill="{c}"/><circle cx="{cx + 4}" cy="{cy + 1}" r="2" fill="{c}"/><circle cx="{cx - 1.5}" cy="{cy + 5}" r="1.7" fill="{c}"/>')
def ic_people(cx, cy, c):
    add(f'<circle cx="{cx + 9}" cy="{cy - 9}" r="6.8" fill="{c}" opacity=".55"/><path d="M{cx - 4},{cy + 17} a13,14 0 0 1 26,0 z" fill="{c}" opacity=".55"/>')
    add(f'<circle cx="{cx - 6}" cy="{cy - 8}" r="8.3" fill="{c}" stroke="#FFFFFF" stroke-width="1.6"/><path d="M{cx - 22},{cy + 20} a16,17 0 0 1 32,0 z" fill="{c}" stroke="#FFFFFF" stroke-width="1.6"/>')

# ------------------------------------------------------------------ layout
TX0, X0 = 26, 190            # tower front face from TX0 to X0; decks start at X0
TD, TT, TB = 270, 436, 1356  # tower depth, top and bottom of front face
TB_ = 44                     # deck thickness
D0 = dict(x0=470, yf=182, Wd=710, D=150)
D1 = dict(x0=X0, yf=540, Wd=1000, D=250)
D2 = dict(x0=X0, yf=864, Wd=1000, D=220)
D3 = dict(x0=X0, yf=1248, Wd=1000, D=270)

# ---- tower (urbanisation): right face, front face, roof
poly([(X0 + 26, TB + 16), (X0 + K * TD + 40, TB - TD + 40), (X0 + K * TD + 26, TB - TD + 16), (TX0 + 30, TB + 22)], '#1B2433', op=.16, extra='filter="url(#blur12)"')
poly([(X0, TT), (X0 + K * TD, TT - TD), (X0 + K * TD, TB - TD), (X0, TB)], 'url(#gtowerR)', ORANGE, 1.6)
g = [f'M{X0},{y} l{K * TD},{-TD}' for y in range(TT + 60, TB, 60)]
add(f'<path d="{" ".join(g)}" stroke="#FFFFFF" stroke-width="1.5" opacity=".38" fill="none"/>')
add(f'<rect x="{TX0}" y="{TT}" width="{X0 - TX0}" height="{TB - TT}" fill="url(#gtowerF)" stroke="{ORANGE}" stroke-width="1.6" stroke-linejoin="round"/>')
ROOF = [(TX0, TT), (X0, TT), (X0 + K * TD, TT - TD), (TX0 + K * TD, TT - TD)]
poly(ROOF, '#FDEDE4', ORANGE, 1.6)
def building(u0, u1, d0, d1, h, win=True, cols=3):
    xa, xb = TX0 + u0 + K * d0, TX0 + u1 + K * d0; yb = TT - d0; dd = d1 - d0
    poly([(xa + 8, yb + 2), (xb + 4, yb + 2), (xb + 40, yb - 18), (xa + 44, yb - 18)], '#7A2D0E', op=.25, extra='filter="url(#blur5)"')
    poly([(xb, yb - h), (xb + K * dd, yb - h - dd), (xb + K * dd, yb - dd), (xb, yb)], '#E69A77', ORANGE_D, 1.1)
    poly([(xa, yb - h), (xb, yb - h), (xb + K * dd, yb - h - dd), (xa + K * dd, yb - h - dd)], '#FFF4EE', ORANGE_D, 1.1)
    add(f'<rect x="{xa:.1f}" y="{yb - h:.1f}" width="{xb - xa:.1f}" height="{h}" fill="#F4B595" stroke="{ORANGE_D}" stroke-width="1.1" stroke-linejoin="round"/>')
    if win:
        wv = (xb - xa - 10) / cols
        for i in range(cols):
            for j in range(int((h - 12) // 19)):
                add(f'<rect x="{xa + 6.5 + i * wv:.1f}" y="{yb - h + 9 + j * 19:.1f}" width="{wv - 5:.1f}" height="10" rx="1.5" fill="#FFFFFF" opacity=".82"/>')
building(64, 128, 172, 236, 150, cols=3)
building(8, 56, 150, 212, 92, cols=2)
building(88, 150, 62, 128, 118, cols=3)
building(14, 72, 36, 100, 66, cols=3)
# tower label (rotated, bottom to top)
cxT = (TX0 + X0) / 2
text(cxT - 14, (TT + TB) / 2 + 60, 'URBANISATION', 44, ORANGE_D, bold=True, anchor='middle', ls=5, rot=(-90, cxT - 14, (TT + TB) / 2 + 60))
text(cxT + 30, (TT + TB) / 2 + 60, 'built-up fraction of province land', 25, '#7A2D0E', anchor='middle', rot=(-90, cxT + 30, (TT + TB) / 2 + 60))
rrect(TX0 + 14, TT + 18, X0 - TX0 - 28, 66, 10, ORANGE, 'none')
text(cxT, TT + 46, 'EFFECT', 23, '#FFFFFF', bold=True, anchor='middle', ls=1.5)
text(cxT, TT + 72, 'MODIFIER', 23, '#FFFFFF', bold=True, anchor='middle', ls=1.5)

# ---- decks
deck(**D0, tb=TB_, top='#F3F5F8', top2='#E3E8EF', band='#64748B', side='#526073', title='SEASON AND ENSO', num=1, gid='g0')
deck(**D1, tb=TB_, top='#EDF4FD', top2='#DCE9FA', band='#2A6FC9', side='#215AA6', title='LOCAL CLIMATE', num=2, gid='g1')
deck(**D2, tb=TB_, top='#ECF7F2', top2='#DAEFE5', band='#2B8A6B', side='#227158', title='MOSQUITO AND VIRUS', num=3, gid='g2')
deck(**D3, tb=TB_, top='#F3EFF9', top2='#E6DEF2', band='#6B579E', side='#584685', title='PEOPLE AND SURVEILLANCE', num=4, gid='g3')

# ---- layer 1: season and ENSO
y0b = D0['yf'] - 42
card(505, y0b, 318, 92, 'ENSO', ['Oceanic Niño Index'], ic_wave, accent='#526073', tint='#E6EAF0')
card(863, y0b, 276, 92, 'Season', ['calendar month'], ic_cal, accent='#526073', tint='#E6EAF0')

# ---- layer 2: local climate; exposure platform (pad)
y1 = D1['yf']
pf, pb, pl, pr_ = 14, 232, X0 + 35, X0 + 600
PAD = [(pl + K * pf, y1 - pf), (pr_ + K * pf, y1 - pf), (pr_ + K * pb, y1 - pb), (pl + K * pb, y1 - pb)]
poly([(p[0] + 10, p[1] + 14) for p in PAD], '#1B2433', op=.18, extra='filter="url(#blur5)"')
poly([PAD[1], PAD[2], (PAD[2][0], PAD[2][1] + 9), (PAD[1][0], PAD[1][1] + 9)], '#7FA8DE', '#5E8FD0', 1)
poly([PAD[0], PAD[1], (PAD[1][0], PAD[1][1] + 9), (PAD[0][0], PAD[0][1] + 9)], '#96BAE9', '#5E8FD0', 1)
poly(PAD, '#C7DCF7', '#5E8FD0', 1.3)
text(388, 374, 'Exposures', 25, '#1C5CAB', bold=True, italic=True, anchor='middle')
TEMP = dict(x=455, yb=y1 - 196, w=286, h=92); RAIN = dict(x=255, yb=y1 - 40, w=286, h=92)
card(**TEMP, title='Temperature', subs=['lags 0–6 months'], icon=ic_thermo, accent='#2A6FC9', tint='#E3EEFC', sw=3)
card(**RAIN, title='Rainfall', subs=['lags 0–6 months'], icon=ic_rain, accent='#2A6FC9', tint='#E3EEFC', sw=3)
HUM = dict(x=944, yb=y1 - 108, w=290, h=138)
ghost(**HUM, title='Humidity', subs=['on the temperature and', 'rainfall pathways;', 'not in main model'])

# ---- layer 3: mosquito and virus (not observed)
y2 = D2['yf']
AED = dict(x=380, yb=y2 - 125, w=358, h=122); VIR = dict(x=814, yb=y2 - 125, w=360, h=122)
card(**AED, title='Aedes mosquitoes', subs=['abundance, survival,', 'biting; breeding sites'], icon=ic_mosq, accent='#227158', tint='#E1F2EA', dash='9 6', sw=2.2, title_italic_first=True)
card(**VIR, title='Viral replication', subs=['in the mosquito', '(extrinsic incubation)'], icon=ic_virus, accent='#227158', tint='#E1F2EA', dash='9 6', sw=2.2)
VC = dict(x=965, yb=y2 - 24, w=202, h=76)
ghost(**VC, title='Reactive', subs=['vector control'])
text(214, y2 - 22, 'Mechanisms (not observed)', 24, '#1F6650', italic=True)

# ---- layer 4: people and surveillance
y3 = D3['yf']
TRA = dict(x=540, yb=y3 - 205, w=284, h=92)
card(**TRA, title='Transmission', subs=['→ infections'], icon=ic_people, accent='#584685', tint='#ECE6F6')
MOB = dict(x=222, yb=y3 - 35, w=326, h=110); IMM = dict(x=612, yb=y3 - 35, w=280, h=82)
ghost(**MOB, title='Human mobility,', subs=['importation, spread from', 'neighbouring provinces'])
ghost(**IMM, title='Population immunity,', subs=['serotype shifts'])
# outcome cylinder
cxY, wY, ybY, hbY, ry = 1110, 256, y3 - 190, 112, 15
add(f'<ellipse cx="{cxY + 26}" cy="{ybY + 6}" rx="{wY / 2 + 8}" ry="{ry + 5}" fill="#1B2433" opacity=".30" filter="url(#blur5)"/>')
add(f'<path d="M{cxY - wY / 2},{ybY - hbY} v{hbY} a{wY / 2},{ry} 0 0 0 {wY},0 v{-hbY} z" fill="url(#gcyl)" stroke="#06172F" stroke-width="1.5"/>')
add(f'<ellipse cx="{cxY}" cy="{ybY - hbY}" rx="{wY / 2}" ry="{ry}" fill="#3F78C4" stroke="#06172F" stroke-width="1.5"/>')
add(f'<path d="M{cxY - wY / 2},{ybY - hbY + 20} a{wY / 2},{ry} 0 0 0 {wY},0" fill="none" stroke="#FFFFFF" stroke-width="1.4" opacity=".35"/>')
text(cxY, ybY - hbY + 55, 'Reported', 27, '#FFFFFF', bold=True, anchor='middle')
text(cxY, ybY - hbY + 85, 'dengue cases', 27, '#FFFFFF', bold=True, anchor='middle')
text(cxY, ybY - hbY + 113, 'outcome', 24, '#CFE0F5', anchor='middle')
YL, YR, YT = cxY - wY / 2, cxY + wY / 2, ybY - hbY - ry

# ------------------------------------------------------------------ arrows
# ribbon: season and ENSO -> exposure platform
rx_ = 826; ya, ybn, yh = D0['yf'] + TB_ + 2, 286, 326
add(f'<polygon points="{pts([(rx_ - 30, ya), (rx_ + 30, ya), (rx_ + 30, ybn), (rx_ + 54, ybn), (rx_, yh), (rx_ - 54, ybn), (rx_ - 30, ybn)])}" fill="url(#gribbon)" stroke="#FFFFFF" stroke-width="2.5" stroke-linejoin="round" opacity=".95"/>')
# climate -> mosquito and virus
arrow([(500, RAIN['yb'] + 2), (500, AED['yb'] - AED['h'] - 16)])
arrow([(590, TEMP['yb'] + 2), (566, AED['yb'] - AED['h'] - 16)])
arrow([(702, TEMP['yb'] + 2), (872, VIR['yb'] - VIR['h'] - 16)])
# mosquito and virus -> transmission
arrow([(598, AED['yb'] + 2), (608, TRA['yb'] - TRA['h'] - 16)])
arrow([(848, VIR['yb'] + 2), (802, TRA['yb'] - TRA['h'] - 16)])
# transmission -> reported cases
ym = TRA['yb'] - TRA['h'] / 2 - 2
arrow([(TRA['x'] + TRA['w'] + 9, ym), (YL - 3, ym)], sw=4.2, L=18, hw=8)
text((TRA['x'] + TRA['w'] + YL) / 2 + 6, ym + 37, 'care-seeking,', 24, SUB, italic=True, anchor='middle', halo='#EDE7F5')
text((TRA['x'] + TRA['w'] + YL) / 2 + 6, ym + 64, 'testing', 24, SUB, italic=True, anchor='middle', halo='#EDE7F5')
# humidity link (no arrowhead)
hy = HUM['yb'] - HUM['h'] / 2
arrow([(pr_ + K * (y1 - hy) + 2, hy), (HUM['x'] - 2, hy)], col=DASH, sw=2.8, dash='9 7', heads=False)
# dashed grey: feedback and unmeasured factors
dk = dict(col=DASH, sw=2.8, dash='9 7', L=14, hw=6)
arrow([(MOB['x'] + 282, MOB['yb'] - MOB['h'] - 2), (TRA['x'] + 52, TRA['yb'] + 14)], **dk)
arrow([(IMM['x'] + 112, IMM['yb'] - IMM['h'] - 2), (TRA['x'] + 212, TRA['yb'] + 14)], **dk)
arrow([(YL + 46, ybY + 12), (IMM['x'] + IMM['w'] - 14, IMM['yb'] - IMM['h'] - 12)], **dk)
text(978, ybY + 84, 'past cases', 24, SUB, italic=True, halo='#EFE9F6')
arrow([(1092, YT - 2), (1092, VC['yb'] + 12)], **dk)
arrow([(VC['x'] - 2, VC['yb'] - 38), (790, VC['yb'] - 38), (776, AED['yb'] - 46), (AED['x'] + AED['w'] + 19, AED['yb'] - 46)], r=22, **dk)
# season -> reported cases (other seasonal pathways)
arrow([(863 + 276 + 8, y0b - 46), (1350, y0b - 46), (1350, 902), (1196, YT + 6)], r=60, **dk)
# orange: urbanisation
ok = dict(col=ORANGE, sw=4.4, L=18, hw=8.5)
od = dict(col=ORANGE, sw=3.2, dash='10 7', L=15, hw=7)
yT = TEMP['yb'] - TEMP['h'] / 2
arrow([(X0 + K * 196 + 2, yT), (TEMP['x'] - 3, yT)], **od)
text(TEMP['x'] - 10, yT - 14, 'urban heat', 24, ORANGE_D, italic=True, anchor='end', halo='#FFFFFF')
yA = AED['yb'] - AED['h'] / 2
arrow([(X0 + K * 125 + 2, yA), (AED['x'] - 3, yA)], **ok)
text(AED['x'] - 8, yA + 33, 'modifies', 24, ORANGE_D, bold=True, italic=True, anchor='end', halo='#E3F3EA')
yTr = TRA['yb'] - TRA['h'] / 2 + 12
arrow([(X0 + K * 205 + 2, yTr), (TRA['x'] - 3, yTr)], **ok)
text((X0 + K * 205 + TRA['x']) / 2, yTr - 14, 'modifies', 24, ORANGE_D, bold=True, italic=True, anchor='middle', halo='#EFE9F6')
yo = y3 + TB_ + 40
arrow([(X0 + 2, yo), (1338, yo), (1338, ybY - 52), (YR + 4, ybY - 52)], r=46, **od)
text(700, yo - 12, 'ascertainment, baseline risk', 24, ORANGE_D, italic=True, anchor='middle', halo='#FFFFFF')

# ------------------------------------------------------------------ right panel: model terms and key
PX, PW, PY = 1392, 396, 30
PH = H - PY - 22
add(f'<rect x="{PX + 8}" y="{PY + 12}" width="{PW}" height="{PH}" rx="16" fill="#1B2433" opacity=".14" filter="url(#blur12)"/>')
rrect(PX, PY, PW, PH, 16, '#FBFBFC', '#B9C0CB', 1.6)
add(f'<path d="M{PX},{PY + 96} v-80 a16,16 0 0 1 16,-16 h{PW - 32} a16,16 0 0 1 16,16 v80 z" fill="#2E3644"/>')
text(PX + 22, PY + 42, 'MODEL TERMS AND', 24, '#FFFFFF', bold=True, ls=1.4)
text(PX + 22, PY + 74, 'SENSITIVITY ANALYSES', 24, '#FFFFFF', bold=True, ls=1.4)
def cube(x, y, c1, c2, c3, s=11):
    poly([(x, y), (x + s, y - s * .55), (x + 2 * s, y), (x + s, y + s * .55)], c1)
    poly([(x, y), (x + s, y + s * .55), (x + s, y + s * .55 + s * 1.15), (x, y + s * 1.15)], c2)
    poly([(x + 2 * s, y), (x + s, y + s * .55), (x + s, y + s * .55 + s * 1.15), (x + 2 * s, y + s * 1.15)], c3)
CB = {'grey': ('#C8D0DB', '#64748B', '#465467'), 'blue': ('#A9CBF5', '#2A6FC9', '#1B4F96'), 'orange': ('#F9C2A6', '#E2591B', '#A63F0F'),
      'purple': ('#CDBFE8', '#6B579E', '#4A3A75'), 'navy': ('#8FB2E3', '#103C76', '#081F40')}
ROWS = [('blue', 'Temperature, rainfall', ['distributed lag non-linear', 'terms, lags 0–6 months']),
        ('grey', 'ENSO', ['Oceanic Niño Index,', 'lags 0–6 months']),
        ('grey', 'Season', ['country harmonics with', 'province-specific deviations']),
        ('orange', 'Urbanisation', ['log built-up fraction ×', 'temperature and rainfall terms']),
        ('purple', 'Country × year effect', ['epidemic years, serotype', 'shifts, reporting changes']),
        ('purple', 'BYM2 spatial effect', ['unmeasured spatially', 'structured factors']),
        ('purple', 'Province AR(1) process', ['month-to-month persistence,', 'extra-Poisson variation']),
        ('navy', 'Population', ['log offset']),
        ('navy', 'Sensitivity analyses', ['excluding 2015–16 or 2020–21;', 'country × month effect;', 'other lags and harmonics'])]
yy = PY + 140
for col, t, ds in ROWS:
    cube(PX + 20, yy - 14, *CB[col])
    text(PX + 54, yy, esc(t), 25, INK, bold=True)
    for i, d in enumerate(ds): text(PX + 54, yy + 29 + 27 * i, esc(d), 24, SUB)
    yy += 29 + 27 * len(ds) + 17
# key
yy += 2
add(f'<path d="M{PX + 20},{yy - 20} h{PW - 40}" stroke="#C9CED6" stroke-width="1.5"/>')
text(PX + 22, yy + 14, 'KEY', 23, '#2E3644', bold=True, ls=1.6)
ky = yy + 50
arrow([(PX + 22, ky - 8), (PX + 92, ky - 8)], halo=False); text(PX + 106, ky, 'pathway', 24, SUB)
ky += 36
arrow([(PX + 22, ky - 8), (PX + 92, ky - 8)], halo=False, **dk); text(PX + 106, ky, 'absorbed by model terms', 24, SUB); text(PX + 106, ky + 27, 'or sensitivity analyses', 24, SUB)
ky += 63
arrow([(PX + 22, ky - 8), (PX + 92, ky - 8)], halo=False, **ok); text(PX + 106, ky, 'effect modification', 24, SUB)
ky += 36
arrow([(PX + 22, ky - 8), (PX + 92, ky - 8)], halo=False, **od); text(PX + 106, ky, 'other urban effects', 24, SUB)
ky += 34
rrect(PX + 24, ky - 20, 64, 30, 7, '#FFFFFF', '#6B7280', 2, '8 6'); text(PX + 106, ky + 3, 'not observed, or not in', 24, SUB); text(PX + 106, ky + 30, 'the main model', 24, SUB)
add('</svg>')
open('out/Figure1_conceptual_framework.svg', 'w', encoding='utf-8').write('\n'.join(o))
print('svg written', W, H, 'key ends', ky + 30, 'panel bottom', PY + PH)
