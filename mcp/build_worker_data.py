"""Build pre-sliced data artifacts for the Cloudflare Worker MCP server.

The Worker cannot afford to parse the big dashboard files per request
(localities.json alone is 4.3 MB), so this script shards them into small
files under data/mcp/ that the Worker fetches from the GitHub Pages CDN:

  data/mcp/index.json        slim locality lookup index (name/semel/religion)
  data/mcp/loc/<id>.json     one file per locality: full per-election data
  data/mcp/parties/<k>.json  party shares by locality, one file per Knesset
  data/mcp/socio.json        socioeconomic slice (only the fields served)
  data/mcp/parties_meta.json party_analysis slice (only the fields served)

<id> is the semel code, or "x<row-index>" for localities without one.
Small source files (core, names_en, parties_national, vote_transfers,
survey_transfers, pm_direct) are fetched by the Worker as-is.

Re-run after any change to the source data files, then commit data/mcp/.
"""

import json
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
OUT = DATA / "mcp"

SOCIO_FIELDS = (
    "population", "median_age", "dependency_ratio",
    "pct_families_4plus_children", "avg_years_schooling",
    "pct_academic_degree", "pct_with_work_income",
    "avg_monthly_income_per_capita", "pct_below_min_wage",
    "pct_above_2x_avg_wage", "pct_income_support",
    "vehicles_per_100_residents",
)

PARTY_FIELDS = ("code", "name", "name_history", "bloc", "peak_seats",
                "ref_k", "trajectory")


def _load(name):
    with open(DATA / f"{name}.json", encoding="utf-8") as f:
        return json.load(f)


def _dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
    return path.stat().st_size


def main():
    if OUT.exists():
        shutil.rmtree(OUT)

    en_map = _load("names_en")["localities"]
    localities = _load("localities")

    index, loc_bytes = [], 0
    for i, rec in enumerate(localities):
        loc_id = str(rec["semel"]) if rec.get("semel") is not None else f"x{i}"
        index.append({"id": loc_id, "he": rec["name"],
                      "en": en_map.get(rec["name"]),
                      "semel": rec.get("semel"),
                      "elections_count": rec.get("elections_count"),
                      "religion": rec.get("religion")})
        loc_bytes += _dump(OUT / "loc" / f"{loc_id}.json",
                           {"he": rec["name"], "en": en_map.get(rec["name"]),
                            "semel": rec.get("semel"), "data": rec["data"]})
    idx_bytes = _dump(OUT / "index.json", index)

    pbl = _load("parties_by_locality")
    pbl_bytes = sum(_dump(OUT / "parties" / f"{k}.json", v)
                    for k, v in pbl.items())

    socio = []
    for s in _load("socioeconomic"):
        row = {"code": s.get("code"), "name": s.get("name")}
        row.update({f: s[f] for f in SOCIO_FIELDS if s.get(f) is not None})
        for k in ("cluster", "socio_cluster", "socioeconomic_cluster"):
            if s.get(k) is not None:
                row["cbs_cluster"] = s[k]
                break
        socio.append(row)
    socio_bytes = _dump(OUT / "socio.json", socio)

    parties = []
    for p in _load("party_analysis")["parties"]:
        row = {f: p[f] for f in PARTY_FIELDS if p.get(f) is not None}
        sh = p.get("strongholds")
        if isinstance(sh, list) and sh:
            row["strongholds"] = sh[:10]
        parties.append(row)
    pm_bytes = _dump(OUT / "parties_meta.json", parties)

    print(f"index.json        {idx_bytes/1024:8.1f} KB  ({len(index)} localities)")
    print(f"loc/*.json        {loc_bytes/1024:8.1f} KB  ({len(index)} files)")
    print(f"parties/*.json    {pbl_bytes/1024:8.1f} KB  ({len(pbl)} files)")
    print(f"socio.json        {socio_bytes/1024:8.1f} KB  ({len(socio)} rows)")
    print(f"parties_meta.json {pm_bytes/1024:8.1f} KB  ({len(parties)} parties)")


if __name__ == "__main__":
    main()
