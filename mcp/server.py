"""Israeli Elections Data MCP server.

Exposes the election-dashboard dataset (Knesset 13-25, 1992-2022, plus the
1996/1999/2001 direct-PM contests) as query-shaped MCP tools. Every tool
returns a small slice -- never a whole data file -- so responses stay well
under a few KB.

Run (stdio):  python mcp/server.py
Data source:  ../data/*.json (the same files the dashboard site fetches).
"""

import json
import re
from pathlib import Path

from mcp.server.fastmcp import FastMCP

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

SITE = "https://yardenmorad2003.github.io/election-dashboard/"

BLOC_NOTES = (
    "Blocs: right, haredi, center, left, arab. right_haredi = right + haredi; "
    "center_left_arab = center + left + arab. From K21 (April 2019) on, "
    "opposition_right (Yisrael Beiteinu) is reported separately and counted "
    "inside center_left_arab, NOT right_haredi."
)

SOURCES = (
    "Official Central Elections Committee locality results (K13-25); CBS "
    "socio-economic municipal data (2021); INES survey series (1996-2022). "
    f"Interactive dashboard: {SITE}"
)

PM_CANDIDATES = {
    "1996": {"right": "Benjamin Netanyahu", "left": "Shimon Peres"},
    "1999": {"right": "Benjamin Netanyahu", "left": "Ehud Barak"},
    "2001": {"right": "Ariel Sharon", "left": "Ehud Barak"},
}

mcp = FastMCP(
    "israeli-elections",
    instructions=(
        "Israeli national election results, 1992-2022 (Knesset 13-25) at "
        "locality level, plus the 1996/1999/2001 direct prime-ministerial "
        "contests, party histories, ecological + survey vote-transfer "
        "matrices, and CBS socio-economic data. Locality and party inputs "
        "accept Hebrew or English names. " + BLOC_NOTES + " Sources: " + SOURCES
    ),
)

# ---------------------------------------------------------------- data access

_cache: dict = {}


def _load(name: str):
    if name not in _cache:
        with open(DATA_DIR / f"{name}.json", encoding="utf-8") as f:
            _cache[name] = json.load(f)
    return _cache[name]


def _norm(s: str) -> str:
    """Match names across spelling variants (geo files strip hyphens)."""
    s = re.sub(r"[-–\"'`׳״()]", " ", str(s))
    return re.sub(r"\s+", " ", s).strip().casefold()


def _r(x, nd=2):
    return round(x, nd) if isinstance(x, float) else x


# ------------------------------------------------------------- locality index

_loc_index: dict | None = None


def _locality_index():
    """norm(name) -> record, for Hebrew names, English names, and semel."""
    global _loc_index
    if _loc_index is None:
        en_map = _load("names_en")["localities"]
        idx = {}
        for rec in _load("localities"):
            he = rec["name"]
            en = en_map.get(he)
            entry = {"rec": rec, "he": he, "en": en}
            idx[_norm(he)] = entry
            if en:
                idx.setdefault(_norm(en), entry)
            if rec.get("semel") is not None:
                idx.setdefault(str(rec["semel"]), entry)
        _loc_index = idx
    return _loc_index


def _find_locality(query: str):
    """Return (entry, None) on a match or (None, suggestions) on a miss."""
    idx = _locality_index()
    q = _norm(query)
    if q in idx or str(query).strip() in idx:
        return idx.get(q) or idx[str(query).strip()], None
    scored = []
    for key, entry in idx.items():
        if key.isdigit():
            continue
        if key.startswith(q) or q in key:
            scored.append((0 if key.startswith(q) else 1, key, entry))
    scored.sort()
    seen, suggestions, entries = set(), [], []
    for _, _, entry in scored:
        if entry["he"] not in seen:
            seen.add(entry["he"])
            entries.append(entry)
            suggestions.append({"name": entry["he"], "name_en": entry["en"],
                                "semel": entry["rec"].get("semel")})
        if len(suggestions) >= 8:
            break
    if len(entries) == 1:  # unambiguous partial match ("Tel Aviv") -> resolve
        return entries[0], None
    return None, suggestions


def _miss(query, suggestions):
    return {"error": f"No locality matched '{query}'.",
            "suggestions": suggestions,
            "hint": "Pass a Hebrew or English locality name, or a semel code."}


# ---------------------------------------------------------------- party index

_party_index: dict | None = None


def _parties_en():
    return _load("names_en")["parties"]


def _party_lookup():
    """norm(code|hebrew name|english name) -> party_analysis record."""
    global _party_index
    if _party_index is None:
        en = _parties_en()
        idx = {}
        for rec in _load("party_analysis")["parties"]:
            keys = {rec["code"], rec["name"], *rec.get("name_history", {}).values()}
            keys |= {en[k] for k in list(keys) if k in en}
            for k in keys:
                idx.setdefault(_norm(k), rec)
        _party_index = idx
    return _party_index


