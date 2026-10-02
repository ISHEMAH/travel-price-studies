"""Render the study graphics as HTML (system sans, validated palette) -> PNG via headless Chrome at 2x.
Run: python3 graphics/make.py   (outputs to charts/)
Palette & mark specs follow the dataviz reference instance: accent #2a78d6, red pole #e34948, hairline grid,
<=24px bars with 4px rounded data-ends, labels in text ink (never the series colour)."""
import csv, pathlib, statistics as st, subprocess
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "charts"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

INK, INK2, MUTED, GRID, BASE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
SURFACE, PLANE, ACCENT, RED, DEEMPH = "#fcfcfb", "#f4f3ef", "#2a78d6", "#e34948", "#cfcec7"

CSS = f"""
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:100%;height:100%}}
body{{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;background:{PLANE};color:{INK};-webkit-font-smoothing:antialiased}}
.card{{position:absolute;inset:0;background:{SURFACE};padding:52px 60px 40px;display:flex;flex-direction:column}}
.kicker{{font-size:15px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:{ACCENT};margin-bottom:12px}}
h1{{font-size:38px;line-height:1.15;font-weight:700;letter-spacing:-.015em;max-width:980px}}
.sub{{font-size:19px;line-height:1.4;color:{INK2};margin-top:12px;max-width:1000px}}
.plot{{flex:1;position:relative;margin-top:20px}}
.foot{{display:flex;justify-content:space-between;align-items:flex-end;font-size:14px;color:{MUTED};border-top:1px solid {GRID};padding-top:14px;gap:24px}}
.brand{{font-weight:600;color:{INK2}}}
.legend{{display:flex;gap:22px;font-size:15px;color:{INK2};margin-top:14px}}
.legend i{{display:inline-block;width:12px;height:12px;border-radius:50%;margin-right:7px;vertical-align:-1px}}
text{{font-family:system-ui,-apple-system,"Segoe UI",sans-serif}}
"""
FOOT_SRC_H = "Source: Google Hotels price lists · 12–15 Nov 2026 stay, 2 adults, USD · collected 2 Oct 2026"
FOOT_SRC_F = "Source: Google Flights · cheapest one-way economy fare, 1 adult, USD · prices seen 2 Oct 2026"
BRAND = "travel-price-studies · open data on GitHub"


def page(w, h, body):
    return f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body style="width:{w}px;height:{h}px;position:relative">{body}</body></html>'


def render(name, w, h, html):
    src = OUT / f"_{name}.html"
    src.write_text(html)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
                    f"--window-size={w},{h}", f"--screenshot={OUT / (name + '.png')}", src.as_uri()],
                   check=True, capture_output=True)
    src.unlink()
    print("rendered", name)


def rbar_h(x0, y, w, h, color):
    """Horizontal bar: square at the baseline (x0), 4px rounded data-end."""
    r = min(4, w / 2)
    return (f'<path d="M{x0},{y} H{x0 + w - r} Q{x0 + w},{y} {x0 + w},{y + r} V{y + h - r} Q{x0 + w},{y + h} {x0 + w - r},{y + h} '
            f'H{x0} Z" fill="{color}"/>')


def rbar_v(x, base, w, h, color):
    """Vertical bar growing up (h>0) or down (h<0) from the baseline; rounded at the data end only."""
    r = min(4, abs(h) / 2)
    if h >= 0:
        top = base - h
        return f'<path d="M{x},{base} V{top + r} Q{x},{top} {x + r},{top} H{x + w - r} Q{x + w},{top} {x + w},{top + r} V{base} Z" fill="{color}"/>'
    bot = base - h
    return f'<path d="M{x},{base} V{bot - r} Q{x},{bot} {x + r},{bot} H{x + w - r} Q{x + w},{bot} {x + w},{bot - r} V{base} Z" fill="{color}"/>'


# ---------------- data ----------------
rows = list(csv.DictReader(open(ROOT / "data/hotels-booking-site-prices-2026-10-02.csv")))
by_hotel = defaultdict(dict)
for r in rows:
    if r["site_total_price"]:
        by_hotel[(r["city"], r["hotel"])][r["site"]] = float(r["site_total_price"])
