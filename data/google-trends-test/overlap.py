"""Overlap of the python related-query lists pulled on 13 Oct 2026 (website x2, plain fetch x2, Actor).
cd data/google-trends-test && python3 overlap.py"""
import itertools, json
L = json.load(open("related-queries-python-lists.json"))
actor = json.load(open("actor-compare-run-kzNBW4s7b2i2eosO5.json"))[0]["relatedQueries"]
L["actor"] = [q["query"] for q in actor["top"]]
names = ["legit1", "legit2", "scraper1", "scraper2", "actor"]
for a, b in itertools.combinations(names, 2):
    print(f"{a:9s} vs {b:9s}: top25 shared {len(set(L[a]) & set(L[b])):2d}, top10 shared {len(set(L[a][:10]) & set(L[b][:10]))}")
print("rising, website load 1 vs load 2:", len(set(L["legit1_rising"]) & set(L["legit2_rising"])))