# --------------------------------------------------------------------- tools


@mcp.tool()
def list_elections() -> dict:
    """All 13 Knesset elections (K13 1992 - K25 2022): year, turnout and
    national bloc shares, plus the three direct-PM contest years. Call this
    first to learn which Knesset numbers exist and how blocs are defined."""
    core = _load("core")["national"]["elections"]
    rows = {
        f"K{k}": {
            "year": v["year"], "turnout_pct": v["turnout_pct"],
            "right_haredi_pct": v["right_haredi_pct"],
            "center_left_arab_pct": v["center_left_arab_pct"],
            "blocs": {b: v[f"{b}_pct"] for b in
                      ("right", "haredi", "center", "left", "arab",
                       "opposition_right") if v.get(f"{b}_pct")},
        }
        for k, v in sorted(core.items(), key=lambda kv: int(kv[0]))
    }
    return {"elections": rows,
            "direct_pm_contests": {y: PM_CANDIDATES[y] for y in
                                   ("1996", "1999", "2001")},
            "bloc_definitions": BLOC_NOTES, "sources": SOURCES}


@mcp.tool()
def search_locality(query: str) -> dict:
    """Find a locality by Hebrew or English name (or semel code). Returns up
    to 8 matches with both names, the semel code, population and religious
    composition. Use this when unsure of exact spelling."""
    entry, suggestions = _find_locality(query)
    if entry is None:
        return _miss(query, suggestions)
    rec, rel = entry["rec"], entry["rec"].get("religion") or {}
    return {"name": entry["he"], "name_en": entry["en"],
            "semel": rec.get("semel"),
            "elections_covered": rec.get("elections_count"),
            "population_2019": rel.get("population_2019"),
            "pct_jews": rel.get("pct_jews"), "pct_arabs": rel.get("pct_arabs"),
            "pct_druze": rel.get("pct_druze")}


@mcp.tool()
def get_locality_results(locality: str, knesset: int | None = None) -> dict:
    """Election results for one locality: bloc percentages, turnout, eligible
    voters and valid votes. Omit `knesset` for the full 1992-2022 series, or
    pass 13-25 for one election. Locality accepts Hebrew/English name or
    semel."""
    entry, suggestions = _find_locality(locality)
    if entry is None:
        return _miss(locality, suggestions)
    rec = entry["rec"]
    years = _load("core")["metadata"]["knesset_years"]

    def row(k, d):
        return {"knesset": int(k), "year": years.get(k),
                "turnout_pct": d.get("turnout_pct"),
                "eligible": d.get("bzb"), "valid_votes": d.get("kosher_votes"),
                "right_haredi_pct": d.get("right_haredi_pct"),
                "center_left_arab_pct": d.get("center_left_arab_pct"),
                "blocs": {b: d[f"{b}_pct"] for b in
                          ("right", "haredi", "center", "left", "arab",
                           "opposition_right") if d.get(f"{b}_pct")}}

    out = {"name": entry["he"], "name_en": entry["en"],
           "semel": rec.get("semel"), "bloc_definitions": BLOC_NOTES}
    if knesset is not None:
        d = rec["data"].get(str(knesset))
        if d is None:
            return {"error": f"No K{knesset} data for {entry['he']}.",
                    "available": sorted(int(k) for k in rec["data"])}
        out["result"] = row(str(knesset), d)
    else:
        out["results"] = [row(k, d) for k, d in
                          sorted(rec["data"].items(), key=lambda kv: int(kv[0]))]
    return out


@mcp.tool()
def get_locality_parties(locality: str, knesset: int) -> dict:
    """Party-level vote shares (percent of valid votes) in one locality for
    one Knesset election (13-25), sorted by share, with estimated vote counts
    (share x valid votes). Party codes are official ballot codes; Hebrew and
    English party names are included. Parties below ~0.01% locally are
    omitted."""
    entry, suggestions = _find_locality(locality)
    if entry is None:
        return _miss(locality, suggestions)
    by_loc = _load("parties_by_locality").get(str(knesset))
    if by_loc is None:
        return {"error": f"No party-level data for K{knesset} (valid: 13-25)."}
    shares = by_loc.get(entry["he"])
    if shares is None:
        want = _norm(entry["he"])
        shares = next((v for n, v in by_loc.items() if _norm(n) == want), None)
    if shares is None:
        return {"error": f"K{knesset} has no party breakdown for {entry['he']}."}
    nat = _load("parties_national")[str(knesset)]
    info = {p["code"]: p for p in nat["party_list"]}
    en = _parties_en()
    valid = entry["rec"].get("data", {}).get(str(knesset), {}).get("kosher_votes")
    parties = [{"code": c,
                "name": info.get(c, {}).get("name", c),
                "name_en": en.get(info.get(c, {}).get("name", c)),
                "bloc": info.get(c, {}).get("bloc"),
                "pct": _r(float(v)),
                "votes_est": round(v * valid / 100) if valid else None}
               for c, v in sorted(shares.items(), key=lambda kv: -kv[1])]
    return {"name": entry["he"], "name_en": entry["en"],
            "knesset": knesset, "year": nat["year"],
            "valid_votes_total": valid,
            "note": "pct is the official share of valid votes; votes_est is "
                    "derived from it and rounded.",
            "parties": parties}


