/**
 * Israeli Elections MCP server — Cloudflare Worker (Streamable HTTP).
 *
 * Remote port of mcp/server.py: same nine query tools, plus `search`/`fetch`
 * for ChatGPT deep-research compatibility. Stateless JSON-RPC over POST /mcp.
 * Data comes from the dashboard's GitHub Pages CDN (env.DATA_BASE): small
 * source files as-is, big ones via the pre-sliced data/mcp/ artifacts
 * produced by mcp/build_worker_data.py.
 */

const SITE = "https://yardenmorad2003.github.io/election-dashboard/";

const BLOC_NOTES =
  "Blocs: right, haredi, center, left, arab. right_haredi = right + haredi; " +
  "center_left_arab = center + left + arab. From K21 (April 2019) on, " +
  "opposition_right (Yisrael Beiteinu) is reported separately and counted " +
  "inside center_left_arab, NOT right_haredi.";

const SOURCES =
  "Official Central Elections Committee locality results (K13-25); CBS " +
  "socio-economic municipal data (2021); INES survey series (1996-2022). " +
  `Interactive dashboard: ${SITE}`;

const INSTRUCTIONS =
  "Israeli national election results, 1992-2022 (Knesset 13-25) at " +
  "locality level, plus the 1996/1999/2001 direct prime-ministerial " +
  "contests, party histories, ecological + survey vote-transfer matrices, " +
  "and CBS socio-economic data. Locality and party inputs accept Hebrew " +
  "or English names. " + BLOC_NOTES + " Sources: " + SOURCES;

const PM_CANDIDATES = {
  1996: { right: "Benjamin Netanyahu", left: "Shimon Peres" },
  1999: { right: "Benjamin Netanyahu", left: "Ehud Barak" },
  2001: { right: "Ariel Sharon", left: "Ehud Barak" },
};

const BLOCS = ["right", "haredi", "center", "left", "arab", "opposition_right"];

// ---------------------------------------------------------------- data access

const memo = new Map();

async function load(env, path) {
  if (memo.has(path)) return memo.get(path);
  const res = await fetch(env.DATA_BASE + path, {
    cf: { cacheEverything: true, cacheTtl: 86400 },
  });
  if (!res.ok) throw new Error(`data fetch failed: ${path} (${res.status})`);
  const data = await res.json();
  memo.set(path, data);
  return data;
}

