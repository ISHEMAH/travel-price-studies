"""Pre-registered out-of-sample test for the hotels study (written 7 Oct 2026, before the 9 Oct pull).

Question (from a reader on DEV): do the three small sites that were cheapest in the 2 Oct data
(Super.com, Traveluro, Vio.com) keep most of the gap to the big brands on a fresh pull?

Fixed before any new data was collected:
- Big brands: Booking.com, Expedia, Hotels.com, Orbitz, Travelocity, CheapTickets, Priceline, Agoda, Trip.com.
- Eligible hotel: at least one big-brand price and three or more smaller sites listed.
- Baseline per hotel: cheapest big-brand price per night.
- Saving of a pick set: (baseline - cheapest listed price among the picks) / baseline, floored at 0;
  a hotel where none of the picks is listed counts as 0 saving (that is part of the test).
- Full gap: the same, using every smaller site.
- "Keeps most of the gap" means the three fixed picks capture more than 50% of the full gap on the new pull.
- Persistence: share of hotels (present on both dates) whose cheapest site is the same on both dates.
  Chance baseline: shuffle site labels within each hotel on the second date, 10,000 times; ties count as a match.

Added 8 Oct 2026, still before the 9 Oct pull (reader follow-up on DEV):
- Full gap = mean of per-hotel percentages (not total savings / total baseline). --dump writes the per-hotel
  baseline, best small-site price and best pick price so any other number can be diffed against it.
- Capture share gets a 95% bootstrap interval (resample hotels with replacement, 10,000 draws, seed 7).
- Verdict per date for the three picks: PASS if the interval's lower bound is above 50%;
  INCONCLUSIVE if only the point estimate is above 50%; FAIL if the point estimate is 50% or below.
- Two dates (9 and 16 Oct): the picks "keep most of the gap" only if both dates PASS. One PASS and one
  FAIL means the picks are not stable and the advice stays "compare all sites" (no fixed shortlist).
  Any other mix is reported as inconclusive.
- Persistence is also reported for hotels where all three picks are listed on both dates.

Run: python3 preregistered_test.py data/hotels-booking-site-prices-2026-10-02.csv [data/<new pull>.csv]
"""
import csv, collections, random, statistics, sys

BIG = ("booking.com", "expedia", "hotels.com", "orbitz", "travelocity", "cheaptickets", "priceline", "agoda", "trip.com")
PICKS = [["Super.com"], ["Super.com", "Traveluro"], ["Super.com", "Traveluro", "Vio.com"]]


def is_big(site):
    s = site.lower()
    return any(s.startswith(b) for b in BIG)


def load(path):
    by = collections.defaultdict(dict)
    for r in csv.DictReader(open(path)):
        try:
            by[(r["city"], r["hotel"])][r["site"]] = float(r["site_price_per_night"])
        except ValueError:
            pass
    return by


def eligible(by):
    out = []
    for h, d in by.items():
        big = [p for s, p in d.items() if is_big(s)]
        small = {s: p for s, p in d.items() if not is_big(s)}
        if big and len(small) >= 3:
            out.append((h, min(big), small))
    return out


def saving(base, small, picks):
    ps = [small[s] for s in picks if s in small]
    return max(0.0, (base - min(ps)) / base) if ps else 0.0


def capture_ci(el, picks, n=10000, seed=7):
    full = [max(0.0, (b - min(sm.values())) / b) for _, b, sm in el]
    pick = [saving(b, sm, picks) for _, b, sm in el]
    rng = random.Random(seed)
    sims = []
    for _ in range(n):
        idx = [rng.randrange(len(el)) for _ in el]
        f = sum(full[i] for i in idx)
        sims.append(sum(pick[i] for i in idx) / f if f else 0.0)
    sims.sort()
    return sims[int(0.025 * n)], sims[int(0.975 * n) - 1]


def report(path, dump=False):
    el = eligible(load(path))
    full = statistics.mean(max(0.0, (b - min(sm.values())) / b) for _, b, sm in el)
    print(f"{path}: {len(el)} eligible hotels, full gap {full*100:.1f}%")
    for picks in PICKS:
        m = statistics.mean(saving(b, sm, picks) for _, b, sm in el)
        lo, hi = capture_ci(el, picks)
        line = f"  {' + '.join(picks)}: {m*100:.1f}% ({m/full*100:.0f}% of the gap, 95% CI {lo*100:.0f}-{hi*100:.0f}%)"
        if picks is PICKS[-1]:
            line += " " + ("PASS" if lo > 0.5 else "INCONCLUSIVE" if m / full > 0.5 else "FAIL")
        print(line)
    if dump:
        out = path.replace(".csv", "-per-hotel.csv")
        with open(out, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["city", "hotel", "big_brand_baseline", "best_small_site", "best_small_price", "gap_pct",
                        "best_pick_price", "pick_saving_pct", "small_sites_listed"])
            for (city, hotel), b, sm in sorted(el):
                best = min(sm, key=sm.get)
                ps = [sm[s] for s in PICKS[-1] if s in sm]
                w.writerow([city, hotel, b, best, sm[best], round(max(0.0, (b - sm[best]) / b) * 100, 2),
                            min(ps) if ps else "", round(saving(b, sm, PICKS[-1]) * 100, 2), len(sm)])
        print(f"  per-hotel dump: {out}")
    return el


def persistence(a, b, n=10000, seed=7, only=None):
    cheapest = lambda d: min(d.values())
    hotels = [h for h in a if h in b and (only is None or only(h))]
    def same(d1, d2):
        c1 = {s for s, p in d1.items() if p == cheapest(d1)}
        c2 = {s for s, p in d2.items() if p == cheapest(d2)}
        return bool(c1 & c2)
    obs = sum(same(a[h], b[h]) for h in hotels) / len(hotels)
    rng = random.Random(seed)
    sims = []
    for _ in range(n):
        k = 0
        for h in hotels:
            sites = list(b[h]); prices = list(b[h].values()); rng.shuffle(prices)
            k += same(a[h], dict(zip(sites, prices)))
        sims.append(k / len(hotels))
    print(f"persistence: same cheapest site on both dates for {obs*100:.0f}% of {len(hotels)} hotels; "
          f"chance baseline {statistics.mean(sims)*100:.0f}%")
    return hotels


if __name__ == "__main__":
    dump = "--dump" in sys.argv
    paths = [a for a in sys.argv[1:] if a != "--dump"]
    first = report(paths[0], dump)
    if len(paths) > 1:
        report(paths[1], dump)
        a, b = load(paths[0]), load(paths[1])
        persistence(a, b)
        print("  restricted to hotels where all three picks are listed on both dates:")
        persistence(a, b, only=lambda h: all(s in a[h] and s in b[h] for s in PICKS[-1]))