@mcp.tool()
def get_national_results(knesset: int) -> dict:
    """National results for one Knesset election (13-25): every party's raw
    votes, vote share, seats and bloc, plus bloc totals and turnout."""
    nat = _load("parties_national").get(str(knesset))
    if nat is None:
        return {"error": f"Unknown Knesset {knesset} (valid: 13-25)."}
    core = _load("core")["national"]["elections"][str(knesset)]
    en = _parties_en()
    info = {p["code"]: p for p in nat["party_list"]}
    parties = [{"code": c,
                "name": info.get(c, {}).get("name", c),
                "name_en": en.get(info.get(c, {}).get("name", c)),
                "bloc": info.get(c, {}).get("bloc"),
                "votes": v, "pct": nat["national"].get(c),
                "seats": nat["seats"].get(c, 0)}
               for c, v in sorted(nat["national_votes"].items(),
                                  key=lambda kv: -kv[1])]
    return {"election": nat["election_name"], "year": nat["year"],
            "turnout_pct": core["turnout_pct"],
            "eligible": core["total_eligible"],
            "bloc_totals_pct": {b: core[f"{b}_pct"] for b in
                                ("right", "haredi", "center", "left", "arab",
                                 "opposition_right") if core.get(f"{b}_pct")},
            "parties": parties, "bloc_definitions": BLOC_NOTES}


@mcp.tool()
def get_party(party: str, knesset: int | None = None) -> dict:
    """History of one party across 1992-2022: seats, national vote share,
    name and bloc per election, plus its top strongholds (highest local
    share). Accepts a ballot code (e.g. 'מחל') or a Hebrew/English party name
    (e.g. 'Likud', 'העבודה'). Optional `knesset` filters to one election."""
    rec = _party_lookup().get(_norm(party))
    if rec is None:
        en = _parties_en()
        names = sorted({en.get(r["name"], r["name"])
                        for r in _load("party_analysis")["parties"]})
        return {"error": f"No party matched '{party}'.",
                "known_parties": names}
    traj = rec.get("trajectory", [])
    if knesset is not None:
        traj = [t for t in traj if t.get("k") == str(knesset)]
        if not traj:
            return {"error": f"{rec['name']} did not run (or is not tracked) "
                             f"in K{knesset}.",
                    "elections_run": [t["k"] for t in rec.get("trajectory", [])]}
    en = _parties_en()
    out = {"code": rec["code"], "name": rec["name"],
           "name_en": en.get(rec["name"]), "bloc": rec.get("bloc"),
           "peak_seats": rec.get("peak_seats"),
           "name_history": rec.get("name_history"),
           "trajectory": [{k: _r(v) for k, v in t.items()} for t in traj]}
    strongholds = rec.get("strongholds")
    if isinstance(strongholds, list) and strongholds:
        out["strongholds"] = strongholds[:10]
        out["strongholds_note"] = (f"Highest local vote share, reference "
                                   f"election K{rec.get('ref_k')}.")
    return out


