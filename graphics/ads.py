"""Graphics for the Google Ads study (same palette and mark specs as make.py).
Run: python3 graphics/ads.py   (reads data/google-ads-travel-brands-us-2026-10-02.csv, writes charts/)"""
import csv, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from make import ACCENT, BASE, BRAND, DEEMPH, GRID, INK, INK2, MUTED, ROOT, page, rbar_h, render  # noqa: E402

DATA = ROOT / "data" / "google-ads-travel-brands-us-2026-10-02.csv"
FOOT = "Source: Google Ads Transparency Center · ads shown in the US, 2 Sep–2 Oct 2026 · Google's own count ranges, collected 2 Oct 2026"
NAMES = {"booking.com": "Booking.com", "expedia.com": "Expedia", "airbnb.com": "Airbnb", "hotels.com": "Hotels.com",
         "tripadvisor.com": "Tripadvisor", "kayak.com": "Kayak", "priceline.com": "Priceline", "vrbo.com": "Vrbo"}


def load():
    rows = {}
    for r in csv.DictReader(DATA.open()):
        rows[(r["website"], r["slice"])] = (int(r["ads_low"]), int(r["ads_high"]))
    return rows


def fmt_range(lo, hi):
    def k(n):
        return f"{n / 1000:g}k" if n >= 1000 else str(n)
    return k(lo) if lo == hi else f"{k(lo)}–{k(hi)}"


def bars_chart(name, title, sub, kicker, slice_, highlight, rows):
    data = sorted(((NAMES[w], *rows[(w, slice_)]) for w in NAMES), key=lambda r: -(r[1] + r[2]))
    W, H = 1200, 675
    x0, label_w, plot_w, bar_h, gap = 190, 190, 760, 22, 24
    vmax = max(hi for _, _, hi in data)
    svg = []
    top = 10
    for i, (brand, lo, hi) in enumerate(data):
        y = top + i * (bar_h + gap)
        mid = (lo + hi) / 2
        w = max(2, plot_w * mid / vmax)
        color = ACCENT if brand in highlight else DEEMPH
        svg.append(f'<text x="{x0 - 14}" y="{y + bar_h - 5}" text-anchor="end" font-size="18" fill="{INK}" font-weight="{600 if brand in highlight else 400}">{brand}</text>')
        svg.append(rbar_h(x0, y, w, bar_h, color))
        svg.append(f'<text x="{x0 + w + 10}" y="{y + bar_h - 5}" font-size="17" fill="{INK2}">{fmt_range(lo, hi)}</text>')
    plot_h = top + len(data) * (bar_h + gap)
    svg.append(f'<line x1="{x0}" y1="0" x2="{x0}" y2="{plot_h - gap + 6}" stroke="{BASE}" stroke-width="1"/>')
    body = f'''<div class="card">
<div class="kicker">{kicker}</div>
<h1>{title}</h1>
<div class="sub">{sub}</div>
<div class="plot"><svg width="{x0 + plot_w + 140}" height="{plot_h}" viewBox="0 0 {x0 + plot_w + 140} {plot_h}">{"".join(svg)}</svg></div>
<div class="foot"><span>{FOOT}</span><span class="brand">{BRAND}</span></div></div>'''
    render(name, W, H, page(W, H, body))


def cover(rows):
    b = rows[("booking.com", "all")]
    e = rows[("expedia.com", "all")]
    body = f'''<div class="card" style="padding:48px 60px;flex-direction:row;align-items:center;gap:40px">
<div style="flex:1">
<div class="kicker">Google Ads · 8 travel brands · US · 30 days</div>
<div style="font-size:42px;font-weight:700;line-height:1.12;letter-spacing:-.015em">Booking.com ran <span style="color:{ACCENT}">~40×</span> more Google ads than Expedia. Expedia ran ~90× more video.</div>
<div style="font-size:18px;color:{INK2};margin-top:14px">Distinct ads shown in the US, 2 Sep – 2 Oct 2026.</div></div>
<div style="width:300px;display:flex;flex-direction:column;gap:18px;text-align:right">
<div><div style="font-size:84px;font-weight:700;letter-spacing:-.04em;line-height:.9">~{(b[0] + b[1]) // 2000}k</div><div style="font-size:16px;color:{INK2};margin-top:6px">Booking.com ads (Google: {fmt_range(*b)})</div></div>
<div><div style="font-size:84px;font-weight:700;letter-spacing:-.04em;line-height:.9">~{(e[0] + e[1]) / 2000:g}k</div><div style="font-size:16px;color:{INK2};margin-top:6px">Expedia ads (Google: {fmt_range(*e)})</div></div></div></div>'''
    render("cover-ads", 1000, 420, page(1000, 420, body))


if __name__ == "__main__":
    rows = load()
    bars_chart("ads-volume", "Booking.com ran ~40× more Google ads than Expedia",
               "Distinct ads each brand showed in the US in the last 30 days (Google's count range; bar = midpoint).",
               "Google Ads · 8 travel brands · US · 2 Sep – 2 Oct 2026", "all", {"Booking.com", "Expedia"}, rows)
    bars_chart("ads-video", "…but Expedia ran ~90× more video ads than Booking.com",
               "Distinct video ads shown in the US in the last 30 days. Booking.com: 29. Priceline: none.",
               "Google Ads · video format only · US · 2 Sep – 2 Oct 2026", "format_video", {"Expedia", "Booking.com"}, rows)
    cover(rows)
