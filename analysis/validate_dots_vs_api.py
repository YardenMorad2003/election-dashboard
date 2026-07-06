# -*- coding: utf-8 -*-
"""
validate_dots_vs_api.py — independent check of the venue-dots layer against the
official data.gov.il election API (dataset votes-knesset, per-ballot resources).

Per era: sum כשרים per settlement from the LIVE API and compare against
  (a) the local ballot-CSV totals (should match ~exactly — pipeline integrity:
      dropped rows, meta-column filters, the K18 בז''ב class of bug), and
  (b) the votes actually PLACED on the map (venue_dots) — placement coverage,
      plus the worst-covered cities.

Double/external envelopes (semel 0/875 old eras, 9999/99999 modern) are excluded
on both sides, matching the builds. K17 has no settlement code in the API
resource → national totals only, and its API total INCLUDES ~184k double
envelopes that cannot be filtered — a Δ of that size there is expected.

Run: python -X utf8 analysis/validate_dots_vs_api.py [25 24 ...]
"""
import json, os, sys, urllib.request, urllib.parse, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "datagov-external-client"}

BALLOT_RESOURCES = {   # dataset votes-knesset, per-קלפיות resources (verified 2026-07-06)
    "16": "498b48e9-5af6-474d-b7a4-5ac1e21d3a08",
    "17": "70f8bc93-8d98-4c20-ad7c-768af713f1c5",
    "18": "840edb33-90ac-4176-8ad9-4cdcb8e5caa5",
    "19": "432d3185-545a-41d9-8c72-d10ee515919c",
    "20": "c3db5581-f48d-45fc-b221-e7635e940c41",
    "21": "f79f9ba5-fe12-4b90-96cc-916f1b7c1c34",
    "22": "22f3a195-3a79-436c-be23-cb606bc7b398",
    "23": "3b9e911a-2e90-4587-b209-84171664056b",
    "24": "419be3b0-fd30-455a-afc0-034ec36be990",
    "25": "cc223336-07bc-485d-b160-62df92967c0a",
}


def api_rows(resource_id):
    out, offset = [], 0
    while True:
        q = urllib.parse.urlencode({"resource_id": resource_id, "limit": 32000, "offset": offset})
        req = urllib.request.Request(f"https://data.gov.il/api/3/action/datastore_search?{q}", headers=UA)
        res = json.load(urllib.request.urlopen(req, timeout=120))["result"]
        out.extend(res["records"])
        offset += len(res["records"])
        if offset >= res.get("total", 0) or not res["records"]:
            return out


def iv(x):
    try:
        return int(float(x or 0))
    except (ValueError, TypeError):
        return 0


def check_year(yr):
    rows = api_rows(BALLOT_RESOURCES[yr])
    flds = rows[0].keys() if rows else []
    koshcol = next((c for c in flds if "כשר" in str(c)), None)
    semcol = next((c for c in flds if "סמל" in str(c) and "ישוב" in str(c) and "בחירות" not in str(c)), None)
    namecol = next((c for c in flds if "שם ישוב" in str(c)), None)

    api_city = collections.Counter()
    api_names = {}
    api_total = 0
    for r in rows:
        k = iv(r.get(koshcol))
        sem = iv(r.get(semcol)) if semcol else None
        if sem in (0, 875, 9999, 99999):   # double/external envelopes — excluded in the builds too
            continue
        api_total += k
        if sem is not None:
            api_city[sem] += k
            if namecol and sem not in api_names:
                api_names[sem] = str(r.get(namecol) or "").strip()

    vd = json.load(open(os.path.join(ROOT, "data", f"venue_dots_k{yr}.json"), encoding="utf-8"))
    meta = vd["meta"]
    placed_city = collections.Counter()
    for v in vd["venues"]:
        placed_city[v[8]] += v[2]

    d_csv = meta["votes_total"] - api_total
    print(f"\nK{yr}: API total {api_total:,} | local CSV total {meta['votes_total']:,} "
          f"(Δ {d_csv:+,}) | placed on map {meta['votes_placed']:,} "
          f"({100*meta['votes_placed']/api_total:.1f}% of API)")
    if abs(d_csv) > 0.001 * api_total:
        print(f"  *** CSV vs API mismatch above 0.1% — investigate the local ballot file ***")
    if not semcol:
        print("  (no settlement code in this API resource — national check only)")
        return

    gaps = []
    for sem, k in api_city.items():
        p = placed_city.get(sem, 0)
        if k >= 800:                       # ignore tiny localities in the ranking
            gaps.append((k - p, k, p, sem))
    gaps.sort(reverse=True)
    print("  worst-covered cities (API kosher vs placed):")
    for miss, k, p, sem in gaps[:8]:
        print(f"    {api_names.get(sem, sem)!s:<22} semel {sem}: api {k:,} placed {p:,} ({100*p/k:.0f}%)")


if __name__ == "__main__":
    for yr in (sys.argv[1:] or list(BALLOT_RESOURCES)):
        check_year(yr)
