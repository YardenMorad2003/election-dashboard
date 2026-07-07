# -*- coding: utf-8 -*-
"""
apply_fixes_2026_07_06k.py — one-shot applier for the 2026-07-06 evening
user-report session (kashish merge class + gan-dekel sub-1.5km class).

Writes:
  statarea_inputs/station_coord_fixes_k25_addr.json  (NEW: "venue@@addr" keys)
  statarea_inputs/station_coord_fixes.json           (name-keyed confirms merged)

Sources merged, in order:
  1. merge-class address fixes — hand-assembled evidence table below
     (house-precise Nominatim geocodes cross-checked vs SA polygons; הקבלן 8 via
     MOE-registry cluster 0.15km from street geocode = two sources agree);
     הירדן,23 + Modiin-Illit addresses resolved here at runtime (tier-2/3 rules).
  2. sa_mismatch_resolve.json confirms (sub-1.5km SA-mismatch ladder).
  3. k25_tier2.json + k25_tier3.json confirms (re-run >1.5km sweep ladder).

Never overwrites an existing name-keyed fix (evidence-verified by hand).
Runs a duplicate-key + bbox guard on both files afterwards.
Run: python -X utf8 analysis/apply_fixes_2026_07_06k.py
"""
import json, os, re, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
SNAP = os.path.join(HERE, "statarea_inputs")
sys.path.insert(0, HERE)
from build_venue_dots import norm  # noqa: E402
from resolve_sa_mismatch import geocode_precise, street_tokens  # noqa: E402
from resolve_sweep_tier3 import street_vertices, sa_polys_by_semel, sa_at  # noqa: E402

LEDGER_ADDR = (
    "2026-07-06k — the KASHISH MERGE CLASS (user report: 'מרכז יום לקשיש sits in "
    "נווה אביבים but its votes look nothing like it'). build_venue_dots keyed venues "
    "by (semel, name) only, so same-name venues at different buildings collapsed "
    "into one point: TLV מרכז יום לקשיש = 3 buildings / 11 kalpiot, all dumped at "
    "חיים לבנון 75 (SA 50000112, 66% of the SA's votes were foreign). This file is "
    "the address-scoped override layer (key 'venue@@addr', matched after norm(); "
    "K25 only — older years have no official address file and stay merged: KNOWN "
    "LIMITATION). Evidence per entry: house-number-precise Nominatim geocode of the "
    "official CEC address (kalpiplaces_kalpieslist_27-10.xlsx), PIP-verified "
    "in-city; נועם 7 independently corroborated by Cain's google_venue coord for "
    "kalpi 893 (0.06km); הקבלן 8 = MOE-registry בית יעקב cluster (acc 'גבוהה מאוד') "
    "0.15km from the street geocode — two independent sources; ולנברג ראול 11 = the "
    "pre-existing hand-verified name fix, re-scoped to its own building so the "
    "split cannot inherit it wrongly. עבדאללה בן אלחוסין (J-m, 15 kalpiot/9.6k "
    "voters) left UNFIXED: registry acc only 'בינונית', all sources within ~0.5km "
    "straddling the boundary — manual follow-up."
)

# (semel, venue-raw, addr-raw) -> [lat, lng]  — the hand-verified core
CORE = {
    ("5000", "מרכז יום לקשיש", "שד' ששת הימים,26"): [32.049677, 34.810095],  # house 26 ✓ SA 50001041
    ("5000", "מרכז יום לקשיש", "מנדלשטם,12"):       [32.09146, 34.77692],    # house 12 ✓ SA 50000316
    ("5000", "מרכז יום לקשיש", "נועם,7"):            [32.05134, 34.75735],    # house 7 ✓ SA 50001521
    ("5000", "אשכול גנים", "דיזנגוף,221"):           [32.08981, 34.77545],    # house 221 ✓ SA 50000317
    ("5000", "אשכול גנים", "העבודה,29"):             [32.07011, 34.77580],    # house 29 ✓ SA 50000516
    ("5000", "אשכול גנים", "הנגרים,17"):             [32.05634, 34.76525],    # house 17 ✓ SA 50000817
    ("3000", "ביס בית יעקב בנין ב", "מעגלות הרב פרדס,39"): [31.83874, 35.24534],  # house 39 ✓ SA 30000113
    ("3000", "ביס בית יעקב בנין ב", "הקבלן,8"):      [31.78951, 35.17412],    # MOE registry cluster
    ("4000", "מרכז קהילתי", "ולנברג ראול,11"):       [32.78084, 34.98351],    # existing verified fix
}

