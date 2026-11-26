import os
from apify_client import ApifyClient

# What the course keeps in a Google Sheet: destination and the price that counts as a deal
targets = {"CDG": 60, "FRA": 60, "IST": 90, "JFK": 300, "HND": 600}  # GBP, one-way

client = ApifyClient(os.environ["APIFY_TOKEN"])
run = client.actor("kuezi/google-flights-scraper").call(logger=None, run_input={
    "routes": [f"LHR-{iata}" for iata in targets],
    "departureDate": "2027-01-11",
    "scanDays": 7,                 # 11 Jan plus the next 7 days
    "maxFlightsPerSearch": 1,      # we only want the price, not 30 itineraries
    "currency": "GBP",
    "country": "gb",
})

summary = client.key_value_store(run.default_key_value_store_id).get_record("SUMMARY")["value"]
for r in summary["cheapestByRoute"]:
    to = r["route"].split("-")[1]
    flag = "DEAL" if r["cheapestPrice"] <= targets[to] else "    "
    print(f'{flag} {r["route"]}: £{r["cheapestPrice"]} on {r["cheapestDates"][0]} '
          f'(median £{r["medianPrice"]}, {r["daysScanned"]} days)')

print(len(summary["searches"]), "searches,", run.status)
