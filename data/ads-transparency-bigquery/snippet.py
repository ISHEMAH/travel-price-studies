import os
from apify_client import ApifyClient

EEA_TR = set("AT BE BG HR CY CZ DK EE FI FR DE GR HU IE IT LV LT LU MT NL "
             "PL PT RO SK SI ES SE IS LI NO TR".split())

client = ApifyClient(os.environ["APIFY_TOKEN"])

run = client.actor("kuezi/google-ads-transparency-scraper").call(logger=None, run_input={
    "searchTargets": ["shopify.com"],
    "country": "anywhere",
    "lastDays": 30,
    "maxAdsPerTarget": 50,
    "includeAdDetails": True,   # adds shownInCountries, text, video IDs
})

inside, outside = 0, []
for ad in client.dataset(run.default_dataset_id).iterate_items():
    countries = {c["country"] for c in ad["shownInCountries"]}
    if countries & EEA_TR:
        inside += 1
    else:
        outside.append((ad["format"], sorted(countries)))

print(f"shown in the EEA or Turkey: {inside}")
print(f"never shown there:          {len(outside)}")
for fmt, countries in outside[:6]:
    print(f"  {fmt:5} {', '.join(countries[:8])}")
print(run.status_message)