hotels = {k: v for k, v in by_hotel.items() if len(v) >= 2}
prem = defaultdict(list)
for prices in hotels.values():
    low = min(prices.values())
    for s, p in prices.items():
        prem[s].append((p - low) / low * 100)
med = {s: st.median(v) for s, v in prem.items() if len(v) >= 30}

fl = list(csv.DictReader(open(ROOT / "data/flights-cheapest-fare-by-day-2026-10-02.csv")))
route_med = {r: st.median(float(x["cheapest_one_way_fare"]) for x in fl if x["route"] == r) for r in {x["route"] for x in fl}}
wd = defaultdict(list)
for x in fl:
    wd[x["weekday"]].append(float(x["cheapest_one_way_fare"]) / route_med[x["route"]])
WEEK = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
widx = {d: (st.mean(wd[d]) - 1) * 100 for d in WEEK}


# ---------------- 1. hotels: emphasis bars ----------------
def hotels_chart():
    sites = [("Cheapest site", 0.0), ("Super.com", med["Super.com"]), ("Kiwi.com", med["Kiwi.com"]), ("Trip.com", med["Trip.com"]),
             ("Hotels.com", med["Hotels.com"]), ("Expedia", med["Expedia.com"]), ("Priceline", med["Priceline"]), ("Booking.com", med["Booking.com"])]
    big = {"Hotels.com", "Expedia", "Priceline", "Booking.com"}
    W, H = 1080, 380
    left, right, top = 150, 90, 6
    rowh = (H - top - 34) / len(sites)
    bar = 22
    xmax = 140
    sx = lambda v: left + (W - left - right) * v / xmax
    g = []
    for t in range(0, xmax + 1, 20):
        x = sx(t)
        g.append(f'<line x1="{x}" x2="{x}" y1="{top}" y2="{H - 30}" stroke="{GRID}" stroke-width="1"/>')
        g.append(f'<text x="{x}" y="{H - 8}" font-size="14" fill="{MUTED}" text-anchor="middle">${t}</text>')
    for i, (name, p) in enumerate(sites):
        y = top + i * rowh + (rowh - bar) / 2
        price = 100 + p
        color = ACCENT if name in big else DEEMPH
        g.append(f'<text x="{left - 14}" y="{y + bar / 2 + 6}" font-size="18" fill="{INK}" text-anchor="end" font-weight="{600 if name in big else 400}">{name}</text>')
        g.append(rbar_h(sx(0), y, sx(price) - sx(0), bar, color))
        label = f"${price:.0f}" + (f'<tspan fill="{INK2}" font-weight="400">  +{p:.0f}%</tspan>' if p else f'<tspan fill="{INK2}" font-weight="400">  baseline</tspan>')
        g.append(f'<text x="{sx(price) + 10}" y="{y + bar / 2 + 6}" font-size="17" font-weight="700" fill="{INK}">{label}</text>')
    g.append(f'<line x1="{sx(0)}" x2="{sx(0)}" y1="{top}" y2="{H - 30}" stroke="{BASE}" stroke-width="1"/>')
    svg = f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}">{"".join(g)}</svg>'
    body = f'''<div class="card"><div class="kicker">Hotel price study · 47 hotels · 5 cities</div>
<h1>Same room, same dates: the big booking sites cost about 26% more than the cheapest one</h1>
<div class="sub">What you'd pay for a stay that costs <b>$100</b> on the cheapest site (median across hotels). Blue = the four biggest brands.</div>
<div class="plot">{svg}</div>
<div class="foot"><span class="brand">{BRAND}</span><span>{FOOT_SRC_H}</span></div></div>'''
    render("hotels-premium", 1200, 675, page(1200, 675, body))


