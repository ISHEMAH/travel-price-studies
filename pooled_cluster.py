"""Pooled capture share over the out-of-sample pulls, with a hotel-level (cluster) bootstrap.

Added 28 Oct 2026 after a reader pointed out on DEV that the same hotels appear in several pulls,
so a pooled interval must resample hotels, not hotel-date rows. Not part of the pre-registered rule:
the two-date verdict (9 Oct PASS, 17 Oct INCONCLUSIVE) stands. This is a robustness check only.

Pooled capture share = sum of pick savings / sum of full gaps over every eligible hotel-date row.
Cluster bootstrap: draw hotels with replacement and take all of each drawn hotel's rows (10,000 draws, seed 7).
The row bootstrap (rows treated as independent) is printed next to it for comparison.

Run: python3 pooled_cluster.py data/hotels-booking-site-prices-2026-10-09.csv data/hotels-booking-site-prices-2026-10-17.csv
"""
import collections, random, sys

from preregistered_test import PICKS, eligible, load, saving


def ci(groups, n=10000, seed=7):
    rng = random.Random(seed)
    sims = []
    for _ in range(n):
        f = p = 0.0
        for _ in groups:
            for full, pick in groups[rng.randrange(len(groups))]:
                f += full; p += pick
        sims.append(p / f if f else 0.0)
    sims.sort()
    return sims[int(0.025 * n)], sims[int(0.975 * n) - 1]


rows = collections.defaultdict(list)
for path in sys.argv[1:]:
    for h, b, sm in eligible(load(path)):
        rows[h].append((max(0.0, (b - min(sm.values())) / b), saving(b, sm, PICKS[-1])))

flat = [r for rs in rows.values() for r in rs]
share = sum(p for _, p in flat) / sum(f for f, _ in flat)
repeated = sum(len(rs) > 1 for rs in rows.values())
print(f"{len(flat)} hotel-date rows, {len(rows)} distinct hotels ({repeated} in more than one pull)")
print(f"pooled capture share of the three picks: {share*100:.0f}%")
lo, hi = ci(list(rows.values()))
print(f"  cluster bootstrap (resample hotels): 95% CI {lo*100:.0f}-{hi*100:.0f}%")
lo, hi = ci([[r] for r in flat])
print(f"  row bootstrap (rows as independent):  95% CI {lo*100:.0f}-{hi*100:.0f}%")
