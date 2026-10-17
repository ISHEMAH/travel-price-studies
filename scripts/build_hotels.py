"""Google Hotels Scraper dataset items (clean JSON) -> data/hotels-booking-site-prices-<date>.csv
Run: python3 scripts/build_hotels.py items.json out.csv
Inputs used for every pull: scripts/hotels-input.json"""
import sys,json,csv
items=json.load(open(sys.argv[1])); out=sys.argv[2]
cols="city,hotel,hotel_class,guest_rating,review_count,google_lead_price_per_night,site,site_price_per_night,site_total_price,check_in,check_out,nights,adults,currency,collected_utc".split(",")
def f(v): return "" if v is None else v
n=0
with open(out,"w",newline="") as fh:
    w=csv.writer(fh); w.writerow(cols)
    for it in items:
        for v in it.get("vendorPrices") or []:
            w.writerow([it.get("searchedPlace"),it.get("name"),f(it.get("hotelClass")),f(it.get("rating")),f(it.get("reviewCount")),f(it.get("pricePerNight")),v.get("vendor"),f(v.get("pricePerNight")),f(v.get("totalPrice")),it.get("checkIn"),it.get("checkOut"),it.get("nights"),it.get("adults"),it.get("currency"),it.get("scrapedAt")]); n+=1
print(len(items),"hotels",n,"rows")