# resolved at runtime (tier-2 house / tier-3 single-SA street), else skipped:
RUNTIME = [
    ("4000", "חיפה", "מרכז קהילתי", "הירדן,23"),
    ("3797", "מודיעין עילית", "גני ילדים עץ הדעת", "רבי שמעון בר יוחאי,21"),
    ("3797", "מודיעין עילית", "גני ילדים עץ הדעת", "שדרות יחזקאל,1"),
    ("3797", "מודיעין עילית", "גני ילדים", "מסילת יוסף,48ב"),
    ("3797", "מודיעין עילית", "גני ילדים", "זכרון שמואל,3"),
]

LEDGER_NAME = (
    "2026-07-06k — the GAN-DEKEL SUB-1.5KM CLASS (user report: Or-Yehuda גן דקל "
    "sits on רחוב דקל 7 — the geocoder matched the venue NAME to the street name — "
    "instead of official כצנלסון 18, 0.96km away in a different SA; invisible to "
    "the 1.5km sweep threshold). analysis/resolve_sa_mismatch.py swept every K25 "
    "venue whose current SA differs from its official-address-geocode SA and "
    "confirmed fixes by the established ladder: tier-2 = Nominatim returns the "
    "EXACT house number of the official address (+road token match, in-city PIP); "
    "tier-3 = street geometry lies >=80% inside exactly ONE SA that differs from "
    "the current one (fix = median in-SA vertex). Existing hand fixes never "
    "auto-overridden. Also merged: confirms from the re-run >1.5km sweep ladder "
    "(k25_tier2/k25_tier3) after the שד' geocode-query bug fix rescued 554 "
    "previously-failed addresses."
)


def guard(path):
    def hook(pairs):
        keys = [k for k, _ in pairs]
        dups = [k for k, c in collections.Counter(keys).items() if c > 1]
        if dups:
            raise SystemExit(f"DUPLICATE KEYS in {path}: {dups}")
        return dict(pairs)
    data = json.load(open(path, encoding="utf-8"), object_pairs_hook=hook)
    bad = []
    for sem, vmap in data.items():
        if sem.startswith("_"):
            continue
        for k, v in vmap.items():
            if not (isinstance(v, list) and len(v) == 2 and 29.0 < v[0] < 33.5 and 34.0 < v[1] < 36.0):
                bad.append((sem, k, v))
    if bad:
        raise SystemExit(f"BAD ENTRIES in {path}: {bad[:5]}")
    print(f"  guard OK: {path} ({sum(len(v) for k, v in data.items() if not k.startswith('_'))} entries)")


