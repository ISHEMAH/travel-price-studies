"""Reproduce every number in README.md from the CSVs in data/.  Run: python3 analysis.py"""
import csv
import statistics as st
from collections import Counter, defaultdict

# ---------- Hotels: booking-site premiums ----------
rows = list(csv.DictReader(open("data/hotels-booking-site-prices-2026-10-02.csv")))
by_hotel = defaultdict(dict)
for r in rows:
    if r["site_total_price"]:
        by_hotel[(r["city"], r["hotel"])][r["site"]] = float(r["site_total_price"])
hotels = {k: v for k, v in by_hotel.items() if len(v) >= 2}
premium, cheapest, spreads = defaultdict(list), Counter(), defaultdict(list)
for (city, _), prices in hotels.items():
    low = min(prices.values())
    spreads[city].append((max(prices.values()) - low) / low * 100)
    for site, p in prices.items():
        premium[site].append((p - low) / low * 100)
        if p == low:
            cheapest[site] += 1
print(f"Hotels analysed: {len(hotels)}  |  sites per hotel: {st.mean(len(v) for v in hotels.values()):.1f}")
print("Median premium over the cheapest site (sites listed on 30+ hotels):")
for site, ps in sorted(premium.items(), key=lambda kv: st.median(kv[1])):
    if len(ps) >= 30:
        print(f"  {site:<20} +{st.median(ps):5.1f}%   on {len(ps)} hotels, cheapest on {cheapest[site]}")
print("Median cheapest→priciest spread by city:", {c: round(st.median(v), 1) for c, v in spreads.items()})
expedia_group = ["Expedia.com", "Hotels.com", "Travelocity.com", "Orbitz.com", "CheapTickets.com"]
eg = [[p[s] for s in expedia_group if s in p] for p in hotels.values()]
eg = [x for x in eg if len(x) >= 3]
print(f"Expedia Group brands identical price: {sum(1 for x in eg if max(x) - min(x) <= 1)} of {len(eg)} hotels")

# ---------- Flights: cheapest day ----------
fl = list(csv.DictReader(open("data/flights-cheapest-fare-by-day-2026-10-02.csv")))
route_median = {r: st.median(float(x["cheapest_one_way_fare"]) for x in fl if x["route"] == r) for r in {x["route"] for x in fl}}
idx = defaultdict(list)
for x in fl:
    idx[x["weekday"]].append(float(x["cheapest_one_way_fare"]) / route_median[x["route"]])
print("\nCheapest fare by weekday vs route median:")
for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
    print(f"  {d}: {(st.mean(idx[d]) - 1) * 100:+.1f}%")
for r in sorted(route_median):
    prices = [(float(x["cheapest_one_way_fare"]), x["departure_date"]) for x in fl if x["route"] == r]
    lo, hi = min(prices), max(prices)
    print(f"  {r}: ${lo[0]:.0f} – ${hi[0]:.0f} (priciest {hi[1]}), spread +{(hi[0] - lo[0]) / lo[0] * 100:.0f}%")
