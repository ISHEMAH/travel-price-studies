"""Lead-time check for the flights study (reader suggestion on DEV, 2 Oct 2026).

All 150 fares of one pull share a collection day, so an early-November date is both "a Monday" and
"closer to departure". With several pulls of the same routes and dates, weekdays can be compared at the
same lead time (departure date minus collection date).

1. Same route and departure date, different pulls: how did the cheapest fare change as departure got closer?
2. Weekday effect at equal lead time: log(fare) ~ route + weekday + lead-time bucket (7-day buckets), least
   squares. Weekday effects are shown against the average weekday. A 90% interval comes from resampling
   departure dates (all routes and pulls of a date move together), 2,000 draws, seed 7.
Both are run on all of November and on 1-19 November (before the Thanksgiving week).

Run: python3 lead_time.py data/flights-cheapest-fare-by-day-2026-10-02.csv data/flights-cheapest-fare-by-day-2026-10-09.csv ...
"""
import csv, datetime as dt, math, random, re, statistics as st, sys
import numpy as np

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def load(paths):
    rows = []
    for p in paths:
        collected = dt.date.fromisoformat(re.search(r"(\d{4}-\d{2}-\d{2})\.csv$", p).group(1))
        for r in csv.DictReader(open(p)):
            if not r["cheapest_one_way_fare"]:
                continue
            dep = dt.date.fromisoformat(r["departure_date"])
            rows.append({"route": r["route"], "dep": dep, "weekday": r["weekday"], "fare": float(r["cheapest_one_way_fare"]),
                         "collected": collected, "lead": (dep - collected).days})
    return rows


def fit(rows):
    routes = sorted({r["route"] for r in rows})
    buckets = sorted({r["lead"] // 7 for r in rows})
    cols = ["const"] + [f"r:{x}" for x in routes[1:]] + [f"d:{d}" for d in DAYS[1:]] + [f"b:{b}" for b in buckets[1:]]
    X = np.zeros((len(rows), len(cols)))
    y = np.array([math.log(r["fare"]) for r in rows])
    ix = {c: i for i, c in enumerate(cols)}
    for i, r in enumerate(rows):
        X[i, 0] = 1
        if f"r:{r['route']}" in ix: X[i, ix[f"r:{r['route']}"]] = 1
        if f"d:{r['weekday']}" in ix: X[i, ix[f"d:{r['weekday']}"]] = 1
        if f"b:{r['lead'] // 7}" in ix: X[i, ix[f"b:{r['lead'] // 7}"]] = 1
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    raw = np.array([0.0] + [beta[ix[f"d:{d}"]] for d in DAYS[1:]])
    return dict(zip(DAYS, raw - raw.mean()))  # log effect vs the average weekday


def weekday_effects(rows, label, draws=2000, seed=7):
    eff = fit(rows)
    dates = sorted({r["dep"] for r in rows})
    by_date = {d: [r for r in rows if r["dep"] == d] for d in dates}
    rng = random.Random(seed)
    sims = {d: [] for d in DAYS}
    mon_tue = []
    for _ in range(draws):
        sample = [r for _ in dates for r in by_date[dates[rng.randrange(len(dates))]]]
        if len({r["weekday"] for r in sample}) < 7:
            continue
        e = fit(sample)
        for d in DAYS: sims[d].append(e[d])
        mon_tue.append(e["Mon"] - e["Tue"])
    pct = lambda v: (math.exp(v) - 1) * 100
    q = lambda xs, a: sorted(xs)[int(a * len(xs))]
    print(f"\n{label}: {len(rows)} fares, {len(dates)} departure dates, lead time {min(r['lead'] for r in rows)}-{max(r['lead'] for r in rows)} days")
    print("  weekday vs the average weekday, holding route and lead-time bucket fixed (90% interval):")
    for d in DAYS:
        print(f"    {d}: {pct(eff[d]):+5.1f}%  ({pct(q(sims[d], .05)):+.1f} to {pct(q(sims[d], .95)):+.1f})")
    print(f"  Mon minus Tue: {pct(eff['Mon'] - eff['Tue']):+.1f}%  (90% interval {pct(q(mon_tue, .05)):+.1f} to {pct(q(mon_tue, .95)):+.1f})")


def same_flight_changes(rows):
    pulls = sorted({r["collected"] for r in rows})
    key = {(r["route"], r["dep"], r["collected"]): r["fare"] for r in rows}
    print("\nSame route and departure date, later pull vs earlier pull:")
    for a, b in zip(pulls, pulls[1:]):
        ch = [key[(rt, dp, b)] / key[(rt, dp, a)] - 1 for (rt, dp, c) in key if c == a and (rt, dp, b) in key]
        up = sum(x > 0.005 for x in ch); down = sum(x < -0.005 for x in ch)
        print(f"  {a} -> {b} ({(b - a).days} days closer): median change {st.median(ch) * 100:+.1f}%, mean {st.mean(ch) * 100:+.1f}%; "
              f"up {up}, down {down}, same {len(ch) - up - down} of {len(ch)}")
    print("  by route, first -> last pull (median change):")
    for rt in sorted({r["route"] for r in rows}):
        ch = [key[(rt, dp, pulls[-1])] / key[(rt, dp, pulls[0])] - 1 for (r2, dp, c) in key if r2 == rt and c == pulls[0] and (rt, dp, pulls[-1]) in key]
        print(f"    {rt}: {st.median(ch) * 100:+.1f}%")


if __name__ == "__main__":
    rows = load(sys.argv[1:])
    same_flight_changes(rows)
    weekday_effects(rows, "All of November")
    weekday_effects([r for r in rows if r["dep"].day <= 19], "1-19 November (before the Thanksgiving week)")