function norm(s) {
  return String(s)
    .replace(/[-–"'`׳״()]/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();
}

function r(x, nd = 2) {
  return typeof x === "number" && !Number.isInteger(x) ? +x.toFixed(nd) : x;
}

// ------------------------------------------------------------- locality index

async function localityIndex(env) {
  if (memo.has("_locidx")) return memo.get("_locidx");
  const rows = await load(env, "mcp/index.json");
  const byKey = new Map();
  const byId = new Map();
  for (const rec of rows) {
    const entry = { rec, he: rec.he, en: rec.en };
    byKey.set(norm(rec.he), entry);
    if (rec.en && !byKey.has(norm(rec.en))) byKey.set(norm(rec.en), entry);
    if (rec.semel != null && !byKey.has(String(rec.semel)))
      byKey.set(String(rec.semel), entry);
    byId.set(rec.id, entry);
  }
  const idx = { byKey, byId };
  memo.set("_locidx", idx);
  return idx;
}

async function findLocality(env, query) {
  const { byKey } = await localityIndex(env);
  const q = norm(query);
  const direct = byKey.get(q) || byKey.get(String(query).trim());
  if (direct) return [direct, null];
  const scored = [];
  for (const [key, entry] of byKey) {
    if (/^\d+$/.test(key)) continue;
    if (key.startsWith(q) || key.includes(q))
      scored.push([key.startsWith(q) ? 0 : 1, key, entry]);
  }
  scored.sort((a, b) => a[0] - b[0] || (a[1] < b[1] ? -1 : 1));
  const seen = new Set(), suggestions = [], entries = [];
  for (const [, , entry] of scored) {
    if (!seen.has(entry.he)) {
      seen.add(entry.he);
      entries.push(entry);
      suggestions.push({ name: entry.he, name_en: entry.en, semel: entry.rec.semel });
    }
    if (suggestions.length >= 8) break;
  }
  if (entries.length === 1) return [entries[0], null]; // unambiguous partial
  return [null, suggestions];
}

function miss(query, suggestions) {
  return {
    error: `No locality matched '${query}'.`,
    suggestions,
    hint: "Pass a Hebrew or English locality name, or a semel code.",
  };
}

async function locData(env, entry) {
  return load(env, `mcp/loc/${entry.rec.id}.json`);
}

async function partiesEn(env) {
  return (await load(env, "names_en.json")).parties;
}

// --------------------------------------------------------------------- tools

function locResultRow(k, d, years) {
  const blocs = {};
  for (const b of BLOCS) if (d[`${b}_pct`]) blocs[b] = d[`${b}_pct`];
  return {
    knesset: +k, year: years[k],
    turnout_pct: d.turnout_pct ?? null,
    eligible: d.bzb ?? null, valid_votes: d.kosher_votes ?? null,
    right_haredi_pct: d.right_haredi_pct ?? null,
    center_left_arab_pct: d.center_left_arab_pct ?? null,
    blocs,
  };
}

const handlers = {
  async list_elections(env) {
    const core = (await load(env, "core.json")).national.elections;
    const rows = {};
    for (const k of Object.keys(core).sort((a, b) => a - b)) {
      const v = core[k];
      const blocs = {};
      for (const b of BLOCS) if (v[`${b}_pct`]) blocs[b] = v[`${b}_pct`];
      rows[`K${k}`] = {
        year: v.year, turnout_pct: v.turnout_pct,
        right_haredi_pct: v.right_haredi_pct,
        center_left_arab_pct: v.center_left_arab_pct,
        blocs,
      };
    }
    return {
      elections: rows,
      direct_pm_contests: PM_CANDIDATES,
      bloc_definitions: BLOC_NOTES, sources: SOURCES,
    };
  },

  async search_locality(env, { query }) {
    const [entry, suggestions] = await findLocality(env, query);
    if (!entry) return miss(query, suggestions);
    const rel = entry.rec.religion || {};
    return {
      name: entry.he, name_en: entry.en, semel: entry.rec.semel,
      elections_covered: entry.rec.elections_count,
      population_2019: rel.population_2019 ?? null,
      pct_jews: rel.pct_jews ?? null, pct_arabs: rel.pct_arabs ?? null,
      pct_druze: rel.pct_druze ?? null,
    };
  },

  async get_locality_results(env, { locality, knesset }) {
    const [entry, suggestions] = await findLocality(env, locality);
    if (!entry) return miss(locality, suggestions);
    const loc = await locData(env, entry);
    const years = (await load(env, "core.json")).metadata.knesset_years;
    const out = {
      name: entry.he, name_en: entry.en, semel: entry.rec.semel,
      bloc_definitions: BLOC_NOTES,
    };
    if (knesset != null) {
      const d = loc.data[String(knesset)];
      if (!d)
        return {
          error: `No K${knesset} data for ${entry.he}.`,
          available: Object.keys(loc.data).map(Number).sort((a, b) => a - b),
        };
      out.result = locResultRow(String(knesset), d, years);
    } else {
      out.results = Object.keys(loc.data)
        .sort((a, b) => a - b)
        .map((k) => locResultRow(k, loc.data[k], years));
    }
    return out;
  },

  async get_locality_parties(env, { locality, knesset }) {
    const [entry, suggestions] = await findLocality(env, locality);
    if (!entry) return miss(locality, suggestions);
    let byLoc;
    try {
      byLoc = await load(env, `mcp/parties/${knesset}.json`);
    } catch {
      return { error: `No party-level data for K${knesset} (valid: 13-25).` };
    }
    let shares = byLoc[entry.he];
    if (!shares) {
      const want = norm(entry.he);
      for (const [n, v] of Object.entries(byLoc))
        if (norm(n) === want) { shares = v; break; }
    }
    if (!shares)
      return { error: `K${knesset} has no party breakdown for ${entry.he}.` };
    const nat = (await load(env, "parties_national.json"))[String(knesset)];
    const info = Object.fromEntries(nat.party_list.map((p) => [p.code, p]));
    const en = await partiesEn(env);
    const loc = await locData(env, entry);
    const valid = loc.data?.[String(knesset)]?.kosher_votes;
    const parties = Object.entries(shares)
      .sort((a, b) => b[1] - a[1])
      .map(([c, v]) => ({
        code: c,
        name: info[c]?.name ?? c,
        name_en: en[info[c]?.name] ?? null,
        bloc: info[c]?.bloc ?? null,
        pct: r(+v),
        votes_est: valid ? Math.round((v * valid) / 100) : null,
      }));
    return {
      name: entry.he, name_en: entry.en,
      knesset, year: nat.year, valid_votes_total: valid ?? null,
      note: "pct is the official share of valid votes; votes_est is derived " +
        "from it and rounded.",
      parties,
    };
  },

  async get_national_results(env, { knesset }) {
    const nat = (await load(env, "parties_national.json"))[String(knesset)];
    if (!nat) return { error: `Unknown Knesset ${knesset} (valid: 13-25).` };
    const core = (await load(env, "core.json")).national.elections[String(knesset)];
    const en = await partiesEn(env);
    const info = Object.fromEntries(nat.party_list.map((p) => [p.code, p]));
    const parties = Object.entries(nat.national_votes)
      .sort((a, b) => b[1] - a[1])
      .map(([c, v]) => ({
        code: c,
        name: info[c]?.name ?? c,
        name_en: en[info[c]?.name] ?? null,
        bloc: info[c]?.bloc ?? null,
        votes: v, pct: nat.national[c] ?? null,
        seats: nat.seats[c] ?? 0,
      }));
    const blocTotals = {};
    for (const b of BLOCS) if (core[`${b}_pct`]) blocTotals[b] = core[`${b}_pct`];
    return {
      election: nat.election_name, year: nat.year,
      turnout_pct: core.turnout_pct, eligible: core.total_eligible,
      bloc_totals_pct: blocTotals,
      parties, bloc_definitions: BLOC_NOTES,
    };
  },

  async get_party(env, { party, knesset }) {
    const recs = await load(env, "mcp/parties_meta.json");
    const en = await partiesEn(env);
    let idx = memo.get("_partyidx");
    if (!idx) {
      idx = new Map();
      for (const rec of recs) {
        const keys = new Set([rec.code, rec.name,
          ...Object.values(rec.name_history || {})]);
        for (const k of [...keys]) if (en[k]) keys.add(en[k]);
        for (const k of keys)
          if (!idx.has(norm(k))) idx.set(norm(k), rec);
      }
      memo.set("_partyidx", idx);
    }
    const rec = idx.get(norm(party));
    if (!rec) {
      const names = [...new Set(recs.map((p) => en[p.name] ?? p.name))].sort();
      return { error: `No party matched '${party}'.`, known_parties: names };
    }
    let traj = rec.trajectory || [];
    if (knesset != null) {
      traj = traj.filter((t) => t.k === String(knesset));
      if (!traj.length)
        return {
          error: `${rec.name} did not run (or is not tracked) in K${knesset}.`,
          elections_run: (rec.trajectory || []).map((t) => t.k),
        };
    }
    const out = {
      code: rec.code, name: rec.name, name_en: en[rec.name] ?? null,
      bloc: rec.bloc ?? null, peak_seats: rec.peak_seats ?? null,
      name_history: rec.name_history ?? null,
      trajectory: traj.map((t) =>
        Object.fromEntries(Object.entries(t).map(([k, v]) => [k, r(v)]))),
    };
    if (Array.isArray(rec.strongholds) && rec.strongholds.length) {
      out.strongholds = rec.strongholds.slice(0, 10);
      out.strongholds_note =
        `Highest local vote share, reference election K${rec.ref_k}.`;
    }
    return out;
  },

  async get_vote_transfers(env, { from_knesset, to_knesset, source = "ballot" }) {
    const key = `${from_knesset}_to_${to_knesset}`;
    if (source !== "ballot" && source !== "survey")
      return { error: "source must be 'ballot' or 'survey'." };
    const data = await load(env,
      source === "ballot" ? "vote_transfers.json" : "survey_transfers.json");
    const tr = data.transitions[key];
    if (!tr)
      return { error: `No transition ${key}.`,
        available: Object.keys(data.transitions) };
    const labels = tr.bloc_labels || data.categories || data.blocs;
    const block = tr.bloc_with_abstention || tr.with_abstention || {};
    const M = block.M || [];
    const matrix = {};
    M.forEach((row, i) => {
      const cells = {};
      row.forEach((v, j) => { if (v) cells[labels[j]] = r(v, 4); });
      if (Object.keys(cells).length) matrix[labels[i]] = cells;
    });
    const out = {
      from_knesset, to_knesset, source,
      matrix_rows_from_bloc: matrix, bloc_definitions: BLOC_NOTES,
    };
    if (source === "ballot") {
      Object.assign(out, {
        method: "ecological inference (ballot-level constrained least squares)",
        r2: block.r2 ?? null, n_localities: tr.n_localities ?? null,
        electorate_growth: tr.electorate_growth ?? null,
      });
    } else {
      Object.assign(out, {
        method: "INES survey recalled-vote x current-vote crosstab",
        n_respondents: tr.n ?? null, wave: tr.wave ?? null,
        row_sample_sizes: Object.fromEntries(
          labels.map((l, i) => [l, (tr.row_n || [])[i]])),
        note: data.note ?? null,
      });
    }
    return out;
  },

  async get_pm_direct(env, { year, locality }) {
    const pm = await load(env, "pm_direct.json");
    const contest = pm.contests[String(year)];
    if (!contest)
      return { error: `No direct-PM contest in ${year} (valid: 1996, 1999, 2001).` };
    const out = {
      year, candidates: PM_CANDIDATES[year],
      concurrent_knesset: contest.knesset ? `K${contest.knesset}` : null,
      national: {
        right_votes: contest.right_votes, left_votes: contest.left_votes,
        right_pct_two_way: r((100 * contest.right_votes) /
          (contest.right_votes + contest.left_votes)),
      },
    };
    if (locality) {
      const [entry, suggestions] = await findLocality(env, locality);
      if (!entry) return miss(locality, suggestions);
      let row = pm.loc[entry.he] || pm.loc[norm(entry.he)];
      if (!row) {
        const want = norm(entry.he);
        for (const [n, v] of Object.entries(pm.loc))
          if (norm(n) === want) { row = v; break; }
      }
      if (!row || !row[String(year)])
        return { error: `No ${year} PM data for ${entry.he} (small localities ` +
          "and Bedouin tribes are unmapped)." };
      const [rv, lv, voted, registered] = row[String(year)];
      const two = rv + lv;
      out.locality = {
        name: entry.he, name_en: entry.en,
        right_votes: rv, left_votes: lv,
        right_pct_two_way: two ? r((100 * rv) / two) : null,
        invalid_or_blank: voted - two,
        turnout_pct: registered ? r((100 * voted) / registered) : null,
      };
    }
    return out;
  },

  async get_demographics(env, { locality }) {
    const [entry, suggestions] = await findLocality(env, locality);
    if (!entry) return miss(locality, suggestions);
    const out = {
      name: entry.he, name_en: entry.en, semel: entry.rec.semel,
      religion_2019: entry.rec.religion ?? null,
    };
    const want = norm(entry.he);
    const socio = (await load(env, "mcp/socio.json")).find(
      (s) => s.code === entry.rec.semel || norm(s.name) === want);
    if (!socio) {
      out.socio_note =
        "No CBS socio-economic record (covers the 201 municipalities only).";
      return out;
    }
    const { code, name, ...fields } = socio;
    out.socioeconomic_2021 = Object.fromEntries(
      Object.entries(fields).map(([k, v]) => [k, r(v)]));
    return out;
  },

  // ---- ChatGPT deep-research compatibility (search + fetch over localities)

  async search(env, { query }) {
    const [entry, suggestions] = await findLocality(env, query);
    const hits = entry
      ? [{ name: entry.he, name_en: entry.en, semel: entry.rec.semel, _e: entry }]
      : (suggestions || []).map((s) => s);
    const { byKey } = await localityIndex(env);
    const results = hits.slice(0, 8).map((h) => {
      const e = h._e || byKey.get(norm(h.name));
      return {
        id: e.rec.id,
        title: `${e.en || e.he} — Israeli election results 1992-2022`,
        text: `Locality ${e.he}${e.en ? ` (${e.en})` : ""}, semel ` +
          `${e.rec.semel ?? "n/a"}, ${e.rec.elections_count ?? "?"} elections ` +
          "covered. Use fetch with this id for the full bloc-level series.",
        url: SITE,
      };
    });
    return { results };
  },

  async fetch(env, { id }) {
    const { byId } = await localityIndex(env);
    const entry = byId.get(String(id));
    if (!entry) return { error: `Unknown locality id '${id}'. Use search first.` };
    const full = await handlers.get_locality_results(env, { locality: entry.he });
    return {
      id: String(id),
      title: `${entry.en || entry.he} — Israeli election results 1992-2022`,
      text: JSON.stringify(full),
      url: SITE,
      metadata: { source: SOURCES },
    };
  },
};

// ----------------------------------------------------------- tool definitions

const LOCALITY_ARG = {
  type: "string",
  description: "Locality: Hebrew or English name, or semel code.",
};
const KNESSET_ARG = { type: "integer", description: "Knesset number, 13-25." };

const TOOLS = [
  {
    name: "list_elections",
    description:
      "All 13 Knesset elections (K13 1992 - K25 2022): year, turnout and " +
      "national bloc shares, plus the three direct-PM contest years. Call " +
      "this first to learn which Knesset numbers exist and how blocs are " +
      "defined.",
    inputSchema: { type: "object", properties: {}, required: [] },
  },
  {
    name: "search_locality",
    description:
      "Find a locality by Hebrew or English name (or semel code). Returns " +
      "up to 8 matches with both names, the semel code, population and " +
      "religious composition. Use this when unsure of exact spelling.",
    inputSchema: {
      type: "object",
      properties: { query: { type: "string" } },
      required: ["query"],
    },
  },
  {
    name: "get_locality_results",
    description:
      "Election results for one locality: bloc percentages, turnout, " +
      "eligible voters and valid votes. Omit `knesset` for the full " +
      "1992-2022 series, or pass 13-25 for one election. Locality accepts " +
      "Hebrew/English name or semel.",
    inputSchema: {
      type: "object",
      properties: { locality: LOCALITY_ARG, knesset: KNESSET_ARG },
      required: ["locality"],
    },
  },
  {
    name: "get_locality_parties",
    description:
      "Party-level vote shares (percent of valid votes) in one locality " +
      "for one Knesset election (13-25), sorted by share, with estimated " +
      "vote counts (share x valid votes). Party codes are official ballot " +
      "codes; Hebrew and English party names are included. Parties below " +
      "~0.01% locally are omitted.",
    inputSchema: {
      type: "object",
      properties: { locality: LOCALITY_ARG, knesset: KNESSET_ARG },
      required: ["locality", "knesset"],
    },
  },
  {
    name: "get_national_results",
    description:
      "National results for one Knesset election (13-25): every party's " +
      "raw votes, vote share, seats and bloc, plus bloc totals and turnout.",
    inputSchema: {
      type: "object",
      properties: { knesset: KNESSET_ARG },
      required: ["knesset"],
    },
  },
  {
    name: "get_party",
    description:
      "History of one party across 1992-2022: seats, national vote share, " +
      "name and bloc per election, plus its top strongholds (highest local " +
      "share). Accepts a ballot code (e.g. 'מחל') or a Hebrew/English party " +
      "name (e.g. 'Likud', 'העבודה'). Optional `knesset` filters to one " +
      "election.",
    inputSchema: {
      type: "object",
      properties: {
        party: { type: "string" },
        knesset: KNESSET_ARG,
      },
      required: ["party"],
    },
  },
  {
    name: "get_vote_transfers",
    description:
      "Bloc-level vote-transfer matrix between two consecutive Knesset " +
      "elections. `source='ballot'` = ecological inference (constrained " +
      "least squares over ~1,000 localities, includes abstention flows); " +
      "`source='survey'` = INES recalled-vote crosstabs. Rows are the FROM " +
      "bloc and sum to 1; cell = share of the from-bloc's voters going to " +
      "each destination ('dnv' = did not vote). Consecutive pairs only " +
      "(13->14 ... 24->25).",
    inputSchema: {
      type: "object",
      properties: {
        from_knesset: { type: "integer" },
        to_knesset: { type: "integer" },
        source: { type: "string", enum: ["ballot", "survey"], default: "ballot" },
      },
      required: ["from_knesset", "to_knesset"],
    },
  },
  {
    name: "get_pm_direct",
    description:
      "Israel's direct prime-ministerial elections (1996, 1999, 2001): the " +
      "two-candidate result nationally, or in one locality (raw votes, " +
      "shares, turnout). 2001 had a mass Arab boycott and ~21% blank " +
      "ballots -- turnout numbers reflect that.",
    inputSchema: {
      type: "object",
      properties: {
        year: { type: "integer", enum: [1996, 1999, 2001] },
        locality: LOCALITY_ARG,
      },
      required: ["year"],
    },
  },
  {
    name: "get_demographics",
    description:
      "CBS socio-economic profile (2021) for a municipality: income, " +
      "education, age structure, plus religious composition. Available for " +
      "the 201 municipalities only -- small localities return " +
      "religion/population data alone.",
    inputSchema: {
      type: "object",
      properties: { locality: LOCALITY_ARG },
      required: ["locality"],
    },
  },
  {
    name: "search",
    description:
      "Search Israeli localities by name (Hebrew or English). Returns " +
      "matching localities as documents; use `fetch` with a result id for " +
      "the full 1992-2022 election series. (Deep-research compatible.)",
    inputSchema: {
      type: "object",
      properties: { query: { type: "string" } },
      required: ["query"],
    },
  },
  {
    name: "fetch",
    description:
      "Fetch the full 1992-2022 election series for a locality by the id " +
      "returned from `search`. (Deep-research compatible.)",
    inputSchema: {
      type: "object",
      properties: { id: { type: "string" } },
      required: ["id"],
    },
  },
];

// ------------------------------------------------------------- MCP transport

const SUPPORTED_VERSIONS = ["2025-06-18", "2025-03-26", "2024-11-05"];

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers":
    "Content-Type, Authorization, Mcp-Session-Id, MCP-Protocol-Version",
  "Access-Control-Expose-Headers": "Mcp-Session-Id",
};

function rpcResult(id, result) {
  return { jsonrpc: "2.0", id, result };
}

function rpcError(id, code, message) {
  return { jsonrpc: "2.0", id: id ?? null, error: { code, message } };
}

async function handleRpc(env, msg) {
  if (!msg || msg.jsonrpc !== "2.0" || typeof msg.method !== "string")
    return rpcError(msg?.id, -32600, "Invalid Request");
  const { id, method, params = {} } = msg;
  const isNotification = id === undefined;

  try {
    if (method === "initialize") {
      const requested = params.protocolVersion;
      return rpcResult(id, {
        protocolVersion: SUPPORTED_VERSIONS.includes(requested)
          ? requested
          : SUPPORTED_VERSIONS[0],
        capabilities: { tools: { listChanged: false } },
        serverInfo: {
          name: "israeli-elections",
          title: "Israeli Elections 1992-2022",
          version: "1.0.0",
        },
        instructions: INSTRUCTIONS,
      });
    }
    if (isNotification) return null; // notifications/initialized etc.
    if (method === "ping") return rpcResult(id, {});
    if (method === "tools/list")
      return rpcResult(id, {
        tools: TOOLS.map((t) => ({
          ...t,
          annotations: { readOnlyHint: true, openWorldHint: false },
        })),
      });
    if (method === "tools/call") {
      const { name, arguments: args = {} } = params;
      const handler = handlers[name];
      if (!handler || !TOOLS.some((t) => t.name === name))
        return rpcError(id, -32602, `Unknown tool: ${name}`);
      const out = await handler(env, args);
      return rpcResult(id, {
        content: [{ type: "text", text: JSON.stringify(out) }],
        isError: false,
      });
    }
    if (method === "resources/list") return rpcResult(id, { resources: [] });
    if (method === "prompts/list") return rpcResult(id, { prompts: [] });
    return rpcError(id, -32601, `Method not found: ${method}`);
  } catch (e) {
    return rpcError(id, -32603, `Internal error: ${e.message}`);
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === "OPTIONS")
      return new Response(null, { status: 204, headers: CORS });

    if (request.method === "GET") {
      // No server-initiated SSE stream (stateless server); GET / is an
      // info page so the URL can be sanity-checked in a browser.
      if (url.pathname === "/" || url.pathname === "")
        return new Response(
          JSON.stringify({
            name: "israeli-elections MCP server",
            endpoint: "/mcp (MCP Streamable HTTP, POST JSON-RPC)",
            tools: TOOLS.map((t) => t.name),
            dashboard: SITE,
          }, null, 2),
          { headers: { "Content-Type": "application/json", ...CORS } });
      return new Response("Method Not Allowed", { status: 405, headers: CORS });
    }

    if (request.method !== "POST" || !url.pathname.replace(/\/$/, "").endsWith("mcp"))
      return new Response("Not Found", { status: 404, headers: CORS });

    let body;
    try {
      body = await request.json();
    } catch {
      return new Response(JSON.stringify(rpcError(null, -32700, "Parse error")), {
        status: 400,
        headers: { "Content-Type": "application/json", ...CORS },
      });
    }

    const messages = Array.isArray(body) ? body : [body];
    const responses = (
      await Promise.all(messages.map((m) => handleRpc(env, m)))
    ).filter((r) => r !== null);

    if (!responses.length)
      return new Response(null, { status: 202, headers: CORS });

    const payload = Array.isArray(body) ? responses : responses[0];
    return new Response(JSON.stringify(payload), {
      headers: { "Content-Type": "application/json", ...CORS },
    });
  },
};
