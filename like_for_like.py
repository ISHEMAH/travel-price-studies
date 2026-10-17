"""Like-for-like check (reader question on DEV, 16 Oct 2026): is the change in the full gap between pulls
caused by Google's top-10 rotating, or did prices move? Recomputes the pre-registered numbers on only
the hotels that are eligible on every date given. Same definitions as preregistered_test.py.

Run: python3 like_for_like.py data/hotels-booking-site-prices-2026-10-02.csv data/hotels-booking-site-prices-2026-10-09.csv [more pulls]
"""
import statistics, sys
from preregistered_test import load, eligible, saving, capture_ci, PICKS

paths = sys.argv[1:]
pulls = {p: {h: (b, sm) for h, b, sm in eligible(load(p))} for p in paths}
common = set.intersection(*(set(d) for d in pulls.values()))
print(f"hotels eligible on all {len(paths)} dates: {len(common)}")
for p, d in pulls.items():
    el = [(h, *d[h]) for h in sorted(common)]
    full = statistics.mean(max(0.0, (b - min(sm.values())) / b) for _, b, sm in el)
    picks = statistics.mean(saving(b, sm, PICKS[-1]) for _, b, sm in el)
    lo, hi = capture_ci(el, PICKS[-1])
    print(f"  {p}: full gap {full*100:.1f}%, three picks {picks*100:.1f}% ({picks/full*100:.0f}% of the gap, 95% CI {lo*100:.0f}-{hi*100:.0f}%)")