# ---------------- 2. hotels: stat tiles ----------------
def hotels_facts():
    tile = lambda big, small, desc: f'''<div style="flex:1;background:{PLANE};border-radius:14px;padding:34px 30px 36px">
<div style="font-size:72px;font-weight:700;letter-spacing:-.02em;line-height:1">{big}<span style="font-size:30px;font-weight:600;color:{INK2}"> {small}</span></div>
<div style="font-size:21px;line-height:1.42;color:{INK2};margin-top:18px">{desc}</div></div>'''
    body = f'''<div class="card"><div class="kicker">Hotel price study · 47 hotels · 24 booking sites each</div>
<h1>Three things worth knowing before you book a hotel</h1>
<div style="display:flex;gap:22px;margin:auto 0">
{tile("37", "of 45", "hotels where <b>Expedia, Hotels.com, Orbitz, Travelocity and CheapTickets</b> showed the exact same price. Same company, one check.")}
{tile("4", "of 34", "times the <b>hotel's own website</b> was the cheapest place to book it.")}
{tile("67%", "", "median gap between the <b>cheapest and the priciest site</b> for the very same room. In Bangkok it was 116%.")}
</div>
<div class="foot"><span class="brand">{BRAND}</span><span>{FOOT_SRC_H}</span></div></div>'''
    render("hotels-facts", 1200, 675, page(1200, 675, body))


# ---------------- 3. hotels: DEV cover ----------------
def hotels_cover():
    body = f'''<div class="card" style="padding:44px 56px;flex-direction:row;align-items:center;gap:44px">
<div style="flex:1">
<div class="kicker">47 hotels · 24 booking sites · open data</div>
<div style="font-size:40px;font-weight:700;line-height:1.12;letter-spacing:-.015em">Booking.com, Expedia and Hotels.com cost <span style="color:{ACCENT}">~26% more</span> than the cheapest site</div>
<div style="font-size:18px;color:{INK2};margin-top:14px">Same hotel, same dates. Here's who was actually cheapest.</div></div>
<div style="width:300px;text-align:right">
<div style="font-size:120px;font-weight:700;letter-spacing:-.04em;line-height:.9;color:{INK}">+26%</div>
<div style="font-size:16px;color:{INK2};margin-top:12px">median premium of the big brands<br>over the cheapest offer</div></div></div>'''
    render("cover-hotels", 1000, 420, page(1000, 420, body))


# ---------------- 4. flights: diverging columns ----------------
def flights_weekday():
    W, H = 1080, 400
    left, right, top, bottom = 50, 20, 30, 40
    vmax = 24
    base = top + (H - top - bottom) * vmax / (vmax + 10)
    sy = lambda v: (H - top - bottom) * v / (vmax + 10)
    n = len(WEEK)
    band = (W - left - right) / n
    bw = 24 * 2.6
    g = []
    for t in (-10, -5, 5, 10, 15, 20):
        y = base - sy(t)
        g.append(f'<line x1="{left}" x2="{W - right}" y1="{y}" y2="{y}" stroke="{GRID}" stroke-width="1"/>')
        g.append(f'<text x="{left - 10}" y="{y + 5}" font-size="13" fill="{MUTED}" text-anchor="end">{t:+d}%</text>')
    for i, d in enumerate(WEEK):
        v = widx[d]
        x = left + i * band + (band - bw) / 2
        color = ACCENT if v < 0 else RED
        g.append(rbar_v(x, base, bw, sy(v), color))
        ly = base - sy(v) - 12 if v >= 0 else base - sy(v) + 26
        g.append(f'<text x="{x + bw / 2}" y="{ly}" font-size="20" font-weight="700" fill="{INK}" text-anchor="middle">{v:+.0f}%</text>')
        g.append(f'<text x="{x + bw / 2}" y="{H - 10}" font-size="18" fill="{INK}" text-anchor="middle" font-weight="{700 if d in ("Tue", "Fri") else 400}">{d}</text>')
    g.append(f'<line x1="{left}" x2="{W - right}" y1="{base}" y2="{base}" stroke="{INK2}" stroke-width="1.5"/>')
    g.append(f'<text x="{left + 6}" y="{base - 10}" font-size="14" fill="{INK2}" text-anchor="start">typical price for the route</text>')
    svg = f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}">{"".join(g)}</svg>'
    body = f'''<div class="card"><div class="kicker">Flight price study · 5 routes · 150 searches</div>
<h1>Tuesday was cheapest to fly. Friday cost 20% more.</h1>
<div class="sub">Cheapest fare by departure weekday vs each route's typical November price · <span style="color:{ACCENT};font-weight:600">cheaper</span> / <span style="color:#c43a3a;font-weight:600">pricier</span></div>
<div class="plot">{svg}</div>
<div class="foot"><span class="brand">{BRAND}</span><span>{FOOT_SRC_F}</span></div></div>'''
    render("flights-weekday", 1200, 675, page(1200, 675, body))


