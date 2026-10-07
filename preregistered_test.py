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


def report(path):
    el = eligible(load(path))
    full = statistics.mean(max(0.0, (b - min(sm.values())) / b) for _, b, sm in el)
    print(f"{path}: {len(el)} eligible hotels, full gap {full*100:.1f}%")
    for picks in PICKS:
        m = statistics.mean(saving(b, sm, picks) for _, b, sm in el)
        print(f"  {' + '.join(picks)}: {m*100:.1f}% ({m/full*100:.0f}% of the gap)")
    return el


def persistence(a, b, n=10000, seed=7):
    cheapest = lambda d: min(d.values())
    hotels = [h for h in a if h in b]
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


if __name__ == "__main__":
    first = report(sys.argv[1])
    if len(sys.argv) > 2:
        report(sys.argv[2])
        persistence(load(sys.argv[1]), load(sys.argv[2]))
