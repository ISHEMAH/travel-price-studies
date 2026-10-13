# Google Trends: website vs plain fetch vs scraper (13 October 2026)

Data behind the DEV post "Google's Trends API is still invite-only. I tested what the alternatives return".

- `website-compare-series-and-python-lists.json`: the 53-week series for python, javascript, rust, typescript, golang (US, past 12 months) as loaded by trends.google.com, plus the python related-query lists from the first page load.
- `browser-fetch-scraper-top-queries.json`: top related queries for all five terms from a `fetch()` in the same tab (Google tagged it `USER_TYPE_SCRAPER`).
- `related-queries-python-lists.json`: the five python top-25 pulls compared in the post (`legit1`, `legit2` = two website loads; `scraper1`, `scraper2` = two plain fetches; the Actor list is in the run file).
- `actor-compare-run-kzNBW4s7b2i2eosO5.json`, `actor-single-run-Hd9DrkEhN7iTkhX23.json`: full output of the Apify Actor runs.
- `overlap.py`: reproduces the overlap table.