# ---------------- 5. flights: dumbbell per route ----------------
def flights_routes():
    names = {"JFK-LAX": "New York → Los Angeles", "LHR-JFK": "London → New York", "ORD-MIA": "Chicago → Miami",
             "SFO-HNL": "San Francisco → Honolulu", "LAX-NRT": "Los Angeles → Tokyo"}
    data = []
    for r in names:
        ps = [float(x["cheapest_one_way_fare"]) for x in fl if x["route"] == r]
        data.append((r, min(ps), max(ps)))
    data.sort(key=lambda d: d[2] / d[1], reverse=True)
    W, H = 1080, 360
    left, right, top = 270, 170, 10
    rowh = (H - top - 34) / len(data)
    xmax = 900
    sx = lambda v: left + (W - left - right) * v / xmax
    g = []
    for t in range(0, xmax + 1, 150):
        x = sx(t)
        g.append(f'<line x1="{x}" x2="{x}" y1="{top}" y2="{H - 30}" stroke="{GRID}" stroke-width="1"/>')
        g.append(f'<text x="{x}" y="{H - 8}" font-size="13" fill="{MUTED}" text-anchor="middle">${t}</text>')
    for i, (r, lo, hi) in enumerate(data):
        y = top + i * rowh + rowh / 2
        g.append(f'<text x="{left - 18}" y="{y + 6}" font-size="18" fill="{INK}" text-anchor="end">{names[r]}</text>')
        g.append(f'<line x1="{sx(lo)}" x2="{sx(hi)}" y1="{y}" y2="{y}" stroke="{BASE}" stroke-width="3" stroke-linecap="round"/>')
        for v, c in ((lo, ACCENT), (hi, RED)):
            g.append(f'<circle cx="{sx(v)}" cy="{y}" r="9" fill="{c}" stroke="{SURFACE}" stroke-width="2"/>')
        g.append(f'<text x="{sx(hi) + 18}" y="{y + 6}" font-size="17" font-weight="700" fill="{INK}">${lo:.0f} → ${hi:.0f}<tspan font-weight="400" fill="{INK2}">  ×{hi / lo:.1f}</tspan></text>')
    svg = f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}">{"".join(g)}</svg>'
    body = f'''<div class="card"><div class="kicker">Flight price study · every November departure day</div>
<h1>Picking the wrong day cost up to 2.7× on the same route</h1>
<div class="legend"><span><i style="background:{ACCENT}"></i>cheapest day in November</span><span><i style="background:{RED}"></i>priciest day in November</span></div>
<div class="plot">{svg}</div>
<div class="foot"><span class="brand">{BRAND}</span><span>{FOOT_SRC_F}</span></div></div>'''
    render("flights-routes", 1200, 675, page(1200, 675, body))


# ---------------- 6. flights: DEV cover ----------------
def flights_cover():
    body = f'''<div class="card" style="padding:44px 56px;flex-direction:row;align-items:center;gap:40px">
<div style="flex:1">
<div class="kicker">150 flight searches · 5 routes · November 2026</div>
<div style="font-size:42px;font-weight:700;line-height:1.12;letter-spacing:-.015em">The cheapest day to fly was <span style="color:{ACCENT}">Tuesday</span>. The priciest was <span style="color:#c43a3a">Friday</span>.</div>
<div style="font-size:18px;color:{INK2};margin-top:14px">Fare vs the route's typical price, by departure weekday.</div></div>
<div style="width:280px;display:flex;flex-direction:column;gap:18px;text-align:right">
<div><div style="font-size:84px;font-weight:700;letter-spacing:-.04em;line-height:.9">−5%</div><div style="font-size:16px;color:{INK2};margin-top:6px">Tuesday</div></div>
<div><div style="font-size:84px;font-weight:700;letter-spacing:-.04em;line-height:.9">+20%</div><div style="font-size:16px;color:{INK2};margin-top:6px">Friday</div></div></div></div>'''
    render("cover-flights", 1000, 420, page(1000, 420, body))


if __name__ == "__main__":
    hotels_chart(); hotels_facts(); hotels_cover(); flights_weekday(); flights_routes(); flights_cover()
