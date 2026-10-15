# -*- coding: utf-8 -*-
"""Levinson indicator (K25 / 2022 census) -> data/levinson_k25.json

Persuadable-Likud profile, after Levinson: masorti or light-hiloni neighbourhoods with a
medium-to-high Asia+Africa origin share, a large Likud vote, medium-to-high income
("western consumerism") and a security-hawkish vote.

Universe: Jewish stat-areas with SA-level 2022 census, modal household lifestyle
hiloni/masorti (dati + haredi excluded), >= 300 valid K25 votes.
Pillars (percentile ranks within the universe):
  mizrahi = % origin Asia + Africa (CBS: person's / father's continent of birth)
  likud   = K25 Likud share
  income  = mean pct of median wage, % in wage deciles 9-10, SES-2021 index, car ownership
  hawk    = right bloc + opposition_right (Yisrael Beiteinu) share
score = mean of the four pillar percentiles (+0.05 if masorti-modal), 0-100.
Passes ("Levinson area") = Likud >= 30% AND Mizrahi >= universe median AND income pct >= 0.60.

Record per SA key: [score, pass, mizrahi, likud, hawk, income_pct(0-100), center, masorti]
"""
import json, os
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data")
load = lambda f: json.load(open(os.path.join(D, f), encoding="utf-8"))

A = load("statarea_2022.json")["areas"]
SES = load("ses_statarea.json")["2021"]
LIKUD_MIN, INC_MIN, VALID_MIN = 30.0, 0.60, 300

rows = []
for k, a in A.items():
    c = a.get("census") or {}
    if a.get("census_src") != "sa" or c.get("religion") != "יהודים" or "parties" not in a:
        continue
    if c.get("datiyut") not in ("חילוני", "מסורתי") or a["valid"] < VALID_MIN or c.get("med_wage") is None:
        continue
    p, b = a["parties"], a["blocs"]
    s = SES.get(f'{a["semel"]}|{a["sa"]}')
    rows.append(dict(id=k, pop=c.get("pop") or 0, masorti=c["datiyut"] == "מסורתי",
        mizrahi=(c.get("orig_asia") or 0) + (c.get("orig_afr") or 0),
        med_wage=c["med_wage"], top2dec=c.get("top2dec"), no_car=c.get("no_car"),
        ses=s[0] if s and s[2] == "sa" else np.nan,
        likud=p.get("מחל", 0), hawk=b["right"] + b["opposition_right"], center=b["center"]))
df = pd.DataFrame(rows)
pr = lambda s: s.rank(pct=True)
inc = pd.concat([pr(df.med_wage), pr(df.top2dec), pr(df.ses), pr(-df.no_car)], axis=1).mean(axis=1, skipna=True)
df["inc_pct"] = pr(inc)
df["score"] = 100 * ((pr(df.mizrahi) + pr(df.likud) + df.inc_pct + pr(df.hawk)) / 4 + 0.05 * df.masorti)
miz_med = float(df.mizrahi.median())
df["pass"] = (df.likud >= LIKUD_MIN) & (df.mizrahi >= miz_med) & (df.inc_pct >= INC_MIN)

P = df[df["pass"]]
out = {
    "meta": {
        "built": pd.Timestamp.today().strftime("%Y-%m-%d"),
        "election": "25", "census": "2022", "ses": "2021",
        "universe": int(len(df)), "n_pass": int(len(P)), "pop_pass": int(P["pop"].sum()),
        "thresholds": {"likud": LIKUD_MIN, "mizrahi": round(miz_med, 1), "income_pct": int(INC_MIN * 100)},
        "center_pass": round(float(P.center.mean()), 1),
        "center_other_likud30": round(float(df[~df["pass"] & (df.likud >= LIKUD_MIN)].center.mean()), 1),
        "fields": ["score", "pass", "mizrahi", "likud", "hawk", "income_pct", "center", "masorti"],
    },
    "areas": {r.id: [round(r.score, 1), int(r["pass"]), round(r.mizrahi, 1), round(r.likud, 1),
                     round(r.hawk, 1), round(100 * r.inc_pct), round(r.center, 1), int(r.masorti)]
              for _, r in df.iterrows()},
}
with open(os.path.join(D, "levinson_k25.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
print(json.dumps(out["meta"], ensure_ascii=False))
