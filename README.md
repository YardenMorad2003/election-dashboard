# Israeli Election Comparison Dashboard

## Quick Start for Future Sessions

**To continue working on this project:**
1. Read this README
2. Data is in `data.json` (pre-processed, ready to use)
3. Dashboard is in `dashboard.html` (single file, all sections)

---

## Project Structure

```
/home/claude/election-dashboard/
├── README.md          ← You are here
├── data.json          ← All data (3MB, pre-computed)
└── dashboard.html     ← The dashboard (single file)
```

---

## Data Structure (data.json)

### Top Level
```json
{
  "metadata": { ... },
  "national": { ... },
  "localities": [ ... ],
  "socioeconomic": [ ... ]
}
```

### metadata
- `knesset_years`: { 14: 1996, 15: 1999, ... 25: 2022 }
- `total_localities`: 1391
- `municipalities_with_socio`: 255

### national.elections[knesset_number]
```json
{
  "year": 2022,
  "total_eligible": 4693607,
  "localities_count": 1188,
  "right_haredi_pct": 50.22,
  "center_left_arab_pct": 48.28,
  "right_pct": 35.9,
  "haredi_pct": 14.3,
  "center_pct": 31.6,
  "left_pct": 6.9,
  "arab_pct": 9.7
}
```

### localities[i]
```json
{
  "name": "תל אביב - יפו",
  "elections_count": 12,
  "data": {
    "14": { "eligible": 265796, "right_haredi_pct": 27.4, ... },
    "25": { "eligible": 265796, "right_haredi_pct": 27.4, ... }
  }
}
```

### socioeconomic[i]
```json
{
  "name": "תל אביב - יפו",
  "name_en": "TEL AVIV - YAFO",
  "socio_cluster": 8,
  "socio_rank": 200,
  "population": 460613,
  "avg_monthly_income_per_capita": 9500,
  "pct_academic_degree": 55.2,
  "avg_days_abroad": 5.3,
  "election_data": { ... }  // Same as localities[i].data
}
```

---

## Dashboard Sections

### Section 1: National (תוצאות ארציות)
- Election selector (from/to comparison)
- Key metrics cards (eligible voters, bloc percentages, changes)
- Sub-groups breakdown (5 blocs)
- Historical trend line chart
- Stacked bar comparison

### Section 2: Localities (ניתוח לפי ישובים)
- Searchable table of 1391 localities
- Filter: All / 12 elections / Partial data
- Single locality detail view with charts
- Top movers lists (biggest changes)

### Section 3: Socioeconomic (ניתוח סוציו-אקונומי)
- Election selector
- Scatter: Income vs Right-Haredi %
- Scatter: Academic degree % vs Right-Haredi %
- Bar: Voting by socio-economic cluster (1-10)
- Scatter: Days abroad vs Right-Haredi %

---

## Political Blocs Definitions

| Hebrew | English | Parties (examples) |
|--------|---------|-------------------|
| ימין | Right | Likud, Yamina, etc. |
| חרדים | Ultra-Orthodox | Shas, UTJ |
| מרכז | Center | Yesh Atid, Blue & White |
| שמאל | Left | Labor, Meretz |
| ערבים | Arab | Joint List, Ra'am |

**Grouped:**
- ימין-חרדים (Right-Haredi): Right + Ultra-Orthodox
- מרכז-שמאל-ערבים (Center-Left-Arab): Center + Left + Arab

---

## Color Scheme (from screenshots)

- Background: Dark blue (#0a1628, #0f1f3d)
- Cards: Semi-transparent blue
- Right-Haredi: Blue (#4a9eff)
- Center-Left-Arab: Red (#ff6b6b)
- Right: Blue (#4a9eff)
- Haredi: Purple (#9b59b6)
- Center: Green (#2ecc71)
- Left: Red (#e74c3c)
- Arab: Orange (#f39c12)

---

## Key Findings (for context)

1. **Center explosion**: 3% (K14) → 31.6% (K25)
2. **Left collapse**: 33.9% (K14) → 6.9% (K25)
3. **Tel Aviv**: Shifted +19.5% toward Center-Left
4. **Strong correlation**: Higher income/education → more Center-Left voting

---

## Future Improvements

- [ ] Add voter turnout data
- [ ] Add geographic map view
- [ ] Add party-level breakdown (not just blocs)
- [ ] Add demographic filters (population size, region)
