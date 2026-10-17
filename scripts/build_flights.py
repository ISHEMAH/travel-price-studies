"""Google Flights Scraper SUMMARY record -> data/flights-cheapest-fare-by-day-<date>.csv
Run: python3 scripts/build_flights.py SUMMARY.json out.csv
Inputs used for every pull: scripts/flights-input.json"""
import sys,json,csv,datetime
d=json.load(open(sys.argv[1])); out=sys.argv[2]
cols="route,departure_date,weekday,cheapest_one_way_fare,currency,google_price_level,google_typical_low,google_typical_high,itineraries_found".split(",")
def f(v): return "" if v is None else v
rows=[]
for s in d["searches"]:
    dt=datetime.date.fromisoformat(s["departureDate"])
    rows.append([s["route"],s["departureDate"],dt.strftime("%a"),f(s.get("cheapestPrice")),d.get("currency","USD"),f(s.get("priceLevel")),f(s.get("typicalPriceLow")),f(s.get("typicalPriceHigh")),f(s.get("flightsFound"))])
rows.sort(key=lambda r:(r[0],r[1]))
with open(out,"w",newline="") as fh:
    w=csv.writer(fh); w.writerow(cols); w.writerows(rows)
print(len(rows),"rows; failed:",len(d.get("failed") or []), "missing price:",sum(1 for r in rows if r[3]==""))