def main():
    polys = sa_polys_by_semel()

    # ---------- 1) address-scoped file ----------
    apath = os.path.join(SNAP, "station_coord_fixes_k25_addr.json")
    afx = json.load(open(apath, encoding="utf-8")) if os.path.exists(apath) else {}
    afx.setdefault("_doc", "K25-only address-scoped venue coordinate fixes. Key: "
                   "'venue@@addr' exactly as in ballot_locations_25/k25_ballot_addresses "
                   "(matched after norm()). Consumed by build_venue_dots.py and "
                   "build_statarea_modern.py with precedence over name-keyed fixes.")
    afx["_verification_2026_07_06k"] = LEDGER_ADDR
    n_addr = 0
    for (sem, ven, adr), ll in CORE.items():
        afx.setdefault(sem, {})[f"{ven}@@{adr}"] = ll
        n_addr += 1
    for sem, city, ven, adr in RUNTIME:
        pg = geocode_precise(adr, city)
        chosen, how = None, ""
        mm = re.search(r"[,\s](\d+)\s*[א-ת]?\s*$", adr)
        want = mm.group(1) if mm else None
        if pg:
            la, ln, house, road = pg
            road_ok = (not road) or (street_tokens(adr) & set(norm(road).split()))
            if want and house and re.sub(r"\D", "", house) == want and road_ok \
                    and sa_at(ln, la, polys.get(sem, [])):
                chosen, how = [round(la, 6), round(ln, 6)], "house"
        if not chosen:
            street, verts = street_vertices(adr, city)
            if verts:
                assigns = [sa_at(x, y, polys.get(sem, [])) for x, y in verts]
                inside = [a for a in assigns if a]
                if inside and len(inside) >= 0.8 * len(assigns) and len(set(inside)) == 1:
                    in_verts = [v for v, a in zip(verts, assigns) if a]
                    vx, vy = in_verts[len(in_verts) // 2]
                    chosen, how = [round(vy, 6), round(vx, 6)], "street"
        if chosen:
            afx.setdefault(sem, {})[f"{ven}@@{adr}"] = chosen
            n_addr += 1
            print(f"  runtime[{how}] {city} {ven!r}@@{adr!r} -> {chosen}")
        else:
            print(f"  runtime MANUAL (no confident geocode): {city} {ven!r}@@{adr!r}")
    json.dump(afx, open(apath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"wrote {apath}: {n_addr} address fixes this run")

    # ---------- 2) name-keyed confirms ----------
    npath = os.path.join(SNAP, "station_coord_fixes.json")
    nfx = json.load(open(npath, encoding="utf-8"))
    existing = {(sem, norm(v)) for sem, vmap in nfx.items() if not sem.startswith("_")
                for v in vmap}
    added, skipped = [], []

    def add(sem, venue, fix, src):
        key = (str(sem), norm(venue))
        if key in existing:
            skipped.append((sem, venue, src))
            return
        nfx.setdefault(str(sem), {})[venue] = [round(fix[0], 6), round(fix[1], 6)]
        existing.add(key)
        added.append((sem, venue, src))

    res = json.load(open(os.path.join(SNAP, "sa_mismatch_resolve.json"), encoding="utf-8"))
    for c in res["confirms"]:
        add(c["semel"], c["venue"], c["fix"], f"sa-mismatch/{c['how']}")
    sw = json.load(open(os.path.join(SNAP, "k25_official_sweep.json"), encoding="utf-8"))
    for f in sw["flags"]:          # registry <=0.3km from geocode = two sources agree
        if f["verdict"] == "confirm":
            add(f["semel"], f["venue"], f["geo"], "sweep-registry-confirm")
    for fn, src in (("k25_tier2.json", "sweep-tier2"), ("k25_tier3.json", "sweep-tier3")):
        p = os.path.join(SNAP, fn)
        if not os.path.exists(p):
            continue
        t = json.load(open(p, encoding="utf-8"))
        for c in t.get("confirms", []):
            if "fix" in c:
                add(c["semel"], c["venue"], c["fix"], src)
    nfx["_verification_2026_07_06k"] = LEDGER_NAME
    json.dump(nfx, open(npath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    srcs = collections.Counter(s for _, _, s in added)
    print(f"wrote {npath}: +{len(added)} name fixes {dict(srcs)} | "
          f"skipped (existing hand fix): {len(skipped)}")
    for s in skipped:
        print("   skipped:", s)

    # ---------- 3) guards ----------
    guard(apath)
    guard(npath)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