@mcp.tool()
def get_vote_transfers(from_knesset: int, to_knesset: int,
                       source: str = "ballot") -> dict:
    """Bloc-level vote-transfer matrix between two consecutive Knesset
    elections. `source='ballot'` = ecological inference (constrained least
    squares over ~1,000 localities, includes abstention flows);
    `source='survey'` = INES recalled-vote crosstabs. Rows are the FROM bloc
    and sum to 1; cell = share of the from-bloc's voters going to each
    destination ('dnv' = did not vote). Consecutive pairs only (13->14 ...
    24->25)."""
    key = f"{from_knesset}_to_{to_knesset}"
    if source not in ("ballot", "survey"):
        return {"error": "source must be 'ballot' or 'survey'."}
    data = _load("vote_transfers" if source == "ballot" else "survey_transfers")
    tr = data["transitions"].get(key)
    if tr is None:
        return {"error": f"No transition {key}.",
                "available": list(data["transitions"])}
    labels = (tr.get("bloc_labels") or data.get("categories")
              or data.get("blocs"))
    block = tr.get("bloc_with_abstention") or tr.get("with_abstention") or {}
    M = block.get("M", [])
    matrix = {}
    for i, row in enumerate(M):
        cells = {labels[j]: _r(row[j], 4) for j in range(len(row)) if row[j]}
        if cells:
            matrix[labels[i]] = cells
    out = {"from_knesset": from_knesset, "to_knesset": to_knesset,
           "source": source, "matrix_rows_from_bloc": matrix,
           "bloc_definitions": BLOC_NOTES}
    if source == "ballot":
        out.update({"method": "ecological inference (ballot-level constrained "
                              "least squares)",
                    "r2": block.get("r2"),
                    "n_localities": tr.get("n_localities"),
                    "electorate_growth": tr.get("electorate_growth")})
    else:
        out.update({"method": "INES survey recalled-vote x current-vote "
                              "crosstab", "n_respondents": tr.get("n"),
                    "wave": tr.get("wave"),
                    "row_sample_sizes": dict(zip(labels, tr.get("row_n", []))),
                    "note": data.get("note")})
    return out


@mcp.tool()
def get_pm_direct(year: int, locality: str | None = None) -> dict:
    """Israel's direct prime-ministerial elections (1996, 1999, 2001): the
    two-candidate result nationally, or in one locality (raw votes, shares,
    turnout). 2001 had a mass Arab boycott and ~21% blank ballots -- turnout
    numbers reflect that."""
    pm = _load("pm_direct")
    y = str(year)
    contest = pm["contests"].get(y)
    if contest is None:
        return {"error": f"No direct-PM contest in {year} (valid: 1996, 1999, "
                         "2001)."}
    cands = PM_CANDIDATES[y]
    out = {"year": year, "candidates": cands,
           "concurrent_knesset": f"K{contest['knesset']}" if
           contest.get("knesset") else None,
           "national": {"right_votes": contest["right_votes"],
                        "left_votes": contest["left_votes"],
                        "right_pct_two_way": _r(100 * contest["right_votes"] /
                                                (contest["right_votes"] +
                                                 contest["left_votes"]))}}
    if locality:
        entry, suggestions = _find_locality(locality)
        if entry is None:
            return _miss(locality, suggestions)
        row = None
        for cand in (entry["he"], _norm(entry["he"])):
            row = pm["loc"].get(cand)
            if row:
                break
        if row is None:
            want = _norm(entry["he"])
            row = next((v for n, v in pm["loc"].items()
                        if _norm(n) == want), None)
        if row is None or y not in row:
            return {"error": f"No {year} PM data for {entry['he']} (small "
                             "localities and Bedouin tribes are unmapped)."}
        r, l, voted, registered = row[y]
        two = r + l
        out["locality"] = {
            "name": entry["he"], "name_en": entry["en"],
            "right_votes": r, "left_votes": l,
            "right_pct_two_way": _r(100 * r / two) if two else None,
            "invalid_or_blank": voted - two,
            "turnout_pct": _r(100 * voted / registered) if registered else None}
    return out


@mcp.tool()
def get_demographics(locality: str) -> dict:
    """CBS socio-economic profile (2021) for a municipality: income,
    education, age structure, plus religious composition. Available for the
    201 municipalities only -- small localities return religion/population
    data alone."""
    entry, suggestions = _find_locality(locality)
    if entry is None:
        return _miss(locality, suggestions)
    rec = entry["rec"]
    out = {"name": entry["he"], "name_en": entry["en"],
           "semel": rec.get("semel"),
           "religion_2019": rec.get("religion")}
    want = _norm(entry["he"])
    socio = next((s for s in _load("socioeconomic")
                  if s.get("code") == rec.get("semel")
                  or _norm(s["name"]) == want), None)
    if socio is None:
        out["socio_note"] = ("No CBS socio-economic record (covers the 201 "
                             "municipalities only).")
        return out
    fields = ("population", "median_age", "dependency_ratio",
              "pct_families_4plus_children", "avg_years_schooling",
              "pct_academic_degree", "pct_with_work_income",
              "avg_monthly_income_per_capita", "pct_below_min_wage",
              "pct_above_2x_avg_wage", "pct_income_support",
              "vehicles_per_100_residents")
    out["socioeconomic_2021"] = {f: _r(socio[f]) for f in fields
                                 if socio.get(f) is not None}
    for k in ("cluster", "socio_cluster", "socioeconomic_cluster"):
        if socio.get(k) is not None:
            out["socioeconomic_2021"]["cbs_cluster"] = socio[k]
            break
    return out


if __name__ == "__main__":
    mcp.run()
