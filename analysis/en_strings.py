# -*- coding: utf-8 -*-
"""
en_strings.py — Hebrew -> English translation dictionaries for the *_en.html build
(consumed by analysis/build_english_pages.py).

GLOBAL: strings shared verbatim across pages (sitenav, aria labels, bloc compounds).
PAGES[page]: page-specific strings (headings, prose, chart labels, tooltips).
FIXES[page]: exact structural replacements applied BEFORE translation
             (RTL-specific CSS/JS, reversed chart axes, bidi control chars).

Entries are applied longest-first, plain string replace (no regex).
Rules of thumb:
  * full-sentence / full-phrase entries, keyed on the exact source text;
  * short words only with disambiguating context (">עיר</th>", not "עיר");
  * ballot codes (מחל, פה, שס...) are never translated — they are join keys.
"""

GLOBAL = {
    # sitenav variants across pages
    "ניווט האתר": "Site navigation",
    "לוח מחוונים": "Dashboard",
    "מפה אינטראקטיבית": "Interactive Map",
    "נדידת קולות": "Vote Transfers",
    "דמוגרפיה והצבעה": "Demographics & Voting",
    "ניתוח מפלגות": "Party Analysis",
    "המיון הגאוגרפי": "Geographic Sorting",

    # grand blocs + bloc compounds (safe multi-word forms only; both hyphen and maqaf spellings)
    "ימין-חרדים": "Right-Haredim",
    "ימין־חרדים": "Right-Haredim",
    "מרכז-שמאל-ערבים": "Center-Left-Arabs",
    "מרכז־שמאל־ערבים": "Center-Left-Arabs",
    "ימין אופוזיציוני": "Opposition Right",

    "כנסת": "Knesset",

    # --- redesign slim nav (2026-07-09): full-line entries; current page carries class="on" ---
    "<a class=\"rd-brand\" href=\"index_en.html\">בחירות בישראל <span class=\"rd-yrs\">1992–2022</span></a>":
        "<a class=\"rd-brand\" href=\"index_en.html\">Israeli Elections <span class=\"rd-yrs\">1992–2022</span></a>",
    "<a class=\"rd-brand on\" href=\"index_en.html\">בחירות בישראל <span class=\"rd-yrs\">1992–2022</span></a>":
        "<a class=\"rd-brand on\" href=\"index_en.html\">Israeli Elections <span class=\"rd-yrs\">1992–2022</span></a>",
    "<a href=\"dashboard_en.html\">לוח מחוונים</a>": "<a href=\"dashboard_en.html\">Dashboard</a>",
    "<a class=\"on\" href=\"dashboard_en.html\">לוח מחוונים</a>": "<a class=\"on\" href=\"dashboard_en.html\">Dashboard</a>",
    "<a href=\"election_map_en.html\">מפה ארצית</a>": "<a href=\"election_map_en.html\">National Map</a>",
    "<a class=\"on\" href=\"election_map_en.html\">מפה ארצית</a>": "<a class=\"on\" href=\"election_map_en.html\">National Map</a>",
    "<a href=\"statarea_map_en.html\">מפת שכונות</a>": "<a href=\"statarea_map_en.html\">Neighborhood Map</a>",
    "<a class=\"on\" href=\"statarea_map_en.html\">מפת שכונות</a>": "<a class=\"on\" href=\"statarea_map_en.html\">Neighborhood Map</a>",
    "<a href=\"transfers_en.html\">נדידת קולות</a>": "<a href=\"transfers_en.html\">Vote Transfers</a>",
    "<a class=\"on\" href=\"transfers_en.html\">נדידת קולות</a>": "<a class=\"on\" href=\"transfers_en.html\">Vote Transfers</a>",
    "<a href=\"demographics_en.html\">דמוגרפיה</a>": "<a href=\"demographics_en.html\">Demographics</a>",
    "<a class=\"on\" href=\"demographics_en.html\">דמוגרפיה</a>": "<a class=\"on\" href=\"demographics_en.html\">Demographics</a>",
    "<a href=\"party_analysis_en.html\">מפלגות</a>": "<a href=\"party_analysis_en.html\">Parties</a>",
    "<a class=\"on\" href=\"party_analysis_en.html\">מפלגות</a>": "<a class=\"on\" href=\"party_analysis_en.html\">Parties</a>",
    "<a href=\"findings_en.html\">ממצאים</a>": "<a href=\"findings_en.html\">Findings</a>",
    "<a class=\"on\" href=\"findings_en.html\">ממצאים</a>": "<a class=\"on\" href=\"findings_en.html\">Findings</a>",
    "<a href=\"index_en.html\">דף הבית</a>": "<a href=\"index_en.html\">Home</a>",
    "<a href=\"dashboard_en.html#polls2026\">סקרי 2026</a>": "<a href=\"dashboard_en.html#polls2026\">2026 Polling</a>",
}

PAGES = {
    # ------------------------------------------------------------------ index (landing)
    "index": {
        "בחירות בישראל 1992–2022 · מעבדת חקר": "Israeli Elections 1992–2022 · An Exploration Lab",
        "שלושים שנה · שלושה־עשר פתקים · 1,325 יישובים": "Thirty years · Thirteen ballots · 1,325 localities",
        "המפה הפוליטית של ישראל,<br><em>יישוב־יישוב</em>": "Israel's political map,<br><em>town by town</em>",
        "כל נקודה היא יישוב אמיתי, צבועה לפי תוצאת האמת שלו. גררו את ציר הזמן וצפו איך המדינה ממיינת את עצמה, ואז רדו פנימה: מהמדינה, דרך העיר, עד תיבת הקלפי בשכונה.":
            "Every dot is a real locality, colored by its actual result. Drag the timeline and watch the country sort itself, then go deeper: from the national picture, through the city, down to the neighborhood ballot box.",
        "נגנו את שלושים השנה": "Play the thirty years",
        "בחירת שנת בחירות": "Choose an election year",
        "חפשו יישוב: חיפה, עפולה, רהט…": "Search a locality: Haifa, Afula, Rahat…",
        "רחפו ולחצו על נקודה · <a href=\"election_map_en.html\">המפה המלאה, עם פוליגונים וסיורים ←</a>":
            "Hover and click a dot · <a href=\"election_map_en.html\">the full map, with polygons and tours →</a>",
        "אחוז הצבעה": "Turnout",
        "פתחו במפה הארצית": "Open in the national map",
        # K24 Bennett caveat under the bloc bar (2026-07-11); lands in a single-quoted JS string — keep apostrophe-free
        "מחנה המרכז־שמאל־ערבים של 2021 כולל כאן את ימינה של בנט: כך קמה הממשלה בפועל, וזה בקירוב היתרון שהאופוזיציה תצטרך בבחירות הקרובות; במפה המלאה אפשר לספור אותה בימין.":
            "The 2021 Center-Left-Arab camp here includes Bennett and his Yamina party: that is how the government was actually formed, and this is roughly the margin the opposition will need in the coming election; the full map has an option to count Yamina with the right.",
        "התחילו משאלה": "Start from a question",
        "או תנו למפה לספר סיפור": "Or let the map tell a story",
        "סיורים מודרכים על המפה הארצית: המפה זזה, מצביעה ומסבירה, תחנה אחר תחנה.":
            "Guided tours on the national map: it moves, points and explains, stop by stop.",
        "מה קרה בכל הארץ?": "What happened nationwide?",
        "תוצאות ארציות, בונה קואליציות ומדדי קיטוב לאורך 13 מערכות · לוח המחוונים":
            "National results, a coalition builder and polarization metrics across 13 elections · Dashboard",
        "איך זה נראה על המפה?": "What does it look like on the map?",
        "גושים, מפלגות ותנודות בכל יישוב: פוליגונים, בועות וקרטוגרמה · המפה הארצית":
            "Blocs, parties and swings in every locality: polygons, bubbles, cartogram · National Map",
        "ומה קרה בשכונה שלכם?": "And in your neighborhood?",
        "עשר מערכות ברמת האזור הסטטיסטי, מוצלבות עם מפקדי אוכלוסין · מפת השכונות":
            "Ten elections at statistical-area level, cross-referenced with censuses · Neighborhood Map",
        "לאן נדדו הקולות?": "Where did the votes go?",
        "אומדן מעברי מצביעים בין מערכות סמוכות, מאומת מול סקרי INES · נדידת קולות":
            "Estimated voter movement between adjacent elections, validated against INES surveys · Vote Transfers",
        "מי מצביע למי, ולמה?": "Who votes for whom, and why?",
        "השכלה, שכר, פריון ודתיות מול הצבעה, 1972–2022 · דמוגרפיה והצבעה":
            "Education, wages, fertility and religiosity against the vote, 1972–2022 · Demographics",
        "מה הסיפור של כל מפלגה?": "What's each party's story?",
        "מסלול המנדטים, מעוזי הכוח והפרופיל החברתי־כלכלי · ניתוח מפלגות":
            "Seat trajectory, geographic strongholds and socioeconomic profile · Party Analysis",
        "אז מה השורה התחתונה?": "So what's the bottom line?",
        "ישראל נפרדת לשני מחנות גאוגרפיים: ממצאי המחקר · המיון הגאוגרפי":
            "Israel is separating into two geographic camps: the research findings · Geographic Sorting",
        # stories rail (titles match the en fields in data/map_tours.json)
        "הרחוב הרוסי": "The Russian street",
        "החגורה מחליפה דגלים": "The belt changes flags",
        "הנסיגה הארוכה של השמאל": "The left's long retreat",
        "רכבת ההרים של ההשתתפות הערבית": "The Arab turnout rollercoaster",
        "המנוע החרדי": "The Haredi engine",
        "הדפוס הדרוזי": "The Druze pattern",
        "המהפך של רבין": "The Rabin upheaval",
        "הכרעה על חוט השערה": "A knife-edge decision",
        "<span class=\"qarr\">←</span>": "<span class=\"qarr\">→</span>",
        "מקורות: ועדת הבחירות המרכזית, הלמ\"ס, data.gov.il, סקרי INES · פירוט מלא בעמוד <a href=\"dashboard_en.html\">אודות ומתודולוגיה</a>":
            "Sources: Central Elections Committee, CBS, data.gov.il, INES surveys · Full detail on the <a href=\"dashboard_en.html\">About & Methodology</a> page",
    },
    # ------------------------------------------------------------------ findings
    "findings": {
        # --- neighborhood-level extension (SA common space, 2026-07-09) ---
        "ברזולוציית השכונה: המרחב האלקטורלי המשותף (2003–2022)":
            "At neighborhood resolution: the common electoral space (2003–2022)",
        "הפאנל היישובי שלמעלה נעצר בגבול העיר. ההרחבה הזו יורדת לרמת האזור הסטטיסטי:":
            "The locality panel above stops at the city limits. This extension descends to statistical-area level:",
        "כ-2,400 שכונות בכל מערכת, 10 מערכות (כנסת 16–25), וממקמת את כולן ב<b>מרחב אלקטורלי משותף</b> אחד:":
            "roughly 2,400 neighborhoods per election, 10 elections (Knesset 16–25), and places them all in one <b>common electoral space</b>:",
        "ניתוח גורמים (PCA) על הצבעת כל השכונות בכל המערכות יחד, לפי 13 שושלות מפלגתיות רציפות.":
            "a factor analysis (PCA) of every neighborhood's vote in every election together, over 13 continuous party lineages.",
        "שני צירים מארגנים את המרחב: <b>ערבי–יהודי</b> (46% מהשונות) ו<b>חרדי–חילוני</b> (21%).":
            "Two axes organize the space: <b>Arab–Jewish</b> (46% of variance) and <b>Haredi–secular</b> (21%).",
        "פאנל מאוזן: 2,305 שכונות": "Balanced panel: 2,305 neighborhoods",
        "🗺️ הציר במפה": "🗺️ the axis on the map",
        "🗺️ הפלחים במפה": "🗺️ the segments on the map",
        "הפער בין השכונות על הציר החרדי-חילוני": "The between-neighborhood gap on the Haredi–secular axis",
        "עשירון-90 מול עשירון-10: 33.6 → 48.0 נק׳ מרחב, 2009→2022":
            "90th vs 10th percentile: 33.6 → 48.0 space units, 2009→2022",
        "כוח הניבוי של הדמוגרפיה (R²)": "Demographics' predictive power (R²)",
        "חיזוי %ימין-חרדים של שכונה בעיר שהמודל לא ראה, מ-18 משתני מפקד זהים":
            "Predicting a neighborhood's Right-Haredi share in a city the model never saw, from 18 identical census variables",
        "הקטבים הקפואים (ערבי · חרדי)": "The frozen poles (Arab · Haredi)",
        "שיעור השכונות שנשארו באותו פלח אלקטורלי, 2009→2022":
            "Share of neighborhoods that stayed in the same electoral segment, 2009→2022",
        "פלח \"מעוז העבודה\": חלקו בקולות": "The \"Labor stronghold\" segment: vote share",
        "שיא 2015 → כמעט אפס מ-2021. עוצמת הקריסה יציבה בכל גרסאות הפילוח; מניין השכונות המדויק תלוי-פילוח":
            "2015 peak → near zero from 2021. The collapse magnitude is stable across all segmentations; the exact neighborhood count is not",
        "הציר החרדי-חילוני נפתח כמניפה, גם בתוך הערים":
            "The Haredi–secular axis fans out, inside cities too",
        "פער עשירון-90/עשירון-10 בין השכונות על ציר PC2, פאנל מאוזן. גם הפיזור התוך-עירוני עלה ~17%.":
            "90/10 percentile gap between neighborhoods on the PC2 axis, balanced panel. Within-city dispersion also rose ~17%.",
        "הדמוגרפיה מנבאת את השכונה טוב מתמיד": "Demographics predict the neighborhood better than ever",
        "R² מחוץ-למדגם (ערים מוחזקות בחוץ). בעידן מפקד 2008 הניבוי עולה כשמתרחקים מהמפקד; בעידן 2022, כשמתקרבים אליו. שני הכיוונים מצביעים על מיון אמיתי, לא על ארטיפקט מדידה.":
            "Out-of-sample R² (held-out cities). In the 2008-census era prediction improves moving AWAY from the census date; in the 2022 era, moving TOWARD it. Both directions point to real sorting, not a measurement artifact.",
        "<b>מי זז ומי קפוא:</b> שכונות בני-ברק ומודיעין-עילית זזו 7–12 יחידות מרחב בסך הכל לאורך שמונה מערכות;":
            "<b>Who moves and who is frozen:</b> Bnei Brak and Modi'in Illit neighborhoods moved 7–12 space units in total across eight elections;",
        "הנעים הגדולים הם כפרים דרוזיים (כסרא-סמיע, חורפיש, עראמשה) שנעים עשרות יחידות בין מערכות. רוב התנועה היא תנודה מחזורית ולא נדידה:":
            "the biggest movers are Druze villages (Kisra-Sumei, Hurfeish, Arab al-Aramshe), swinging dozens of units between elections. Most movement is cyclical oscillation, not migration:",
        "חציון היחס תזוזה-נטו/דרך הוא 0.15. המנוע הדמוגרפי של הניבוי התחלף: ב-2009 המשתנה החזק ביותר היה <b>מוצא אירופאי</b>; ב-2022,":
            "the median net-displacement/path ratio is 0.15. The demographic engine of prediction changed hands: in 2009 the strongest variable was <b>European origin</b>; in 2022,",
        "<b>מוצא \"ישראל\" (דור שלישי), חילוניוּת והשכלה</b>. השסע העדתי פינה את מקומו לשסע הדתי-השכלתי כמארגן הגאוגרפיה.":
            "<b>\"Israel\" origin (third generation), secularism and education</b>. The ethnic cleavage gave way to the religiosity-education cleavage as the organizer of the geography.",
        # --- MRP paragraph (2026-07-09) ---
        "<b>מהפרט אל השכונה (MRP):</b> הקשר נבחן גם מלמטה: מודל ברמת הבוחר הבודד (סקר INES‏ 2022, כ-1,100 מצביעים:":
            "<b>From the individual to the neighborhood (MRP):</b> the link was also tested bottom-up: an individual-voter model (INES 2022 survey, ~1,100 voters:",
        "דתיות × השכלה × גיל) הוצמד לכל שכונה דרך תאי מפקד, ונבחן מול תוצאות האמת שלה: ולידציה שכמעט אף יישום MRP בעולם לא יכול להריץ.":
            "religiosity × education × age) was attached to every neighborhood through census cells and tested against its actual results: a validation almost no MRP application anywhere can run.",
        "כשהרכב הדתיות של שכונה נלקח מהקטגוריה הדומיננטית של הלמ\"ס בלבד: R²‏ 0.375 (סטייה ממוצעת 17.1 נק'). כשההרכב המלא":
            "With each neighborhood's religiosity taken from the CBS dominant category alone: R² 0.375 (mean error 17.1 pts). With the full mix",
        "משוחזר סטטיסטית</b> ממאפייני מפקד ניטרליים (פריון, גיל, השכלה, גודל משק בית): R²‏ 0.645 (12.6 נק'); ההרכב המעורב של השכונות, לא המודל,":
            "reconstructed statistically</b> from neutral census characteristics (fertility, age, education, household size): R² 0.645 (12.6 pts); the neighborhoods' mixed composition, not the model,",
        "היה צוואר הבקבוק. השערת פערי ההצבעה בין המגזרים (turnout) נבדקה ונדחתה: בסקר כולם \"הצביעו\" (92%–98% בכל המגזרים), אין גרדיאנט שמיש. מבחן רגישות לכ\"ד הראה שבוחרי ימינה של בנט מתנהגים דמוגרפית כימין לכל דבר, וכך הוגדרו במדדים; תקווה חדשה של סער נותרה בימין האופוזיציוני.":
            "was the bottleneck. The sector-turnout-gap hypothesis was tested and rejected: in the survey everyone \"voted\" (92%–98% in every sector), no usable gradient. A K24 sensitivity test showed Bennett's Yamina voters behave demographically as right in every respect, and are so defined in the metrics; Sa'ar's Tikva Hadasha remains opposition-right.",
        "במפה, <a href=\"statarea_map_en.html#year=2022&amp;mode=pc2\" style=\"color:#9cc4ff\">הציון על הציר מוצג לכל שכונה</a> עם תיוג מכויל לפי חציוני הסיווג הרשמי (חילוני ≈ ‎−9‎, מסורתי ≈ ‎+8‎, חרדי ≈ ‎+56‎).":
            "On the map, <a href=\"statarea_map_en.html#year=2022&amp;mode=pc2\" style=\"color:#9cc4ff\">each neighborhood's axis score is shown</a> with a tag calibrated on the official classification's medians (secular ≈ −9, traditional ≈ +8, Haredi ≈ +56).",
        "אומדני הרכב אורח-החיים הם תוצר מודל (סטיית שכונה בודדת עד 10–20 נק') ואינם נתון רשמי.":
            "The lifestyle-mix estimates are a model product (single-neighborhood error up to 10–20 pts), not an official statistic.",
        "<b>שיטה וזהירות:</b> שושלות המפלגות נקבעו ידנית מול עדויות מטריצות המעבר (מיזוגים → השותף הדומיננטי);":
            "<b>Method &amp; caution:</b> party lineages were set manually against the transfer-matrix evidence (mergers → the dominant partner);",
        "גאומטריות אזורים שונות (2008/2022) גושרו בהצלבה מרחבית, וההשוואות רצות על פאנל מאוזן בלבד. הניבוי נמדד בקיפול-קבוצות לפי יישוב,":
            "different statistical-area geometries (2008/2022) were bridged by spatial crosswalk, and comparisons run on a balanced panel only. Prediction is scored with locality-grouped folds,",
        "המודל נבחן על ערים שלא ראה. ציר PC1 (ערבי–יהודי) הוחרג מטענות המיון: פיזורו מונע ממחזורי השתתפות ערבית, לא ממיון מרחבי. המרחב המאוחד נבדק מול ניתוח פר-מערכתי: בכל 10 המערכות שני הצירים הראשיים זהים כמעט לחלוטין לצירי המערכה עצמה (|cos| ≥ 0.84, מתאם ציונים ≥ 0.91).":
            "the model is tested on cities it never saw. The PC1 (Arab–Jewish) axis is excluded from the sorting claims: its dispersion is driven by Arab turnout cycles, not spatial sorting. The common space was checked against per-election analysis: in all 10 elections the two leading axes are near-identical to the election's own (|cos| ≥ 0.84, score correlation ≥ 0.91).",
        "מעברי פלחים משקפים גם שינוי מפלגתי-מערכתי, לא רק תזוזת שכונות. כרגיל: יחידת הניתוח היא השכונה, לא הבוחר.":
            "Segment transitions reflect party-system change as well as neighborhood movement. As always: the unit of analysis is the neighborhood, not the voter.",
        "'אפר׳ 19','ספט׳ 19'": "'Apr 19','Sep 19'",
        "label:'פער 90/10 על הציר החרדי-חילוני'": "label:'90/10 gap on the Haredi–secular axis'",
        "label:'מפקד 2008'": "label:'Census 2008'",
        "label:'מפקד 2022'": "label:'Census 2022'",
        "המיון הגאוגרפי של ההצבעה בישראל, 1992–2022":
            "The Geographic Sorting of Israel's Vote, 1992–2022",
        "ממצא · פאנל מאוזן של 896 ישובים, כל 13 מערכות הבחירות · משוקלל לפי גודל היישוב":
            "Finding · Balanced panel of 896 localities, all 13 elections · weighted by locality size",
        "ישראל נפרדת לשני מחנות גאוגרפיים":
            "Israel Is Splitting into Two Geographic Camps",
        "בין 1992 ל-2022 הישובים בישראל לא רק החליפו למי הם מצביעים, הם <b>התרחקו זה מזה</b>.":
            "Between 1992 and 2022, Israel's localities didn't just change who they vote for, they <b>drifted apart</b>.",
        "פיזור ההצבעה לימין-חרדים בין הישובים גדל ב-~50%, הפער בין העשירון הימני ביותר לשמאלי ביותר כמעט הוכפל,":
            "The dispersion of the Right-Haredi vote across localities grew ~50%, the gap between the most right-wing and most left-wing deciles nearly doubled,",
        "והבוחרים של שני הגושים נעשו מופרדים גאוגרפית הרבה יותר. <b>הרמות מתפצלות, אבל התנודות מסתנכרנות</b>:":
            "and the two blocs' voters became far more geographically separated. <b>Levels are diverging, but swings are synchronizing</b>:",
        "הישובים זזים יותר ויותר יחד, מנקודות פתיחה שרק הולכות ומתרחקות.":
            "localities increasingly move together, from starting points that keep drifting apart.",
        "התפלגות ההצבעה לימין-חרדים בין הישובים: נפתחת כמניפה":
            "The distribution of the Right-Haredi vote across localities: opening like a fan",
        "רצועה = העשירון ה-10 עד ה-90 של הישובים (משוקלל לפי בוחרים); קו = החציון. ככל שהרצועה מתרחבת, הישובים מתפצלים.":
            "Band = the 10th–90th percentile of localities (voter-weighted); line = the median. The wider the band, the more the localities diverge.",
        "1992 מול 2022: המיון":
            "1992 vs 2022: the sorting",
        "משקל הבוחרים בכל טווח של % ימין-חרדים. 2022 (כתום) מפוזר לקצוות; 1992 (ירוק) מרוכז יותר.":
            "Voter weight in each Right-Haredi % bin. 2022 (orange) spreads to the extremes; 1992 (green) is more concentrated.",
        "הפרדה גאוגרפית בין הגושים ↑":
            "Geographic separation between the blocs ↑",
        "מדד אי-דמיון (dissimilarity) של בוחרי ימין-חרדים מול מרכז-שמאל-ערבים בין הישובים.":
            "Dissimilarity index of Right-Haredi vs Center-Left-Arab voters across localities.",
        "הצד השני: התנודות מתלאמות (נציונליזציה)":
            "The flip side: swings are nationalizing",
        "סטיית תקן (משוקללת) של תנודות ההצבעה בין הישובים, בכל זוג בחירות עוקבות.":
            "Weighted standard deviation of vote swings across localities, for each consecutive election pair.",
        "<b>נמוך יותר = הישובים זזים יותר יחד</b>. ירידה כללית (הפאזה היציבה 2013–2020 בשפל), עם קפיצה בעידן חילופי הגושים 2021–2022.":
            "<b>Lower = localities move more in sync</b>. A general decline (bottoming in the stable 2013–2020 phase), with a jump in the 2021–2022 bloc-turnover era.",
        "7.3→~2.5 בשנות ה-2010": "7.3→~2.5 in the 2010s",
        "ערים במגמות מנוגדות": "Cities on opposite paths",
        "% ימין-חרדים לאורך זמן.": "Right-Haredi % over time.",
        "אדום = התרחקו שמאלה": "red = moved left",
        "כחול = התרחקו ימינה": "blue = moved right",
        "מה מסביר את הכיוון? השכלה, חילוניות וחרדיות":
            "What explains the direction? Education, secularism and Harediness",
        # footer
        "שיטה:": "Method:",
        "פאנל מאוזן של 896 ישובים המופיעים בכל 13 מערכות הבחירות (כנסת 13–25, 1992–2022).":
            "a balanced panel of 896 localities present in all 13 elections (Knesset 13–25, 1992–2022).",
        "כל המדדים <span class=\"hl\">משוקללים לפי מספר בעלי זכות הבחירה</span> בכל יישוב, כך שערים גדולות שוקלות יותר מקיבוצים.":
            "All metrics are <span class=\"hl\">weighted by registered voters</span> in each locality, so large cities weigh more than kibbutzim.",
        "\"מיון\" נמדד כפיזור/הפרדה של ההצבעה <b>בין</b> הישובים (לא בתוכם; לכך נדרש מפלס תת-עירוני).":
            "\"Sorting\" is measured as dispersion/separation of the vote <b>between</b> localities (not within them; that requires a sub-municipal layer).",
        "מגמות המיון עקביות וחזקות (R²≥0.80); הנציונליזציה חלשה ורועשת יותר. יחידת הניתוח היא היישוב, ולא הבוחר הבודד (זהירות מ\"כשל אקולוגי\").":
            "The sorting trends are consistent and strong (R²≥0.80); nationalization is weaker and noisier. The unit of analysis is the locality, not the individual voter (beware the \"ecological fallacy\").",
        # JS: stat cards
        "פיזור ההצבעה לימין-חרדים בין הישובים": "Dispersion of the Right-Haredi vote across localities",
        "סטיית תקן ${S.wsd_rh[0]}": "SD ${S.wsd_rh[0]}",
        "פער בין העשירון הימני לשמאלי (נק׳ אחוז)": "Gap between right-most and left-most deciles (pp)",
        "כמעט הוכפל": "nearly doubled",
        "מדד ההפרדה הגאוגרפית בין הגושים": "Geographic segregation index between the blocs",
        "% ב-30 שנה": "% in 30 years",
        "סטיית תקן של התנודות המקומיות": "SD of local swings",
        "ירדה → תנודות מסונכרנות": "fell → synchronized swings",
        # JS: charts
        "עשירון 90": "90th percentile",
        "עשירון 10": "10th percentile",
        "חציון": "Median",
        "% מהבוחרים": "% of voters",
        "% ימין-חרדים ביישוב": "Right-Haredi % in the locality",
        "מדד הפרדה": "Segregation index",
        "סטיית תקן של תנודות מקומיות": "SD of local swings",
        "פיזור התנודות": "Swing dispersion",
        "התרחקו שמאלה ↓": "Moved left ↓",
        "התרחקו ימינה ↑": "Moved right ↑",
        # JS: mechanism note (template-literal segments around interpolations)
        "בערים היהודיות (": "In Jewish cities (",
        "), המהלך <b style=\"color:#e74c3c\">שמאלה חזק ככל שההשכלה גבוהה</b> (r=":
            "), the <b style=\"color:#e74c3c\">leftward move is stronger the higher the education</b> (r=",
        " עם % אקדמאים), הפוריות נמוכה (r=+": " with % academics), the lower the fertility (r=+",
        " עם 4+ ילדים), וההצבעה החרדית נמוכה (r=+": " with 4+ children), and the lower the Haredi vote (r=+",
        "). הערים החרדיות (ירושלים, בית שמש, בני ברק) נעו ימינה, וזה נראה ישירות בהצבעה החרדית (ש\"ס+יהדות התורה). (ערי העלייה מברה\"מ/פריפריה, כמו באר שבע, נעו ימינה במנגנון שלישי (קפיצת 1996) ואינן בין הדוגמאות כאן.)":
            "). The Haredi cities (Jerusalem, Beit Shemesh, Bnei Brak) moved right, and this shows directly in the Haredi vote (Shas+UTJ). (FSU-immigration/periphery cities like Be'er Sheva moved right via a third mechanism (the 1996 jump) and are not among the examples here.)",
        "% אקדמאים, מהלך ": "% academics, move ",
        "% אקדמאים (השכלה)": "% academics (education)",
        # JS: profiles table
        "haredi:'חרדי'": "haredi:'Haredi'",
        "'חילוני-משכיל'": "'Secular-educated'",
        "'פריפריה'": "'Periphery'",
        ">עיר</th>": ">City</th>",
        ">% אקדמאים</th>": ">% academics</th>",
        ">% 4+ ילדים</th>": ">% 4+ children</th>",
        ">הצבעה חרדית</th>": ">Haredi vote</th>",
        ">המהלך</th>": ">Move</th>",
        ">סוג</th>": ">Type</th>",
        # literature-context panel (2026-07-03, sourced from the Elections-in-Israel series digest)
        "הממצא מול ספרות המחקר": "The Finding vs. the Research Literature",
        "סדרת הכרכים האקדמית The Elections in Israel, ספר מערכת המפלגות ומחקרי הקיטוב מספקים את התמונה ברמת הבוחר הבודד ומערכת המפלגות. הם אינם מודדים גאוגרפיה של יישובים, ודווקא לכן חשוב שהתמונות מתלכדות: יציבות גושית לצד סערה מפלגתית.":
            "The academic volume series The Elections in Israel, the party-system book and the polarization literature provide the picture at the level of the individual voter and the party system. They do not measure locality geography, which is exactly why the convergence matters: bloc stability alongside party-level turbulence.",
        "<b>אי-מערכת מפלגתית, גושים יציבים.</b> ספרות מערכת המפלגות מאבחנת את ישראל שאחרי 2003 כאי-מערכת (non-system): מפת מפלגות שמשתנה מדי מערכת בחירות, ללא מבנה יציב, אך לצד יציבות גושית גבוהה. הממצא בעמוד זה הוא הבבואה הגאוגרפית של אותה אבחנה: הרמות הגושיות של היישובים מתרחקות בהתמדה, בעוד התנודות בין מערכות מסתנכרנות ארצית. <span class=\"cite\">[The Parties in Israel 1992–2021, עמ׳ 720–723]</span>":
            "<b>A party non-system, stable blocs.</b> The party-system literature diagnoses post-2003 Israel as a non-system: a party map that changes every election, with no stable structure, yet alongside high bloc stability. The finding on this page is the geographic mirror of that diagnosis: localities' bloc levels drift steadily apart while between-election swings synchronize nationally. <span class=\"cite\">[The Parties in Israel 1992–2021, pp. 720–723]</span>",
        "<b>העוגן ברמת הבוחר: שיא התנודתיות של 2006.</b> נתוני INES בכרך 2006 מציבים את אותה מערכה כשיא: אי-יציבות מפלגתית של 42.7% ו-63% מהבוחרים שהחליפו מפלגה, אך אי-היציבות הגושית עלתה הרבה פחות; הבוחרים שיחררו את הזיקה למפלגה מבלי לנטוש את מבנה הגושים. זו המקבילה הפרטנית לממצא היישובי כאן. <span class=\"cite\">[The Elections in Israel 2006, פרק קדימה]</span>":
            "<b>The individual-level anchor: the 2006 volatility peak.</b> INES data in the 2006 volume place that election at the peak: party instability of 42.7% and 63% of voters switching parties, while bloc instability rose far less; voters loosened their party ties without abandoning the bloc structure. That is the individual-level counterpart of the locality finding here. <span class=\"cite\">[The Elections in Israel 2006, Kadima chapter]</span>",
        "<b>השסע יציב, ולכן המיון בר-משמעות.</b> אריאן ושמיר מראים שמבנה השסעים שהתגבש ב-1977 (עתיד השטחים והזהות הקולקטיבית) נותר על כנו גם בעשור הסוער 1996–2006: סולמות הזהות יציבים, וגם קדימה הייתה מרכז בתוך השסע הישן ולא ממד חדש. מיון גאוגרפי לאורך ציר ימין-חרדים מודד אפוא התמיינות לאורך ממד יציב ובעל משמעות, לא ארטיפקט של תוויות מפלגתיות מתחלפות. <span class=\"cite\">[Arian &amp; Shamir 2008]</span>":
            "<b>The cleavage is stable, so the sorting is meaningful.</b> Arian and Shamir show that the cleavage structure formed in 1977 (the future of the territories and collective identity) held even through the turbulent 1996–2006 decade: the identity scales stayed stable, and even Kadima was a center within the old cleavage rather than a new dimension. Geographic sorting along the Right-Haredi axis therefore measures movement along a stable, meaningful dimension, not an artifact of churning party labels. <span class=\"cite\">[Arian &amp; Shamir 2008]</span>",
        "<b>גם ב-2022 השסע מנבא.</b> כרך 2022 מדווח שהפערים האידאולוגיים הגדולים ביותר הם בסוגיות הסכסוך, דת-ומדינה ובית-המשפט העליון, וסוגיות שסע-הזהות ניבאו הצבעה טוב יותר מעמדות חברתיות-כלכליות. עקבי עם פאנל המנגנון למעלה: השכלה, פריון וחרדיות מתואמים עם כיוון התנועה של הערים, אבל תוכן השסע שממיין אותן הוא זהותי. <span class=\"cite\">[The Elections in Israel 2022, עמ׳ 31–32]</span>":
            "<b>In 2022, too, the cleavage predicts.</b> The 2022 volume reports that the largest ideological gaps are over the conflict, religion-state and the Supreme Court, and that identity-cleavage issues predicted vote choice better than socioeconomic positions. Consistent with the mechanism panel above: education, fertility and Harediness correlate with the direction cities move, but the content of the cleavage doing the sorting is identity. <span class=\"cite\">[The Elections in Israel 2022, pp. 31–32]</span>",
        "<b>הסתייגות ההשתתפות.</b> הספרות מתעדת שינוי משטר-השתתפות אחרי 2001: 67.8% ב-2003, 63.5% ב-2006 (השפל עד אז) ו-64.7% ב-2009, לעומת כ-80% בעשורים הקודמים, ומפרשת את ההימנעות כמיאוס נסיבתי, לא כדחיית המוסדות הדמוקרטיים. מפת המיון שאחרי 2003 היא אפוא גם מפה של השתתפות נמוכה יותר, ושורת הלא-מצביעים במטריצות המעבר מקבלת משנה חשיבות. <span class=\"cite\">[The Elections in Israel 2003, עמ׳ 17–19 · 2006, מבוא · 2009, עמ׳ 26]</span>":
            "<b>The participation caveat.</b> The literature documents a turnout-regime change after 2001: 67.8% in 2003, 63.5% in 2006 (the low point until then) and 64.7% in 2009, versus roughly 80% in earlier decades, and reads the abstention as circumstance-specific disaffection, not rejection of democratic institutions. The post-2003 sorting map is therefore also a lower-participation map, and the did-not-vote row of the transfer matrices matters all the more. <span class=\"cite\">[The Elections in Israel 2003, pp. 17–19 · 2006, introduction · 2009, p. 26]</span>",
        "<b>המקבילה הרגשית.</b> פאנל הקיטוב הישראלי (עשרה גלים, 2019–2021) מודד את הקיטוב גם כרגש (מדחומי מפלגות, מרחק חברתי ורגש כלפי נתניהו) ומתעד ציר מארגן שנדד חלקית משמאל-ימין אל בעד/נגד נתניהו. ההפרדה הגאוגרפית הנמדדת כאן היא הביטוי המרחבי של מערכת שהספרות מתארת כמקוטבת גם רגשית. <span class=\"cite\">[<a href=\"https://doi.org/10.1016/j.electstud.2022.102512\" target=\"_blank\">Electoral Studies 2022 — Israel Polarization Panel</a>]</span>":
            "<b>The affective counterpart.</b> The Israel Polarization Panel (ten waves, 2019–2021) measures polarization as affect too (party thermometers, social distance and feelings toward Netanyahu) and documents an organizing axis that partly shifted from left-right to pro/anti-Netanyahu. The geographic separation measured here is the spatial expression of a system the literature describes as affectively polarized as well. <span class=\"cite\">[<a href=\"https://doi.org/10.1016/j.electstud.2022.102512\" target=\"_blank\">Electoral Studies 2022 — Israel Polarization Panel</a>]</span>",
        "המקורות: הסדרה שייסדו אשר אריאן ומיכל שמיר, The Elections in Israel (כרכי 1992–2022); The Parties in Israel 1992–2021; מאמר השסעים של אריאן ושמיר (2008); ומאמר פאנל הקיטוב הישראלי (<a href=\"https://doi.org/10.1016/j.electstud.2022.102512\" target=\"_blank\">Electoral Studies, 2022</a>). מספרי העמודים מפנים למהדורות הדיגיטליות.":
            "Sources: the series founded by Asher Arian and Michal Shamir, The Elections in Israel (1992–2022 volumes); The Parties in Israel 1992–2021; Arian and Shamir's cleavage-structure article (2008); and the Israel Polarization Panel article (<a href=\"https://doi.org/10.1016/j.electstud.2022.102512\" target=\"_blank\">Electoral Studies, 2022</a>). Page numbers refer to the digital editions.",
        # ---- direct-PM split-ticket panel (2026-07) ----
        "<h2>ניסוי טבעי: שני פתקים בקלפי אחת (1996–2001)</h2>":
            "<h2>A natural experiment: two ballots in one polling booth (1996–2001)</h2>",
        "בבחירות 1996 ו-1999 החזיק כל בוחר שני פתקים: אחד לכנסת ואחד לראש הממשלה. זו הפעם היחידה שבה אפשר למדוד את הפער בין הקול הגושי לקול האישי יישוב-יישוב, מתוצאות אמת ולא מסקרים. כל נקודה = יישוב (גודל = מספר המצביעים): ציר X = הקול לגוש הימין-חרדים בכנסת; ציר Y = הקול למועמד הימין לראשות הממשלה (שניהם מנורמלים דו-גושית). יישוב שיושב על האלכסון לא פיצל את הקול.":
            "In the 1996 and 1999 elections every voter held two ballots: one for the Knesset and one for the prime minister. This is the only time the gap between the bloc vote and the personal vote can be measured locality by locality, from real results rather than surveys. Each dot is a locality (size = number of voters): X axis = the vote for the right-Haredi bloc on the Knesset ballot; Y axis = the vote for the right's PM candidate (both normalized two-way). A locality sitting on the diagonal did not split its ticket.",
        "פער שיטתי ‎−4‎ עד ‎−5‎ נק׳": "systematic gap −4 to −5 pts",
        "<b>הגאוגרפיה הגושית שרדה את הפתק האישי (r=0.98–0.99), אבל עם פער שיטתי:</b> מועמד הימין רץ כמעט בכל מקום 4–5 נק׳ מאחורי הגוש שלו. ב-1996 הרוב הגושי בכנסת (54.3% דו-גושי) בלע את הפער: נתניהו ניצח עם 50.5%; ב-1999 הגוש ירד ל-48.6%, ופער אישי דומה (‎−4.8‎ ארצית) הפך למפולת: ברק 56.1%. הפיצול גם התרחב בין שתי המערכות: הפער המוחלט הממוצע (משוקלל) עלה מ-4.3 ל-5.1 נק׳, ומשקל הקולות ביישובים הרחוקים יותר מ-5 נק׳ מהאלכסון עלה משליש (32%) לכמעט מחצית (42%).":
            "<b>Bloc geography survived the personal ballot (r=0.98–0.99), but with a systematic gap:</b> the right's candidate ran 4–5 points behind his own bloc almost everywhere. In 1996 the bloc's Knesset majority (54.3% two-bloc) absorbed the gap: Netanyahu won with 50.5%; in 1999 the bloc fell to 48.6%, and a similar personal gap (−4.8 nationally) became a landslide: Barak 56.1%. The splitting also widened between the two contests: the weighted mean absolute gap rose from 4.3 to 5.1 points, and the share of votes in localities more than 5 points off the diagonal grew from a third (32%) to nearly half (42%).",
        "<b>מי פיצל?</b> הפער השלילי התרכז ביישובים היהודיים (ממוצע משוקלל ‎−4.8‎ ב-96, ‎−5.3‎ ב-99), ובראשם עיירות הפיתוח של 1999 (נתיבות ‎−10.1‎, דימונה ‎−11.1‎, אשקלון ‎−10.8‎), המקומות שבהם ש\"ס נסקה באותו יום לשיא של 17 מנדטים; הדרוזים פיצלו חזק מכולם ב-99 (‎−11.2‎ בממוצע): רשימות הגוש הימני-חרדי לכנסת, ברק לרה\"מ. ביישובים ערביים שבהם ש\"ס קיבלה קולות התופעה קיצונית: בכפר מנדא הגוש הימני-חרדי קיבל 30.2% מהקול הדו-גושי לכנסת, ונתניהו 1.5% בלבד מהקול לרה\"מ. הפיצול החיובי המרוכז היחיד: רמת הגולן ב-1996: ביישובים החילוניים שהצביעו מרכז-שמאל לכנסת (ובהם בוחרי \"Third Way\", שנכללת כאן בגוש המרכז), נתניהו קיבל פי כמה מקול הגוש: אורטל 5.8%→42.9%, כנף 13.3%→50.0%.":
            "<b>Who split?</b> The negative gap was concentrated in Jewish localities (weighted mean −4.8 in 96, −5.3 in 99), led by the development towns of 1999 (Netivot −10.1, Dimona −11.1, Ashkelon −10.8), the very places where Shas surged that same day to its 17-seat peak; the Druze split hardest of all in 99 (−11.2 on average): right-Haredi bloc lists for the Knesset, Barak for PM. In Arab localities where Shas drew votes the phenomenon is extreme: in Kafr Manda the right-Haredi bloc took 30.2% of the two-bloc Knesset vote, and Netanyahu just 1.5% of the PM vote. The only concentrated positive split: the Golan Heights in 1996: in the secular localities that voted center-left for the Knesset (among them Third Way voters, counted here in the center bloc), Netanyahu took several times the bloc vote: Ortal 5.8%→42.9%, Kanaf 13.3%→50.0%.",
        ">מפת הפיצול המלאה</a>": ">The full split-ticket map</a>",
        ">שלוש המערכות במצב הבחירה הישירה במפה הארצית</a>": ">All three contests in the national map, direct-election mode</a>",
        "<b>אפילוג 2001:</b> הניסוי הסתיים בבחירות מיוחדות לרה\"מ בלבד: פתק אחד, בלי כנסת. הציבור הערבי החרים: ההצבעה ביישובים הערביים צנחה מ-76.1% ל-14.1% (אום אל-פחם: 74.5%→4.1%), חמישית (20.8%) מהמעטים שהגיעו הטילו פתק לבן, ומבין הקולות הכשרים ברק קיבל עדיין 81.4%. שיטת הבחירה הישירה בוטלה באותה שנה. ספרות המחקר מזהה במנגנון הזה בדיוק את מה שהמפה מודדת: ההצבעה הכפולה הגדילה את פיצול הקול, שהיה בולט ב-1999 יותר מב-1996, ושימשה כלי לביטוי סקטוריאלי, אידאולוגי ומחאתי; ומכאן גם שיאה של ש\"ס ב-1999.":
            "<b>Epilogue, 2001:</b> the experiment ended with a special PM-only election: one ballot, no Knesset. The Arab public boycotted: turnout in Arab localities collapsed from 76.1% to 14.1% (Umm al-Fahm: 74.5%→4.1%), a fifth (20.8%) of the few who did come cast blank ballots, and of the valid votes Barak still took 81.4%. Direct election was repealed that same year. The research literature identifies in this mechanism exactly what the map measures: the double ballot increased ticket splitting, which was more pronounced in 1999 than in 1996, and served as an instrument of sectoral, ideological and protest expression; hence also the 1999 Shas peak.",
        "[The Elections in Israel 1999, עמ׳ 11, 53–72 · The Parties in Israel 1992–2021, עמ׳ 728–733]":
            "[The Elections in Israel 1999, pp. 11, 53–72 · The Parties in Israel 1992–2021, pp. 728–733]",
        "<b>שיטה וזהירות:</b> תוצאות הבחירה הישירה נקלטו מקבצי התוצאות הרשמיים ברמת היישוב (OCR + אימות אריתמטי מלא; כ-99% מהקולות; ללא מעטפות כפולות: חיילים, שליחויות ובתי חולים). ההשוואה דו-גושית מול דו-מועמדית; יחידת הניתוח היא היישוב ולא הבוחר; פער יישובי אינו מוכיח אילו בוחרים ספציפיים פיצלו (זהירות מכשל אקולוגי).":
            "<b>Method and caution:</b> the direct-election results were captured from the official locality-level result volumes (OCR + full arithmetic verification; ~99% of votes; without the double-envelope vote: soldiers, embassies and hospitals). The comparison is two-bloc vs two-candidate; the unit of analysis is the locality, not the voter; a locality-level gap does not prove which specific voters split (beware the ecological fallacy).",
        # JS strings of the scatter (apostrophe-free values — they live in single-quoted JS)
        "${c.raw.name} (${c.dataset.label}): כנסת ${c.raw.x}% ← רה\"מ ${c.raw.y}%":
            "${c.raw.name} (${c.dataset.label}): Knesset ${c.raw.x}% → PM ${c.raw.y}%",
        "text:'ימין-חרדים בכנסת (דו-גושי)'": "text:'Right-Haredi bloc, Knesset vote (two-bloc)'",
        "text:'מועמד הימין לרה\"מ (דו-מועמדי)'": "text:'Right candidate for PM (two-candidate)'",
    },
    # ------------------------------------------------------------------ transfers
    "transfers": {
        "נדידת קולות בין מערכות בחירות, 1992–2022":
            "Vote Transfers Between Elections, 1992–2022",
        "אומדן מעברי מצביעים בין מערכות בחירות סמוכות, 1992–2022 · רמת יישוב":
            "Estimated voter flows between consecutive elections, 1992–2022 · locality level",
        "> גושים</label>": "> Blocs</label>",
        "> מפלגות (ניסיוני)</label>": "> Parties (experimental)</label>",
        # NOTE: the name-literal pass replaces "לא הצביעו" (a names_en key) before the
        # dictionary runs — these entries are keyed on the post-pass text.
        "כולל \"Did not vote\"": "include \"Did not vote\"",
        "> אומדן יישובי</label>": "> Locality estimate</label>",
        "> סקרי INES</label>": "> INES surveys</label>",
        "> פאנל IPP</label>": "> IPP panel</label>",
        "מקור: <b>פאנל IPP (": "Source: <b>IPP panel (",
        "הצלבה מול פאנל IPP: <b>r=": "Cross-check vs the IPP panel: <b>r=",
        "🧪 פאנל אמיתי: אותם משיבים דיווחו אחרי כל מערכת בחירות, ללא הטיית זיכרון (מדגם יהודי, לא משוקלל)":
            "🧪 True panel: the same respondents reported after each election, no recall bias (Jewish sample, unweighted)",
        "<b>שכבת אימות שלישית, פאנל IPP:</b> לארבעת המעברים של 2019–2022 מוצג אומדן עצמאי שלישי, מתוך ה-Israel Polarization Panel (גדרון, שפר ומור): פאנל של אותם משיבים שדיווחו על הצבעתם <b>אחרי כל מערכת בחירות</b>, ולכן חף לחלוטין מהטיית זיכרון (כ-900–1,400 משיבים למעבר). המדגם יהודי בלבד ואינו משוקלל; רמות התמיכה בו מוטות, אך הנרמול לשורות סופג את רוב ההטיה, והשיפועים החברתיים בו תואמים את INES 2022 כמעט אחד-לאחד (פער ההשכלה: 21.5 מול 21.2 נק'). התאמת הפאנל לאומדן היישובי בארבעת המעברים: r=0.96–0.97, פער משוקלל ממוצע כ-4 נק', האישוש ההדוק ביותר שיש לשיטה האקולוגית בעמוד זה. שורת \"Did not vote\" נשענת על דגלוני ההצבעה של הפאנל; בבחירות 2020 הדגלון נשאל בגל העוקב.":
            "<b>A third validation layer, the IPP panel:</b> for the four 2019–2022 transitions a third independent estimate is shown, from the Israel Polarization Panel (Gidron, Sheffer &amp; Mor): a panel of the same respondents reporting their vote <b>after each election</b>, hence entirely free of recall bias (~900–1,400 respondents per transition). The sample is Jewish-only and unweighted; its support levels are skewed, but row-normalization absorbs most of the bias, and its social gradients match INES 2022 almost one-to-one (education gap: 21.5 vs 21.2 pts). Panel-vs-ecological agreement across the four transitions: r=0.96–0.97, weighted mean gap ~4 pts, the tightest corroboration the ecological method has on this page. The did-not-vote row rests on the panel&#39;s voting flags; for the 2020 election the flag was asked in the following wave.",
        "<b>ציטוט פאנל IPP</b> (שכבת האימות השלישית, מעברי 2019–2022):":
            "<b>IPP panel citation</b> (the third validation layer, 2019–2022 transitions):",
        # method section
        "מתודולוגיה בקצרה": "Methodology in brief",
        "המטריצות נאמדות בשיטת ריבועים פחותים עם אילוצים (הסקה אקולוגית): מחפשים את טבלת-המעבר הארצית שממזערת את שגיאת החיזוי על פני כ-1,000–1,150 יישובים משותפים לשתי מערכות הבחירות, בכפוף לאי-שליליות ולסכומי-שורה השווים לגידול ציבור הבוחרים (כך שגידול דמוגרפי, למשל העלייה מברה\"מ בשנות ה-90, לא נרשם כזרימות מדומות).":
            "The matrices are estimated by constrained least squares (ecological inference): the estimator searches for the national transfer table that minimizes prediction error across the ~1,000–1,150 localities common to both elections, subject to non-negativity and to row sums equal to electorate growth (so demographic growth, e.g. the 1990s FSU immigration wave, is not recorded as phantom flows).",
        "<b>מגבלה מהותית:</b> ההנחה היא שדפוס המעבר אחיד בין יישובים (\"טבלה ארצית אחת\"). זו פשטה מודעת: הנתונים הם צבירים יישוביים, לא מצביעים בודדים (כשל אקולוגי). מבחן פיצול לפי מגזר (ערבי/יהודי) רץ על כל מעבר; במעברים שבהם נמצאה סטייה מוצגת אזהרה. שיוך מפלגות לגושים הוא פר-מערכת בחירות; חלק מ\"תנועת הגושים\" משקף סיווג-מחדש של מפלגה (למשל כולנו) ולא מעבר מצביעים; תצוגת המפלגות מפרידה זאת.":
            "<b>A fundamental limitation:</b> the assumption is that the transfer pattern is uniform across localities (\"one national table\"). This is a deliberate simplification: the data are locality aggregates, not individual voters (ecological fallacy). A sector split test (Arab/Jewish) runs on every transition; transitions with a detected divergence display a warning. Party-to-bloc assignment is per election; some of the \"bloc movement\" reflects a party's reclassification (e.g. Kulanu) rather than voter movement; the party view separates this.",
        "רצועות דקות מוסתרות לניקיון התצוגה. רווחי-סמך (95%) מבוססי bootstrap על דגימת יישובים מחדש; הם מודדים דיוק סטטיסטי בלבד, לא את תקפות הנחת האחידות. בבחירות 2006 חסר מרשם בוחרים יישובי, והוא נאמד כממוצע 2003/2009 (מסומן).":
            "Thin ribbons are hidden for display clarity. Confidence intervals (95%) are bootstrap-based, resampling localities; they measure statistical precision only, not the validity of the uniformity assumption. The 2006 election lacks a locality-level voter registry, and is estimated as the 2003/2009 average (flagged).",
        "<b>שכבת אימות מסקרי INES:</b> לכל מעבר מוצג אומדן עצמאי שני, מסקרי מדד הבחירות הישראלי (INES): הצלבה משוקללת של ההצבעה המדווחת בבחירות הנוכחיות מול ההצבעה הקודמת כפי שנזכרה (כ-500–1,500 משיבים למעבר; משיבים שלא היו זכאים בבחירות הקודמות הוחרגו: עולים וצעירים אינם \"עוברים\"). מעבר אפריל→ספטמבר 2019 מבוסס <b>פאנל אמיתי</b> (אותם משיבים נשאלו אחרי שתי מערכות הבחירות), ולכן חף מהטיית זיכרון; השוואתו לאומדן מבוסס-זיכרון של אותו מעבר (מגל 2020) מודדת את ההטיה ישירות: פער של 6–19 נק' לשורה. באופן שיטתי, הסקרים מפחיתים הימנעות (דיווח-יתר על הצבעה) ומחליקים את המטריצה (זיכרון נוטה אל המנצח), בעוד האומדן האקולוגי נוטה לפתרונות-פינה (0% או 100% בתא). התאמת שני האומדנים: r=0.78–1.00, פער משוקלל ממוצע 2–10 נק'; כל אחד מהם משמש בקרת-שפיות לשני.":
            "<b>Validation layer from the INES surveys:</b> each transition also shows a second, independent estimate from the Israel National Election Studies (INES) surveys: a weighted crosstab of the reported current vote against the recalled previous vote (~500–1,500 respondents per transition; respondents not eligible in the previous election are excluded: immigrants and the newly-of-age are not \"movers\"). The April→September 2019 transition is based on a <b>true panel</b> (the same respondents were interviewed after both elections) and is therefore free of recall bias; comparing it to a recall-based estimate of the same transition (from the 2020 wave) measures that bias directly: a 6–19 pp gap per row. Systematically, surveys understate abstention (over-reporting of voting) and smooth the matrix (recall drifts toward the winner), while the ecological estimate tends to corner solutions (0% or 100% cells). Agreement between the two estimates: r=0.78–1.00, weighted mean gap 2–10 pp; each serves as a sanity check on the other.",
        "<b>קרדיט לשיטה:</b> <a href=\"https://kolot-nodedim.netlify.app/\" target=\"_blank\">הראל קין (קולות נודדים)</a> ואיתמר מושקין. מימוש עצמאי על נתוני יישובים; התוצאות כאן תואמות את אומדני רמת-הקלפי של קין במעברים החופפים (r=0.99).":
            "<b>Method credit:</b> <a href=\"https://kolot-nodedim.netlify.app/\" target=\"_blank\">Harel Cain (Kolot Nodedim)</a> and Itamar Mushkin. An independent implementation on locality data; the results here match Cain's ballot-box-level estimates on the overlapping transitions (r=0.99).",
        "<b>ציטוט סקרי INES</b> (שכבת האימות משתמשת במחקרי הבחירות 1996–2022; הפורמט הרשמי):":
            "<b>Citing the INES studies</b> (the validation layer uses the 1996–2022 election studies; official format):",
        "<b>אימות מול הספרות:</b> את מעבר 2003→2006 אפשר להצליב עם נתוני פאנל INES שפורסמו בכרך 2006 של סדרת The Elections in Israel: 42% מקולות קדימה הגיעו ממצביעי ליכוד 2003, 23% מהעבודה, 17% משינוי ו-4% ממצביעים חדשים. שכבת הסקרים בעמוד זה מתלכדת עם התמונה הזו (32% ממצביעי גוש הימין של 2003 עברו למרכז), ואילו תצוגת המפלגות האקולוגית סוטה ממנה מהותית באותו מעבר (מוצגת אזהרה): המחשה חיה למגבלת הנחת האחידות ולערכה של שכבת אימות עצמאית.":
            "<b>Validation against the literature:</b> the 2003→2006 transition can be cross-checked against INES panel data published in the 2006 volume of The Elections in Israel: 42% of Kadima's votes came from 2003 Likud voters, 23% from Labor, 17% from Shinui and 4% from new voters. The survey layer on this page converges with that picture (32% of the 2003 right bloc moved to the center), while the ecological party view deviates from it substantially on that transition (a warning is shown): a live illustration of the uniformity assumption's limits and of the value of an independent validation layer.",
        "⚠️ מעבר 2003→2006 בתצוגת המפלגות: האומדן היישובי מייחס את רוב קולות קדימה לשינוי (59%) ומעט לליכוד (14%), אך נתוני פאנל INES שבספרות הפוכים: 42% מקולות קדימה ממצביעי ליכוד 2003, 23% מהעבודה ו-17% משינוי. זהו כשל פתרון-פינה מוכר של הסקה אקולוגית בין מפלגות בעלות פריסה גאוגרפית דומה; העדיפו כאן את תצוגת הגושים, המתלכדת עם הסקרים (The Elections in Israel 2006, פרק קדימה).":
            "⚠️ The 2003→2006 transition in party view: the locality-based estimate attributes most Kadima votes to Shinui (59%) and few to Likud (14%), but the INES panel data in the literature are the reverse: 42% of Kadima votes came from 2003 Likud voters, 23% from Labor and 17% from Shinui. This is a known corner-solution failure of ecological inference between parties with similar geographic footprints; prefer the bloc view here, which converges with the surveys (The Elections in Israel 2006, Kadima chapter).",
        # stats bar
        "גל סקר: <b>INES": "Survey wave: <b>INES",
        "משיבים: <b>": "Respondents: <b>",
        "שקלול: <b>": "Weighting: <b>",
        "'ללא'": "'none'",
        "רווחי-סמך: <b>bootstrap ×": "Confidence intervals: <b>bootstrap ×",
        "התאמה לאומדן היישובי: <b>r=": "Agreement with the locality estimate: <b>r=",
        "פער ממוצע <b>": "mean gap <b>",
        "🧪 פאנל אמיתי (אפריל→ספטמבר 2019), ללא הטיית זיכרון":
            "🧪 True panel (April→September 2019), no recall bias",
        "יישובים משותפים: <b>": "Common localities: <b>",
        "גידול ציבור הבוחרים: <b>×": "Electorate growth: <b>×",
        "התאמה לאומדני קין (קלפי): <b>r=": "Agreement with Cain's estimates (ballot-box): <b>r=",
        "הצלבה מול סקרי INES: <b>r=": "Cross-check vs INES surveys: <b>r=",
        # warnings
        "⚠️ עמודת היעד במעבר זה מבוססת על כוונת הצבעה (סקר קדם-בחירות); מתלבטים הוחרגו, וייתכנו פערים מול ההצבעה בפועל.":
            "⚠️ The destination column in this transition is based on vote intent (pre-election survey); undecideds were excluded, and gaps vs the actual vote are possible.",
        "⚠️ שורות דלות-מדגם (פחות מ-30 משיבים): ": "⚠️ Thin-sample rows (under 30 respondents): ",
        "; האומדן שלהן רועש.": "; their estimates are noisy.",
        "שורת \"Did not vote\" מבוססת על דיווח עצמי; סקרים מפחיתים הימנעות (דיווח-יתר על הצבעה), והנזכרים בהצבעה נוטים לזכור את המנצח.":
            "The \"Did not vote\" row is based on self-report; surveys understate abstention (over-reporting of voting), and respondents recalling their vote tend to remember the winner.",
        "⚠️ מרשם הבוחרים של 2006 חסר בנתוני המקור, ונאמד כממוצע 2003/2009. זרימות \"Did not vote\" במעבר זה הן הערכה.":
            "⚠️ The 2006 voter registry is missing from the source data, and estimated as the 2003/2009 average. \"Did not vote\" flows in this transition are approximate.",
        "⚠️ מבחן הפיצול לפי מגזר: אומדן הגוש הערבי במעבר זה שונה מהותית בין פתרון כלל-ארצי לפתרון בתוך המגזר (פער ":
            "⚠️ Sector split test: the Arab-bloc estimate in this transition differs materially between the national solution and the within-sector one (gap of ",
        " נק' L1; במגזר נאמד יותר מעבר להימנעות). קראו את שורת הגוש הערבי בזהירות.":
            " pp L1; the within-sector solution estimates more movement to abstention). Read the Arab-bloc row with caution.",
        "תצוגת המפלגות ניסיונית: מפלגות קטנות בעלות פריסה גאוגרפית דומה קשות להפרדה סטטיסטית (מולטיקולינאריות). העדיפו את תצוגת הגושים.":
            "The party view is experimental: small parties with similar geographic footprints are hard to separate statistically (multicollinearity). Prefer the bloc view.",
        # tooltips + labels
        "רווח-סמך 95%: <span": "95% CI: <span",
        "לפי הסקר: ": "Per the survey: ",
        " ממקור זה (≈": " of this source (≈",
        " ממקור זה)": " of this source)",
        "משיבים בשורה זו: ": "Respondents in this row: ",
        "האומדן היישובי: ": "Locality estimate: ",
        "סקר INES: ": "INES survey: ",
        " (מקור)": " (source)",
        " (יעד)": " (destination)",
        "הוסתרו ": "Hidden: ",
        " זרימות דקות (פחות מ-0.4% מסך הקולות; ": " thin flows (each under 0.4% of total votes; ",
        " קולות יחד).": " votes combined).",
        " קולות (": " votes (",
        " קולות)": " votes)",
        " נק'": " pp",
    },
    # ------------------------------------------------------------------ party_analysis
    "party_analysis": {
        "ניתוח מפלגות: פרופיל חברתי-כלכלי וגאוגרפי, כנסת 13–25":
            "Party Analysis: Socioeconomic & Geographic Profiles, Knesset 13–25",
        "ניתוח מפלגתי · כנסת 13–25 (1992–2022) · הצבעה × מדדים חברתיים-כלכליים":
            "Party analysis · Knesset 13–25 (1992–2022) · Voting × socioeconomic indicators",
        "פרופיל מפלגות": "Party Profiles",
        "בחרו מפלגה כדי לראות את <b>מסלול המנדטים</b> שלה, <b>מעוזי הכוח</b> הגאוגרפיים, ומהו":
            "Pick a party to see its <b>seat trajectory</b>, its geographic <b>strongholds</b>, and the",
        "<b>הפרופיל החברתי-כלכלי</b> של היישובים שבהם היא חזקה: השכלה, פריון, הכנסה, דתיות ומדד חברתי-כלכלי.":
            "<b>socioeconomic profile</b> of the localities where it is strong: education, fertility, income, religiosity and the socioeconomic index.",
        "המתאמים מוצגים גם על <span class=\"hl\">כלל היישובים</span> וגם על <span class=\"hl\">יישובים יהודיים בלבד</span>,":
            "Correlations are shown both for <span class=\"hl\">all localities</span> and for <span class=\"hl\">Jewish localities only</span>,",
        "כי ערבוב הסקטורים מסתיר את המדרג בתוך הסקטור היהודי.":
            "because mixing the sectors hides the gradient within the Jewish sector.",
        ">מפלגה:</label>": ">Party:</label>",
        "מסלול המפלגה: מנדטים ואחוז ארצי": "Party trajectory: seats and national share",
        "עמודות = מנדטים · קו = אחוז מהקולות הארציים. ריחוף מציג את שם הרשימה באותה מערכת בחירות.":
            "Bars = seats · line = share of the national vote. Hover shows the list's name in that election.",
        "מעוזי כוח: אחוז ההצבעה הגבוה ביותר": "Strongholds: highest vote share",
        "היישובים שבהם חלק המפלגה מהקולות הכשרים הוא הגבוה ביותר (יישובים עם 300+ קולות).":
            "Localities where the party's share of valid votes is highest (localities with 300+ votes).",
        "מהיכן מגיעים הקולות: תרומה מוחלטת": "Where the votes come from: absolute contribution",
        "היישובים התורמים הכי הרבה קולות בפועל למפלגה (% מכלל קולות המפלגה).":
            "The localities contributing the most actual votes to the party (% of all the party's votes).",
        "המדרג החברתי-כלכלי: מתאם בין חלק המפלגה למאפייני היישוב":
            "The socioeconomic gradient: correlation between party share and locality attributes",
        "מתאם פירסון (משוקלל בקולות כשרים) בין אחוז ההצבעה למפלגה בכל יישוב לבין המשתנה החברתי-כלכלי.":
            "Pearson correlation (weighted by valid votes) between the party's vote share in each locality and the socioeconomic variable.",
        "חיובי</span> = חזקה יותר ביישובים עם ערך גבוה; ": "Positive</span> = stronger in high-value localities; ",
        "שלילי</span> = ביישובים עם ערך נמוך.": "negative</span> = in low-value localities.",
        "טביעת-אצבע של הבוחרים: פרופיל מתוקנן": "Voter fingerprint: standardized profile",
        "ממוצע (משוקלל בקולות המפלגה) של מאפייני היישובים שבהם היא חזקה, מול ממוצע כלל הבוחרים.":
            "Mean (weighted by the party's votes) of the attributes of the localities where it is strong, vs the all-voter mean.",
        "ה\"מדד המתוקנן\" הוא הפרש ביחידות סטיית-תקן.":
            "The \"standardized index\" is the difference in standard-deviation units.",
        "הרכב אוכלוסייה (משוקלל בקולות)": "Population composition (vote-weighted)",
        "אחוז יהודים / ערבים / \"ללא סיווג דת\" (בעיקר עולי בריה\"מ) ביישובים שבהם המפלגה חזקה.":
            "% Jews / Arabs / \"no religious classification\" (mostly FSU immigrants) in the localities where the party is strong.",
        "התפלגות לפי אשכול חברתי-כלכלי": "Distribution by socioeconomic cluster",
        "חלק מקולות המפלגה לפי אשכול הלמ\"ס של היישוב (1 = נמוך, 10 = גבוה).":
            "Share of the party's votes by the locality's CBS cluster (1 = low, 10 = high).",
        "המדרג לאורך זמן: אותם מתאמים בכל מערכות הבחירות":
            "The gradient over time: the same correlations across every election",
        "כל קו = משתנה חברתי-כלכלי (לחיצה על המקרא מציגה או מסתירה אותו). עוקב אחר בורר כל היישובים / יישובים יהודיים שבלוח שמעליו. המאפיינים קבועים (~2021); מה שמשתנה הוא ההצבעה. לחיצה על נקודה עוברת לאותה מערכת בחירות.":
            "Each line = a socioeconomic variable (click the legend to show or hide it). Follows the all-localities / Jewish-localities selector in the panel above. The attributes are a fixed ~2021 snapshot; what changes is the voting. Clicking a point jumps to that election.",
        "אשכולות לאורך זמן": "Clusters over time",
        "הרכב אוכלוסייה לאורך זמן": "Population composition over time",
        "יהודים / ערבים / אחר בכל מערכת בחירות (משוקלל בקולות המפלגה, אותם צבעים כמו בעוגה; ריחוף מציג גם \"ללא סיווג דת\"). לחיצה על עמודה עוברת לאותה מערכת בחירות.":
            "Jews / Arabs / other in every election (weighted by the party's votes, same colors as the doughnut; hover also shows \"no religious classification\"). Clicking a bar jumps to that election.",
        "text:'% (משוקלל בקולות)'": "text:'% (vote-weighted)'",
        "'ללא סיווג דת: '": "'No religious classification: '",
        "כל עמודה = מערכת בחירות; הפלחים = אשכולות הלמ\"ס 1–10 (אדום = נמוך, כחול = גבוה), באותם צבעים כמו בתרשים ההתפלגות. לחיצה על עמודה עוברת לאותה מערכת בחירות.":
            "Each bar = an election; segments = CBS clusters 1–10 (red = low, blue = high), same colors as the distribution chart. Clicking a bar jumps to that election.",
        # party-system panel
        "🧮 מערכת המפלגות 1992–2022: פיצול, תנודתיות ולאומיזציה":
            "🧮 The Party System 1992–2022: Fragmentation, Volatility and Nationalization",
        "שלושה מדדים קלאסיים על 13 מערכות הבחירות. <b>המספר האפקטיבי של מפלגות</b> (Laakso–Taagepera) מודד פיצול; <b>תנודתיות פדרסן</b> מודדת איזה חלק מהקולות החליף רשימה בין בחירות עוקבות; <b>מדד הלאומיזציה</b> (Jones–Mainwaring) מודד עד כמה חלקה של מפלגה דומה בכל רחבי הארץ (1 = אחיד לגמרי). הסיפור המשולב: <b>רמת הרשימות סוערת (פיצול שיא ותנודתיות גבוהה); רמת הגושים יציבה בהרבה; והמפלגות הולכות ונעשות גאוגרפיות</b>: הלאומיזציה יורדת בהתמדה, בהלימה לממצא המיון הגאוגרפי של <a href=\"findings_en.html\">עמוד הממצאים</a>.":
            "Three classic measures across the 13 elections. The <b>effective number of parties</b> (Laakso–Taagepera) measures fragmentation; <b>Pedersen volatility</b> measures what share of the vote switched lists between consecutive elections; the <b>nationalization score</b> (Jones–Mainwaring) measures how uniform a party's share is across the country (1 = perfectly uniform). The combined story: <b>the list level is stormy (record fragmentation and high volatility); the bloc level is far more stable; and parties are becoming increasingly geographic</b>: nationalization declines steadily, consistent with the geographic-sorting finding on the <a href=\"findings_en.html\">findings page</a>.",
        "מספר אפקטיבי של מפלגות": "Effective number of parties",
        "קו מלא = לפי קולות (הרשימות שבמעקב, מנורמל) · מקווקו = לפי מנדטים.":
            "Solid = by votes (tracked lists, renormalized) · dashed = by seats.",
        "תנודתיות (פדרסן) ולאומיזציה": "Volatility (Pedersen) and nationalization",
        "תנודתיות ברמת רשימות מול ברמת גושים · ירוק (ציר ימני) = לאומיזציה.":
            "List-level vs bloc-level volatility · green (separate axis) = nationalization.",
        "תמונת מצב לפי בחירות: מי ארצית ומי מקומית":
            "Snapshot by election: which lists are national, which are local",
        "בחרו מערכת בחירות: כל רשימה עם מדד הלאומיזציה שלה (1 = חלק אחיד בכל הארץ), צבועה לפי גוש. ריחוף מציג אחוז ומנדטים.":
            "Pick an election: every list with its nationalization score (1 = uniform share nationwide), colored by bloc. Hover shows share and seats.",
        # JS
        " · שיא ": " · peak ",
        " מנדטים`;": " seats`;",
        "הערות שיטה:</span>": "Method notes:</span>",
        "מפלגות אפקטיביות 2022 (שיא: ": "Effective parties 2022 (peak: ",
        " ב-${peakEnp.year})": " in ${peakEnp.year})",
        "תנודתיות רשימות ממוצעת (שיא ": "Mean list volatility (peak ",
        "% ב-${peakVol.year})": "% in ${peakVol.year})",
        "'תנודתיות גושים ממוצעת: כ-'": "'Mean bloc volatility: about '",
        "'% מהרשימות'": "'% of the list level'",
        "'לאומיזציה 1992 ← 2022 (ירידה עקבית)'": "'Nationalization 1992 → 2022 (steady decline)'",
        "label:'לפי קולות'": "label:'By votes'",
        "label:'לפי מנדטים'": "label:'By seats'",
        " רשימות במעקב (": " tracked lists (",
        "% מהקולות)": "% of votes)",
        "הגדולה: ": "Largest: ",
        "'מפלגות אפקטיביות (קולות)'": "'Effective parties (votes)'",
        "'מפלגות אפקטיביות'": "'Effective parties'",
        "label:'תנודתיות · רשימות'": "label:'Volatility · lists'",
        "label:'תנודתיות · גושים'": "label:'Volatility · blocs'",
        "label:'לאומיזציה (PSNS)'": "label:'Nationalization (PSNS)'",
        "'לאומיזציה: '": "'Nationalization: '",
        "'הכי ארציות: '": "'Most national: '",
        "'הכי מקומיות: '": "'Most local: '",
        "text:'% מהקולות שהחליפו'": "text:'% of votes that switched'",
        "text:'לאומיזציה (0–1)'": "text:'Nationalization (0–1)'",
        "שיטה:</span>": "Method:</span>",
        "המספר האפקטיבי לפי קולות מחושב על הרשימות שבמעקב, כולל רשימות בולטות שלא עברו את אחוז החסימה (מנורמל; שאר הקולות, 0.3%–5.9%, חסרים, הטיה קלה כלפי מטה: הספרות, המחשבת על כל הרשימות שרצו, מגיעה ל-10.3 ב-1999 לעומת 9.01 כאן). ":
            "The effective number by votes is computed over the tracked lists, including prominent lists that missed the threshold (renormalized; the remaining votes, 0.3%–5.9%, are missing, a slight downward bias: the literature, which counts every list that ran, reaches 10.3 for 1999 vs 9.01 here). ",
        "תנודתיות פדרסן ברמת רשימות עוקבת אחרי קווי-מפלגה קנוניים; רשימות משותפות ופיצולים נספרים כיציאה+כניסה (המוסכמה המקובלת, שמנפחת שנות מיזוג כמו 2013). ":
            "List-level Pedersen volatility follows canonical party lines; joint lists and splits count as exit+entry (the standard convention, which inflates merger years like 2013). ",
        "תנודתיות הגושים סופרת גם שינוי סיווג של מפלגה: ישראל ביתנו נספרת בגוש הימין עד 2015 ובמרכז-שמאל מאפריל 2019 (מוסכמת האתר); המעבר הזה תורם כ-4 נק׳ לשיא של אפריל 2019. ":
            "Bloc volatility also counts party reclassification: Yisrael Beiteinu is counted in the right bloc through 2015 and in the center-left from April 2019 (the site convention); that move contributes ~4 points of the April-2019 peak. ",
        "הלאומיזציה מחושבת ברמת יישובים (לא קלפיות); הרמה המוחלטת גבוהה מבמחקרים מבוססי-קלפי; ההשוואה המשמעותית היא לאורך זמן.":
            "Nationalization is computed at the locality level (not ballot boxes); absolute levels read higher than in ballot-box studies; the meaningful comparison is over time.",
        "עוגן בספרות:</span> המספר האפקטיבי לפי מנדטים כאן משחזר אחד-לאחד את סדרת The Elections in Israel: 8.69 ב-1999 ו-6.17 ב-2003; כרך 2003 מציג את הצניחה כתוצר ביטול הבחירה הישירה, שהחזיר קולות למפלגות הגדולות מבלי לשחזר את הריכוזיות של טרום-1996. ספר מערכת המפלגות מאבחן את התקופה שאחרי 2003 כאי-מערכת (non-system) ללא מבנה יציב ברמת הרשימות, לצד יציבות גושית גבוהה; בדיוק הפער הנמדד כאן בין תנודתיות הרשימות (ממוצע ~27%) לתנודתיות הגושים (~12%). את שיא 2006 (41.4% אצלנו) הספרות מתעדת גם ברמת הבוחר הבודד: 63% מהמצביעים החליפו מפלגה, בעוד נאמנות הגושים נשמרה. [The Elections in Israel 2003, עמ׳ 44–59 · The Parties in Israel 1992–2021, עמ׳ 720–723 · The Elections in Israel 2006, פרק קדימה]":
            "Literature anchor:</span> The effective number by seats here reproduces The Elections in Israel series one-for-one: 8.69 in 1999 and 6.17 in 2003; the 2003 volume presents that drop as a product of repealing direct PM election, which returned votes to the large parties without restoring pre-1996 concentration. The party-system book diagnoses the post-2003 period as a non-system with no stable structure at the list level alongside high bloc stability; precisely the gap measured here between list volatility (mean ~27%) and bloc volatility (~12%). And the 2006 peak (41.4% here) is documented in the literature at the individual level too: 63% of voters switched parties while bloc loyalty held. [The Elections in Israel 2003, pp. 44–59 · The Parties in Israel 1992–2021, pp. 720–723 · The Elections in Israel 2006, Kadima chapter]",
        "'2019א'": "'Apr 2019'",
        "'2019ב'": "'Sep 2019'",
        "תנודתיות מאז ": "Volatility since ",
        " (גושים: ": " (blocs: ",
        "'בחירות ראשונות בסדרה'": "'First election in the series'",
        "'לאומיזציה ממוצעת (PSNS)'": "'Mean nationalization (PSNS)'",
        "`לאומיזציה ": "`Nationalization ",
        "% מהקולות · ": "% of votes · ",
        " מנדטים · ": " seats · ",
        "text:'מדד לאומיזציה (0 = מרוכזת גאוגרפית, 1 = אחידה בכל הארץ)'":
            "text:'Nationalization score (0 = geographically concentrated, 1 = uniform nationwide)'",
        "⚠ אות הרשימה <b>": "⚠ Ballot letter <b>",
        "</b> שימשה כמה רשימות שונות לאורך השנים; המסלול למטה מחבר אותן: ":
            "</b> served several different lists over the years; the trajectory below chains them: ",
        "'בחירות:'": "'Election:'",
        "'כל הלוחות למטה מוצגים לבחירות שנבחרו (אפשר גם ללחוץ על עמודה במסלול). המאפיינים החברתיים-כלכליים (מדד, השכלה, הכנסה, דת) הם צילום ~2021 קבוע, גם לבחירות עבר.'":
            "'All panels below are shown for the selected election (you can also click a bar in the trajectory). The socioeconomic attributes (index, education, income, religion) are a fixed ~2021 snapshot, including for past elections.'",
        "lbl:`מנדטים (כ׳": "lbl:`Seats (K",
        "'אחוז ארצי'": "'National share'",
        "'שיא מנדטים היסטורי'": "'Historical peak seats'",
        "lbl:`קולות (כ׳": "lbl:`Votes (K",
        "'יהודים (משוקלל)'": "'Jews (weighted)'",
        "'ללא סיווג דת (עולי בריה״מ)'": "'No religious classification (FSU immigrants)'",
        "כ׳": "K",
        "label:'מנדטים'": "label:'Seats'",
        "text:'מנדטים'": "text:'Seats'",
        "'% ארצי'": "'% national'",
        "יישובים יהודיים בלבד (pct_jews≥70), n≈": "Jewish localities only (pct_jews≥70), n≈",
        ". מסיר את בלבול הסקטור הערבי.": ". Removes the Arab-sector confound.",
        "כל היישובים שהותאמו למדד החברתי-כלכלי, n≈": "All localities matched to the socioeconomic index, n≈",
        ". מערבב יהודים וערבים.": ". Mixes Jewish and Arab localities.",
        "text:'מתאם r'": "text:'correlation r'",
        "<th>מאפיין</th>": "<th>Attribute</th>",
        "<th>המפלגה</th>": "<th>Party</th>",
        "<th>כלל הבוחרים</th>": "<th>All voters</th>",
        "<th>מתוקנן (ס״ת)</th>": "<th>Standardized (SD)</th>",
        # keyed post-literal-pass: 'יהודים'/'ערבים' are names_en keys and translate first
        "'אחר/מעורב'": "'Other/mixed'",
        "'אשכול '": "'Cluster '",
        "'% מקולות המפלגה'": "'% of party votes'",
        "text:'אשכול חברתי-כלכלי (1=נמוך, 10=גבוה)'": "text:'Socioeconomic cluster (1=low, 10=high)'",
        "<th>יישוב</th>": "<th>Locality</th>",
        "<th>קולות</th>": "<th>Votes</th>",
        "'חלק ביישוב'": "'Share in locality'",
        "'% מהמפלגה'": "'% of party'",
        "'כל היישובים'": "'All localities'",
        "'יישובים יהודיים'": "'Jewish localities'",
    },
    # ------------------------------------------------------------------ demographics
    "demographics": {
        "דמוגרפיה והצבעה — 1972–2022": "Demographics & Voting — 1972–2022",
        "מפקדי אוכלוסין 1972–2022 · פרופילי רשויות שנתיים 1999–2024 · מדד חברתי-כלכלי · סקרי INES · רמת יישוב ורמת הפרט":
            "Censuses 1972–2022 · annual local-authority profiles 1999–2024 · socioeconomic index · INES surveys · locality and individual level",
        # section 1
        "🎓 שיפוע ההשכלה מחריף": "🎓 The Education Gradient Is Steepening",
        # ---------- 3c. within-city SA gradient ----------
        "🧭 גם בתוך הערים: שיפוע ההשכלה ברמת השכונה": "🧭 Inside Cities Too: the Neighborhood-Level Education Gradient",
        "האם המיון קיים רק בין יישובים — או גם בין שכונות באותה עיר? כאן אותה רגרסיה נאמדת ברמת האזור הסטטיסטי, בניכוי הממוצע העירוני: כמה נקודות-אחוז הצבעת ימין-חרדים מפרידות בין שכונות של אותה עיר על כל נקודת-אחוז אקדמאים. השיפוע התוך-עירוני החריף מ-<span class=\"n\">0.72−</span> ב-2009 ל-<span class=\"n\">1.06−</span> ב-2022, והמתאם התחזק מ-<span class=\"n\">0.58−</span> ל-<span class=\"n\">0.75−</span>. גם על מפת השכלה <b>קבועה של 2008</b> (בהטלה על גאומטריית 2022) השיפוע מחריף — ל-<span class=\"n\">0.86−</span> — כלומר יש מיון-מחדש התנהגותי גם <b>בתוך</b> הערים, לא רק עדכון של מפת ההשכלה. ההשוואה לשיפוע הבין-יישובי (הקו האפור; <span class=\"n\">1.64−</span> ב-2022) מראה שהמיון בין יישובים חד מהמיון בין שכונות — אבל שניהם מחריפים. שני צירים נוספים, שלהם יש נתוני מפקד 1995 והם מושכים את הסדרה אחורה ל-2003: <b>מוצא אסיה-אפריקה</b> — שיפוע חיובי מתון ויציב יחסית, כלומר ההחרפה התוך-עירונית היא סיפור של השכלה, לא של מוצא — ו<b>עולים</b>, שם שכונות עולי שנות ה-90 הצביעו ימינה מסביבתן ב-2003–2006, ואילו שכונות עולי 2002+ במפקדים המאוחרים כמעט אינן חריגות.":
            "Does the sorting exist only between localities — or between neighborhoods of the same city as well? Here the same regression is estimated at the statistical-area level, net of each city&#39;s mean: how many Right-Haredi vote points separate neighborhoods of the same city per percentage point of academics. The within-city slope steepened from <span class=\"n\">−0.72</span> in 2009 to <span class=\"n\">−1.06</span> in 2022, and the correlation strengthened from <span class=\"n\">−0.58</span> to <span class=\"n\">−0.75</span>. Even on an education map <b>frozen at 2008</b> (projected onto the 2022 geometry) the slope steepens — to <span class=\"n\">−0.86</span> — i.e., there is behavioral re-sorting <b>inside</b> cities too, not merely an update of the education map. The comparison with the between-locality slope (the gray line; <span class=\"n\">−1.64</span> in 2022) shows sorting between localities is sharper than between neighborhoods — but both are steepening. Two further axes have 1995-census data and pull the series back to 2003: <b>Asia-Africa origin</b> — a modest, fairly stable positive slope, i.e., the within-city steepening is an education story, not an origin one — and <b>olim</b>, where the 1990s-wave neighborhoods voted to the right of their cities in 2003–2006, while post-2002 olim neighborhoods in the later censuses are barely distinctive.",
        "הדמוגרפיה לפי מפקד העידן, כמו במפת השכונות: בחירות 2003/2006 מול מפקד 1995 (גאומטריית 1995), 2009–2015 מול מפקד 2008, 2019–2022 מול מפקד 2022. וריאנט \"השכלה קבועה 2008\" מטיל את אחוז האקדמאים של 2008 על אזורי 2022 באינטרפולציה משוקללת-אוכלוסייה (כיסוי ≥70%). היקום: אזורים סטטיסטיים יהודיים עם מפקד ברמת האזור, בערים עם ≥5 אזורים כשירים; משקל = קולות כשרים; רווח-סמך: bootstrap אשכולות-ערים (B=1,000). ציר ההשכלה מתחיל ב-2009 — לוחות 1995 שבידינו כוללים דת, מוצא וגיל אך לא השכלה (טבלת ההשכלה של מפקד 1995 תתווסף כשתיקלט). מוצא אסיה-אפריקה נמדד לדור המהגרים וילדיהם בלבד (יליד חו\"ל או אב יליד חו\"ל) — חלק הולך וקטן מהאוכלוסייה, ולכן ההשוואה לאורך זמן שמרנית. ציר העולים מחליף עוקבה: עולי 1990+ במפקד 1995, עולי 2002+ במפקדי 2008/2022 — הקו אינו מחובר בין העוקבות. וריאנט \"ללא שכונות חרדיות\" משמיט אזורים שבהם הגוש החרדי ≥40% מהקולות (זיהוי פוליטי, זמין בכל העידנים) — ההחרפה שרירה גם בלעדיהם, כלומר המיון התוך-עירוני אינו רק הגאוגרפיה החרדית.":
            "Demographics are the era census, as on the neighborhood map: the 2003/2006 elections against the 1995 census (1995 geometry), 2009–2015 against the 2008 census, 2019–2022 against the 2022 census. The <i>education fixed at 2008</i> variant projects the 2008 %academics onto the 2022 areas by population-weighted areal interpolation (coverage ≥70%). Universe: Jewish statistical areas with area-level census data, in cities with ≥5 eligible areas; weight = valid votes; CI: city-cluster bootstrap (B=1,000). The education axis starts in 2009 — the 1995 volumes on hand cover religion, origin and age but not education (the 1995 census education table will join once brought in). Asia-Africa origin is measured for the immigrant generation and their children only (born abroad, or father born abroad) — a shrinking population share, so the over-time comparison is conservative. The olim axis switches cohorts: post-1990 olim in the 1995 census, post-2002 olim in the 2008/2022 censuses — the line is not bridged between cohorts. The <i>excluding haredi neighborhoods</i> variant omits areas where the haredi bloc takes ≥40% of the vote (a political proxy, available in every era) — the steepening holds without them, i.e., the within-city sorting is not merely haredi geography.",
        "> אקדמאים</label>": "> Academics</label>",
        "> מוצא אסיה-אפריקה</label>": "> Asia-Africa origin</label>",
        "> עולים</label>": "> Olim</label>",
        "'מוצא אסיה-אפריקה — בתוך הערים'": "'Asia-Africa origin — within cities'",
        "'עולי 1990+ (מפקד 1995)'": "'Olim 1990+ (1995 census)'",
        "'עולי 2002+ (מפקדי 2008/2022)'": "'Olim 2002+ (2008/2022 censuses)'",
        "'נק\"א ימין-חרדים לנק\"א מוצא אסיה-אפריקה (תוך-עירוני)'": "'RH pp per pp of Asia-Africa origin (within-city)'",
        "'נק\"א ימין-חרדים לנק\"א עולים (תוך-עירוני)'": "'RH pp per pp of olim (within-city)'",
        "יציב-מתון לאורך התקופה — ההחרפה התוך-עירונית היא בהשכלה": "Modest and stable across the period — the within-city steepening is in education",
        "עולי 1990+ ב-2003:": "Olim 1990+ in 2003:",
        "</b> · ב-2006: <b": "</b> · in 2006: <b",
        "עולי 2002+ ב-2022:": "Olim 2002+ in 2022:",
        "החלפת עוקבה בין המפקדים — הקו אינו מחובר": "Cohort switch between censuses — the line is not bridged",
        "'ללא שכונות חרדיות (גוש חרדי ≥40%)'": "'Excluding haredi neighborhoods (haredi bloc ≥40%)'",
        "ללא שכונות חרדיות ב-2022:": "Excluding haredi neighborhoods, 2022:",
        "> מוצא</label>": "> Origin</label>",
        "'אסיה-אפריקה (מזרחים)'": "'Asia-Africa (Mizrahim)'",
        "'אירופה-אמריקה'": "'Europe-America'",
        "'ילידי ישראל, אב יליד ישראל'": "'Israel-born, father Israel-born'",
        "פער מזרחים-אשכנזים 1992:": "Mizrahi-Ashkenazi gap 1992:",
        "לפי יבשת לידה של הנשאל/האב (1996: הגדרה עצמית) · נקודה חלולה: n&lt;100":
            "By continent of birth of the respondent/father (1996: self-definition) · hollow point: n&lt;100",
        "'בתוך הערים (מפקד העידן)'": "'Within cities (era census)'",
        "'בתוך הערים — השכלה קבועה 2008'": "'Within cities — education fixed at 2008'",
        "'בין יישובים (הסעיף הראשון)'": "'Between localities (the first section)'",
        " שכונות ב-${": " neighborhoods in ${",
        " ערים (r=${": " cities (r=${",
        "'נק\"א ימין-חרדים לנק\"א אקדמאים (תוך-עירוני)'": "'RH pp per pp of academics (within-city)'",
        "'שיפוע תוך-עירוני — 12 הערים הגדולות'": "'Within-city slope — the 12 largest cities'",
        ": שיפוע ${": ": slope ${",
        " שכונות)`": " neighborhoods)`",
        "השכלה קבועה 2008 ב-2022:": "Education fixed at 2008, in 2022:",
        "</span> שכונות · <span": "</span> neighborhoods · <span",
        "</span> ערים`,": "</span> cities`,",
        "בכל מערכת בחירות נאמד הקשר בין אחוז האקדמאים ביישוב (מפקדי הלמ\"ס 1972–2022, באינטרפולציה לשנת הבחירות) ובין הצבעת ימין-חרדים, במשקל גודל ציבור הבוחרים. השיפוע (כמה נקודות-אחוז הצבעה \"עולה\" כל נקודת-אחוז אקדמאים) <b>כמעט הוכפל</b> בין 1992 ל-2022, והמתאם התחזק מ-<span class=\"n\">0.35−</span> ל-<span class=\"n\">0.82−</span>. ההחרפה שרירה גם כשמקבעים את מפת ההשכלה לזו של 2008; כלומר, ההצבעה נערכה מחדש לאורך מפה חברתית קיימת, לא רק בעקבות שינוי דמוגרפי.":
            "For each election, the link between a locality's % academics (CBS censuses 1972–2022, interpolated to the election year) and its Right-Haredi vote is estimated, weighted by electorate size. The slope (how many vote percentage points each percentage point of academics \"buys\") <b>nearly doubled</b> between 1992 and 2022, and the correlation strengthened from <span class=\"n\">−0.35</span> to <span class=\"n\">−0.82</span>. The steepening holds even when the education map is frozen at its 2008 values; i.e., the vote re-sorted along an existing social map, not merely via demographic change.",
        "> יישובים יהודיים</label>": "> Jewish localities</label>",
        "> כל היישובים</label>": "> All localities</label>",
        "> השכלה עדכנית (אינטרפולציה)</label>": "> Current education (interpolated)</label>",
        "> השכלה קבועה (2008)</label>": "> Fixed education (2008)</label>",
        "> שיפוע</label>": "> Slope</label>",
        "> מתאם (r)</label>": "> Correlation (r)</label>",
        "רווח-סמך 95% (רצועה): bootstrap על דגימת יישובים מחדש (B=1,000). שיפוע ביחידות נק\"א הצבעה לנק\"א אקדמאים (בני 15+).":
            "95% CI (band): bootstrap over locality resamples (B=1,000). Slope in units of vote pp per pp of academics (ages 15+).",
        # section 1b
        "💰 ההכנסה חילקה כבר ב-1999, ההשכלה הדביקה אותה":
            "💰 Income Already Divided the Map in 1999, Education Caught Up",
        "הפאנל השנתי של הרשויות המקומיות (למ\"ס, 1999–2024) מודד שכר ממוצע ואחוז זכאים לבגרות בכל מערכת בחירות, בלי אינטרפולציית מפקדים. על אותם ~115 יישובים יהודיים בדיוק: <b>פער ההכנסה חילק את המפה כבר ב-1999</b> (מתאם <span class=\"n\">0.80−</span>) והעמיק רק במתינות; <b>פער ההשכלה התחיל חלש ממנו</b> (<span class=\"n\">0.68−</span>) <b>והתחזק כמעט פי שניים מהר יותר</b>, עד שב-2022 השתווה להכנסה (<span class=\"n\">0.89−</span>). ההיערכות-מחדש של שנות ה-2000 היא בעיקר השכלה שהתיישרה על מפת הכנסה שכבר הייתה קיימת.":
            "The annual local-authority panel (CBS, 1999–2024) measures average wage and bagrut (matriculation) eligibility at every election, with no census interpolation. On the exact same ~115 Jewish localities: <b>the income divide had already split the map by 1999</b> (correlation <span class=\"n\">−0.80</span>) and deepened only modestly; <b>the education divide started weaker</b> (<span class=\"n\">−0.68</span>) <b>and strengthened nearly twice as fast</b>, until by 2022 it matched income (<span class=\"n\">−0.89</span>). The re-alignment of the 2000s is mostly education lining up along an income map that already existed.",
        "מתאם משוקלל-בוחרים של הצבעת ימין-חרדים על לוג השכר הממוצע, אחוז אקדמאים (מפקדים, באינטרפולציה) ואחוז זכאים לבגרות, על אותן רשויות בכל בחירות (בגרות: החל מ-2003). רצועות: רווח-סמך 95% (bootstrap רשויות, B=1,000). הקו האפור: שיפוע ההשכלה על כלל ~900 היישובים (הסעיף הקודם); הממצא שריר גם ביקום הרשויות המצומצם.":
            "Voter-weighted correlation of the Right-Haredi vote with log average wage, % academics (censuses, interpolated) and % bagrut-eligible, on the same authorities in every election (bagrut: from 2003). Bands: 95% CI (authority bootstrap, B=1,000). Gray line: the education gradient on all ~900 localities (previous section); the finding holds in the restricted authority universe too.",
        "הקשר מחקרי: סדרת The Elections in Israel מתעדת לאורך התקופה פער ייצוג חברתי-כלכלי: ב-2009, למשל, 58% מחברי הכנסת השתייכו למפלגות בעלות גישה כלכלית ליברלית בעוד 68% מהנשאלים העדיפו גישה חברתית, ומסבירה אותו בכך שמערכת המפלגות נעולה על שסע הסכסוך והזהות. גם כשסדר-היום הכלכלי ניצח בקמפיין (ב-2013, 44% אמרו שהבחירות עסקו בעיקר בסוגיות המחאה), התוצאה תורגמה למינוף מרכזני בתוך ממשלת נתניהו, לא לפוליטיקה מעמדית. זה מתלכד עם הממצא כאן: ההכנסה מיינה את המפה כבר ב-1999, אך התרגום הפוליטי שלה עובר דרך ציר הזהות, לא דרך מפלגות מעמדיות. [The Elections in Israel 2009, עמ׳ 23–24 · 2013, עמ׳ 16–17]":
            "Research context: The Elections in Israel series documents a socioeconomic representation gap throughout the period: in 2009, for instance, 58% of MKs belonged to parties with an economically liberal approach while 68% of respondents preferred a social-welfare approach, and explains it by a party system locked onto the conflict-and-identity cleavage. Even when the economic agenda won the campaign (in 2013, 44% said the election was mainly about the protest issues), the outcome translated into centrist leverage inside a Netanyahu government, not class politics. This converges with the finding here: income sorted the map as early as 1999, but its political translation runs through the identity axis, not through class parties. [The Elections in Israel 2009, pp. 23–24 · 2013, pp. 16–17]",
        # section 2
        "🔀 מי נודד: מעברי קולות לפי שלישי השכלה": "🔀 Who Moves: Vote Transfers by Education Tercile",
        "מטריצות המעבר של <a href=\"transfers_en.html\" style=\"color:var(--c-right)\">עמוד נדידת הקולות</a>, נאמדות כאן בנפרד לשלושה שלישים של היישובים היהודיים לפי אחוז אקדמאים (שלישים שווי-בוחרים; החיתוך מוצג מטה). בחרו מעבר וגוש-מוצא כדי לראות לאן הלכו קולותיו בכל שליש.":
            "The transfer matrices of the <a href=\"transfers_en.html\" style=\"color:var(--c-right)\">vote-transfers page</a>, re-estimated separately for three terciles of Jewish localities by % academics (voter-balanced terciles; cutpoints shown below). Pick a transition and a source bloc to see where its votes went in each tercile.",
        ">גוש מוצא:</span>": ">Source bloc:</span>",
        "'מעט מדי קולות מוצא באחד השלישים'": "'Too few source votes in one of the terciles'",
        "'שליש תחתון'": "'Bottom third'",
        "'שליש עליון'": "'Top third'",
        "% אקדמאים)`": "% academics)`",
        "</b> אקדמאים`": "</b> academics`",
        "חיתוך שלישים: ": "Tercile cutpoints: ",
        "</b> קולות מוצא · R²=<span": "</b> source votes · R²=<span",
        "כיסוי מפקד: <b": "Census coverage: <b",
        "</b> מהבוחרים`": "</b> of voters`",
        "⚠️ בגוש \"": "⚠️ The \"",
        "\" יש מעט קולות מוצא ב": "\" bloc has few source votes in ",
        " — האומדן שם רועש (פתרונות-פינה של 0%/100% אפשריים).":
            " — the estimate there is noisy (0%/100% corner solutions possible).",
        "⚠️ מעבר הנוגע ל-2006: מרשם הבוחרים נאמד (ממוצע 2003/2009) — נתוני ההימנעות הם הערכה.":
            "⚠️ Transition involving 2006: the voter registry is estimated (2003/2009 average) — abstention figures are approximate.",
        "'שלישי ההשכלה מוגדרים על יישובים יהודיים בלבד (המגזר הערבי מוצג בנפרד בעמוד נדידת הקולות). חברות בשליש משתנה בין מעברים (השכלה עדכנית).'":
            "'Education terciles are defined on Jewish localities only (the Arab sector is shown separately on the vote-transfers page). Tercile membership changes between transitions (current education).'",
        "% (כ-": "% (≈",
        " קולות)`": " votes)`",
        "text:'% מקולות גוש המוצא'": "text:'% of the source bloc\\'s votes'",
        # section 3
        "🏙️ בתוך הערים הפערים מצטמצמים; בין היישובים המיון גובר":
            "🏙️ Within Cities Gaps Are Narrowing; Between Localities Sorting Is Rising",
        "פיזור ערכי המדד החברתי-כלכלי של האזורים הסטטיסטיים <b>בתוך</b> כל עיר (ביחידות יחסיות לפיזור הארצי של אותו שנתון, פאנל מאוזן של אותן ~80 ערים) <b>ירד</b> בהתמדה מ-2008 ל-2021, בעוד שהמיון הפוליטי <b>בין</b> יישובים (סטיית-התקן המשוקללת של הצבעת ימין-חרדים) <b>עלה</b> באותה תקופה. ברמת העיר הבודדת הקשר חלש (r≈<span class=\"n\">0.2−</span>): עיר שהתגוונה חברתית לא בהכרח שינתה את ייחודה הפוליטי.":
            "The dispersion of statistical-area socioeconomic index values <b>within</b> each city (in units relative to that vintage's national dispersion, a balanced panel of the same ~80 cities) <b>fell</b> steadily from 2008 to 2021, while political sorting <b>between</b> localities (the weighted SD of the Right-Haredi vote) <b>rose</b> over the same period. At the single-city level the link is weak (r≈<span class=\"n\">−0.2</span>): a city that diversified socially did not necessarily change its political distinctiveness.",
        "המדד החברתי-כלכלי מתוקנן מחדש בכל שנתון, ולכן מוצגות יחידות יחסיות (פיזור תוך-עירוני ÷ פיזור ארצי), לא ערכים גולמיים. חישוב הפיזור שוחזר ואומת מול לוחות הפיזור הרשמיים של הלמ\"ס ל-2008 ול-2019 (התאמה מלאה, r=1.000).":
            "The socioeconomic index is re-standardized each vintage, hence relative units (within-city dispersion ÷ national dispersion), not raw values. The dispersion computation was reproduced and validated against the official CBS dispersion tables for 2008 and 2019 (exact match, r=1.000).",
        "label:'פיזור חברתי-כלכלי בתוך הערים (מדד=100 ב-2008)'":
            "label:'Socioeconomic dispersion within cities (index=100 in 2008)'",
        "label:'מיון פוליטי בין יישובים (סט\"ן ימין-חרדים, =100 ב-2009)'":
            "label:'Political sorting between localities (RH weighted SD, =100 in 2009)'",
        "`פיזור תוך-עירוני יחסי ": "`Relative within-city dispersion ",
        " (מדד ": " (index ",
        "`סט\"ן ימין-חרדים כנסת ": "`RH weighted SD, Knesset ",
        "label:'ערים'": "label:'Cities'",
        "`Δ פיזור תוך-עירוני: ": "`Δ within-city dispersion: ",
        "`Δ ייחוד פוליטי: ": "`Δ political distinctiveness: ",
        "text:'Δ פיזור חברתי-כלכלי תוך-עירוני, 2008→2021'":
            "text:'Δ within-city socioeconomic dispersion, 2008→2021'",
        "text:'Δ |מרחק מהממוצע הארצי| בהצבעת ימין-חרדים, 2009→2022'":
            "text:'Δ |distance from national mean| in RH vote, 2009→2022'",
        "text:'מדד (נקודת מוצא=100)'": "text:'Index (start=100)'",
        "פיזור תוך-עירוני 2008→2021: <b": "Within-city dispersion 2008→2021: <b",
        "פאנל מאוזן: <b>": "Balanced panel: <b>",
        "</b> ערים`": "</b> cities`",
        "קשר עירוני Δ↔Δ: r=<b": "City-level Δ↔Δ link: r=<b",
        "`ג'יני-שכר תוך-עירוני ארצי ": "`National within-city wage Gini ",
        " (יציב) · ΔΔ מול הפיזור: r=<b": " (stable) · ΔΔ vs dispersion: r=<b",
        # section 3b
        "🚚 הגירה פנימית אינה מסבירה את המיון": "🚚 Internal Migration Does Not Explain the Sorting",
        "אם המיון הגאוגרפי נוצר מהגירה סלקטיבית — אנשים שעוברים ליישובים \"שמתאימים להם\" — נצפה שיישובים עם מאזן הגירה פנימית חיובי יזוזו פוליטית. הנתונים לא מראים זאת: המתאם בין קצב ההגירה הפנימית נטו ובין השינוי בהצבעת ימין-חרדים 1999→2022 הוא כמעט אפס, וכך גם מבחני ההגברה (האם הגירה מחזקת את הנטייה הקיימת?) והייחודיות (האם קולטות-הגירה נעשות חריגות יותר?). זה מחזק את ממצא \"ההשכלה הקבועה\" למעלה: המיון נובע בעיקר משינוי הצבעה <b>בתוך</b> יישובים, לא ממעבר <b>בין</b> יישובים. הקצוות בכל זאת מספרים סיפור — שלושת המקרים מטה.":
            "If geographic sorting were produced by selective migration — people moving to localities that \"fit them\" — we would expect localities with a positive internal-migration balance to shift politically. The data show otherwise: the correlation between the net internal-migration rate and the 1999→2022 change in the Right-Haredi vote is near zero, as are the amplification test (does migration reinforce the existing lean?) and the distinctiveness test (do migration magnets become more atypical?). This reinforces the \"fixed education\" result above: sorting comes mostly from vote change <b>within</b> localities, not movement <b>between</b> them. The extremes still tell a story — the three cases below.",
        "מאזן נטו מסתיר את הרכב הזרמים ברוטו — עיר יכולה לקלוט ולפלוט אוכלוסיות שונות בו-זמנית (כפי שממחישים המקרים). פיצול ההגירה הפנימית לא פורסם 2002–2013; הקצב הממוצע מחושב על השנים הזמינות (1999–2001, 2014–2024). המבחנים הסטטיסטיים על יישובים יהודיים בלבד.":
            "A net balance hides gross-flow composition — a city can absorb and shed different populations simultaneously (as the cases illustrate). The internal-migration split was unpublished 2002–2013; the mean rate is computed over the available years (1999–2001, 2014–2024). Statistical tests on Jewish localities only.",
        "'עיר חרדית שקלטה חרדים — קליטה עצומה כמעט בלי שינוי פוליטי: הגירה משמרת-הרכב.'":
            "'A Haredi city absorbing Haredim — huge intake with almost no political change: composition-preserving migration.'",
        "'המקרה שכן מתאים למנגנון: קליטה חרדית גדולה ותזוזה ימינה חדה.'":
            "'The one case that does fit the mechanism: large Haredi intake and a sharp rightward shift.'",
        "'מקרה נגדי: קליטה מאסיבית — ותזוזה דווקא שמאלה.'":
            "'A counterexample: massive intake — and a shift leftward.'",
        "label:'רשויות'": "label:'Authorities'",
        "`הגירה פנימית נטו: ": "`Net internal migration: ",
        " לאלף/שנה`": " per 1,000/yr`",
        "`Δ ימין-חרדים 1999→2022: ": "`Δ Right-Haredim 1999→2022: ",
        "text:'מאזן הגירה פנימית נטו לאלף תושבים בשנה (ממוצע, שנים זמינות)'":
            "text:'Net internal-migration balance per 1,000 residents per year (mean, available years)'",
        "text:'Δ הצבעת ימין-חרדים 1999→2022 (נק\"א)'": "text:'Δ Right-Haredi vote 1999→2022 (pp)'",
        "מתאם קצב-הגירה ↔ שינוי הצבעה: r=<b": "Migration-rate ↔ vote-change correlation: r=<b",
        "מבחן הגברה: r=<b": "Amplification test: r=<b",
        "מבחן ייחודיות: r=<b": "Distinctiveness test: r=<b",
        "חלון צפוף 2014–2024 (<span": "Dense window 2014–2024 (<span",
        "</b> לאלף/שנה · Δ ימין-חרדים <b": "</b> per 1,000/yr · Δ Right-Haredim <b",
        " נק\"א`": " pp`",
        " נק\"א</div>": " pp</div>",
        # section 4
        "📍 פרופיל יישוב: השכלה מול הצבעה, 1972–2022": "📍 Locality Profile: Education vs Voting, 1972–2022",
        "חמישה מפקדי אוכלוסין (1972, 1983, 1995, 2008, 2022) מול 13 מערכות בחירות. בחרו יישוב:":
            "Five censuses (1972, 1983, 1995, 2008, 2022) against 13 elections. Pick a locality:",
        "הקלידו שם יישוב…": "Type a locality name…",
        "label:'% אקדמאים (מפקדים)'": "label:'% academics (censuses)'",
        "label:'% הצבעה ימין-חרדים'": "label:'% Right-Haredi vote'",
        "`מפקד ": "`Census ",
        "% אקדמאים`": "% academics`",
        "% ימין-חרדים`": "% Right-Haredim`",
        "text:'% אקדמאים'": "text:'% academics'",
        "text:'% ימין-חרדים'": "text:'% Right-Haredim'",
        "`מדד דתיות 2022 (משקי בית): <b": "`Religiosity index 2022 (households): <b",
        "'אשכול חברתי-כלכלי: '": "'Socioeconomic cluster: '",
        "`פיזור תוך-עירוני 2021: <b": "`Within-city dispersion 2021: <b",
        "</b> (יחסי לארצי)`": "</b> (relative to national)`",
        "'אין נתוני רשות שנתיים ליישוב זה (אינו רשות מקומית עצמאית, ככל הנראה שייך למועצה אזורית).'":
            "'No annual authority data for this locality (not an independent municipality, likely part of a regional council).'",
        "'שכר ממוצע (₪)'": "'Average wage (₪)'",
        "label:'שכר · מושג חדש (2022+)'": "label:'Wage · new concept (2022+)'",
        "'ג\\'יני שכר (אי-שוויון תוך-עירוני)'": "'Wage Gini (within-city inequality)'",
        "`ג'יני ": "`Gini ",
        "`שכר ממוצע ${it.parsed.x}: ₪": "`Average wage ${it.parsed.x}: ₪",
        "' (מושג חדש)'": "' (new concept)'",
        "text:\"ג'יני\"": "text:\"Gini\"",
        "'פאנל הרשויות השנתי (למ\"ס): שכר לפי שנת ההתייחסות (בפיגור שנה אחרי שנת הקובץ); מ-2022 שונה מושג השכר (קו מקווקו); אין להשוות רמות על-פני הקו. ג\\'יני שכירים פורסם עד 2021.'":
            "'The annual authority panel (CBS): wage by reference year (lagging one year behind the file year); from 2022 the wage concept changed (dashed line); do not compare levels across the line. Wage-earner Gini published through 2021.'",
        # gradient chart JS
        "? 'שיפוע' : 'מתאם r'": "? 'Slope' : 'correlation r'",
        "?'שיפוע':'r'": "?'slope':'r'",
        "רו\"ס 95%: ": "95% CI: ",
        " עד ": " to ",
        "</span> יישובים`": "</span> localities`",
        " יישובים`": " localities`",
        "מגמה לעשור: <b": "Trend per decade: <b",
        "'נק\"א ימין-חרדים לנק\"א אקדמאים'": "'RH pp per pp of academics'",
        "'מתאם משוקלל (r)'": "'Weighted correlation (r)'",
        # income chart JS
        "'שכר ממוצע (לוג) · פאנל הרשויות'": "'Average wage (log) · authority panel'",
        "'% אקדמאים · אותן רשויות'": "'% academics · same authorities'",
        "'% זכאים לבגרות'": "'% bagrut-eligible'",
        "'% אקדמאים · כל ~900 היישובים'": "'% academics · all ~900 localities'",
        "`כל היישובים (מפקדים): r ": "`All localities (censuses): r ",
        "wage:'שכר (לוג)'": "wage:'wage (log)'",
        "acad:'% אקדמאים'": "acad:'% academics'",
        "bagrut:'% בגרות'": "bagrut:'% bagrut'",
        "</span> רשויות`": "</span> authorities`",
        " רשויות`": " authorities`",
        "text:'מתאם משוקלל (r) עם הצבעת ימין-חרדים'": "text:'Weighted correlation (r) with the RH vote'",
        "`שכר 1999→2022: <b": "`Wage 1999→2022: <b",
        "`אקדמאים 1999→2022: <b": "`Academics 1999→2022: <b",
        "'מגמת שכר לעשור'": "'Wage trend per decade'",
        "'מגמת השכלה לעשור'": "'Education trend per decade'",
        "'הפרש המגמות (השכלה−שכר)'": "'Trend difference (education−wage)'",
        # methodology
        "מתודולוגיה ומקורות": "Methodology & Sources",
        "<b>מפקדים:</b> גיליון \"השוואות בין מפקדים\" של הקובץ המסוכם למפקד 2008 (למ\"ס): כ-1,050 יישובים במשתנים אחידים ל-1972/1983/1995/2008, בתוספת נתוני יישוב ממפקד 2022. אחוז אקדמאים על בסיס בני 15+. הצמדה ליישובי לוח הבחירות בהתאמת-שמות שמרנית (כ-97%–99% מציבור הבוחרים היהודי מכוסה).":
            "<b>Censuses:</b> the \"inter-census comparisons\" sheet of the CBS 2008 census summary file: ~1,050 localities with harmonized variables for 1972/1983/1995/2008, plus locality data from the 2022 census. % academics based on ages 15+. Joined to the election localities via conservative name matching (~97%–99% of the Jewish electorate covered).",
        "<b>מדד חברתי-כלכלי:</b> פרסומי הלמ\"ס לרשויות (2008, 2013, 2015, 2021) ולאזורים סטטיסטיים בתוך ערים (2008, 2017, 2019, 2021). המדד מתוקנן פר-שנתון; השוואות בין שנים נעשות ביחידות יחסיות או באשכולות בלבד. פיזור תוך-עירוני = סטיית-תקן משוקללת-אוכלוסייה של ערכי האזורים הסטטיסטיים בעיר (≥3 אזורים); משוחזר בקוד ותואם אחד-לאחד את הלוחות הרשמיים (ב5 של 2008, לוח 14 של 2019).":
            "<b>Socioeconomic index:</b> CBS publications for authorities (2008, 2013, 2015, 2021) and for statistical areas within cities (2008, 2017, 2019, 2021). The index is standardized per vintage; cross-year comparisons use relative units or clusters only. Within-city dispersion = population-weighted SD of the city's statistical-area values (≥3 areas); reproduced in code and matching the official tables one-to-one (2008 table B5, 2019 table 14).",
        "<b>שיפוע ההשכלה:</b> רגרסיה/מתאם משוקללי-בוחרים (משקל = ציבור בוחרים רשום) של אחוז הצבעה לימין-חרדים על אחוז אקדמאים, בכל מערכת בחירות בנפרד; רווחי-סמך ומגמה על-פני-זמן ב-bootstrap יישובים (B=1,000). וריאנט \"השכלה קבועה 2008\" מקבע את המשתנה המסביר ומבודד שינוי התנהגותי משינוי הרכב.":
            "<b>Education gradient:</b> voter-weighted regression/correlation (weight = registered electorate) of the Right-Haredi vote share on % academics, per election; confidence intervals and the over-time trend via locality bootstrap (B=1,000). The \"fixed education 2008\" variant freezes the explanatory variable, isolating behavioral change from compositional change.",
        "<b>פאנל הרשויות השנתי:</b> קובצי \"הרשויות המקומיות בישראל\" של הלמ\"ס: קובץ לשנה, 1999–2024 (~255 רשויות בשנה). השכר הממוצע מתייחס לשנה שקדמה לשנת הקובץ (ובקובץ 2021, ל-2019); מקובץ 2022 שונה מושג השכר (הכנסות כלל בעלי ההכנסה); נלקחה תת-העמודה של בעלי הכנסה משכר בלבד לרציפות מושגית, וההשוואות נעשות חתך-חתך, לא ברמות. אחוז הזכאים לבגרות מושווה חתך-חתך בלבד (רפורמות חינוך משנות רמות). מדד הג'יני (שכירים) פורסם עד 2021.":
            "<b>Annual authority panel:</b> the CBS \"Local Authorities in Israel\" files: one per year, 1999–2024 (~255 authorities/yr). The average wage refers to the year before the file year (in the 2021 file, to 2019); from the 2022 file the wage concept changed (income of all earners); the wage-earners-only subcolumn was taken for conceptual continuity, and comparisons are cross-sectional, not in levels. Bagrut eligibility is compared cross-sectionally only (education reforms shift levels). The Gini index (wage earners) was published through 2021.",
        "<b>מעברים לפי שלישים:</b> אותה שיטת ריבועים-פחותים-מאולצים של עמוד נדידת הקולות (קרדיט: הראל קין ואיתמר מושקין), נפתרת בנפרד לכל שליש השכלה של המגזר היהודי (שלישים משוקללי-בוחרים, לפי אקדמאים באינטרפולציה לשנת בחירות היעד). שורות דלות-קולות בתוך שליש (למשל השורה החרדית בשליש העליון) רועשות — מוצגת אזהרה.":
            "<b>Transfers by tercile:</b> the same constrained-least-squares method as the vote-transfers page (credit: Harel Cain and Itamar Mushkin), solved separately for each education tercile of the Jewish sector (voter-weighted terciles, by academics interpolated to the destination election year). Vote-thin rows within a tercile (e.g. the Haredi row in the top tercile) are noisy — a warning is shown.",
        "<b>המגבלה הקבועה:</b> כל האומדנים אקולוגיים: צבירים יישוביים/אזוריים, לא מצביעים בודדים. \"שיפוע השכלה\" הוא תכונת יישובים; אין להסיק ממנו על הקשר ברמת הפרט (כשל אקולוגי).":
            "<b>The standing limitation:</b> all estimates are ecological: locality/area aggregates, not individual voters. The \"education gradient\" is a property of localities; do not infer the individual-level relationship from it (ecological fallacy).",
    },
    # ------------------------------------------------------------------ election_map
    "election_map": {
        # party-mode label toggle (strongholds vs national-vote suppliers)
        "אילו עשרה יישובים מתויגים על המפה: מעוזים = אחוז ההצבעה הגבוה ביותר ביישוב · ספקיות הקולות = הנתח הגדול ביותר מסך הקולות הארצי של המפלגה":
            "Which ten localities get tagged on the map: strongholds = highest local vote share · vote suppliers = largest slice of the party's national vote",
        ">מעוזים</button>": ">Strongholds</button>",
        ">ספקיות הקולות</button>": ">Vote suppliers</button>",
        "% מהמפלגה`": "% of party votes`",
        "מפת בחירות ישראל": "Israel Elections Map",
        "☰ עמודי האתר": "☰ Site pages",
        ">ימינה במרכז-שמאל</button>": ">Yamina in Center-Left</button>",
        ">ימינה בימין</button>": ">Yamina in Right</button>",
        ">פוליגונים</button>": ">Polygons</button>",
        ">בועות</button>": ">Bubbles</button>",
        ">קרטוגרמה</button>": ">Cartogram</button>",
        # satellite basemap toggle (added 2026-07-07)
        ">🛰️ לוויין</button>": ">🛰️ Satellite</button>",
        "רקע לוויין: תצלומי אוויר במקום המפה הכהה": "Satellite basemap: aerial imagery instead of the dark map",
        ">אחוז</button>": ">Share</button>",
        ">סווינג</button>": ">Swing</button>",
        ">פער מהארץ</button>": ">Gap vs national</button>",
        ">מול</span>": ">vs</span>",
        "חפש יישוב או כתובת...": "Search locality or address...",
        # address search (added 2026-07-07)
        "🔍 מחפש כתובת…": "🔍 Searching address…",
        "לא נמצאה כתובת בישראל": "No such address found in Israel",
        ">בחר יישוב במפה</div>": ">Select a locality on the map</div>",
        ">לחץ על אזור לצפייה בנתונים</div>": ">Click an area to view its data</div>",
        "לחץ על אזור במפה כדי לראות את נתוני הבחירות": "Click an area on the map to see its election results",
        # legend title reads physically left→right (gradient: red/CLA left, blue/RH right)
        "ימין-חרדים ← → מרכז-שמאל-ערבים": "Center-Left-Arabs ← → Right-Haredim",
        "גרור לסינון ישובים": "Drag to filter localities",
        # COLOR_MODES labels + legend strings
        "label:'גוש'": "label:'Bloc'",
        "label:'סווינג'": "label:'Swing'",
        "סווינג שמאלה": "Swing left",
        "סווינג ימינה": "Swing right",
        "label:'פער מהארץ'": "label:'Gap vs national'",
        "יותר מרכז-שמאל מהארץ": "More center-left than national",
        "יותר ימין-חרדים מהארץ": "More right-haredi than national",
        "label:'שינוי פער'": "label:'Trend'",   # renamed from 'Gap change' 2026-07-12 (user)
        "התרחק שמאלה": "Moved left",
        "התרחק ימינה": "Moved right",
        "פער גדל שמאלה": "Gap grew leftward",
        "פער גדל ימינה": "Gap grew rightward",
        "label:'ימין'": "label:'Right'",
        "label:'חרדים'": "label:'Haredim'",
        "label:'ערבים'": "label:'Arabs'",
        "label:'שמאל'": "label:'Left'",
        "label:'מרכז'": "label:'Center'",
        "'100% ימין-חרדים'": "'100% Right-Haredim'",
        "'100% מרכז-שמאל-ערבים'": "'100% Center-Left-Arabs'",
        "100% ימין": "100% Right",
        "100% חרדים": "100% Haredim",
        "100% ערבים": "100% Arabs",
        "100% שמאל": "100% Left",
        "100% מרכז-שמאל": "100% Center-Left",
        "100% מרכז": "100% Center",
        "100% הצבעה": "100% turnout",
        "label:'מפלגה מנצחת'": "label:'Winning party'",
        "label:'מפלגה'": "label:'Party'",
        "ראש בראש": "Head to head",
        "s.textContent = 'ניסיוני'": "s.textContent = 'experimental'",  # duel exp badge (2026-07-12)
        "שינוי בשיעור ההצבעה": "Turnout change",
        "שיעור הצבעה": "Turnout",
        "'ירידה'": "'Decline'",
        "'עלייה'": "'Rise'",
        "'מתחת לארצי'": "'Below national'",
        "'מעל הארצי'": "'Above national'",
        # play overlay + legend party branches
        "'עוד ▾'": "'More ▾'",
        "'עוד ▴'": "'More ▴'",
        "' · לא התמודדה'": "' · did not contest'",
        "לא התמודדו שתיהן בכנסת": "not both contested in Knesset",
        "לא התמודדה בכנסת": "did not contest in Knesset",
        "'בחר מפלגה'": "'Select a party'",
        "המפלגה הגדולה ביישוב": "Largest party per locality",
        "פער מהארצי · ": "Gap vs national · ",
        "פער מהארץ": "Gap vs national",
        " מול ": " vs ",
        ">אחרות<b>": ">Other<b>",
        # filter labels
        "'% ל'": "'% to '",
        "'ב׳'": "'B'",
        "'א׳'": "'A'",
        " ישובים`": " localities`",
        # panel
        ">בעלי זכות</div>": ">Registered</div>",
        " בעלי זכות": " registered",
        ">כשרים</div>": ">Valid votes</div>",
        ">הקישו על מדד מקווקו להסבר</div>": ">tap a dotted metric for an explanation</div>",
        "אין נתוני בחירות עבור אזור זה": "No election data for this area",
        "אין נתונים לבחירות אלו": "No data for this election",
        "' · ימינה בימין'": "' · Yamina in Right'",
        "מרווח: ": "Margin: ",
        "סווינג מכ": "Swing since K",
        "'ללא שינוי משמעותי'": "'No significant change'",
        "'למרכז-שמאל-ערבים'": "'toward Center-Left-Arabs'",
        "'לימין-חרדים'": "'toward Right-Haredim'",
        ">שינוי לפי גוש</div>": ">Change by bloc</div>",
        ">מגמות היסטוריות: גושים</div>": ">Historical trends: blocs</div>",
        "מגמה כוללת: ": "Overall trend: ",
        "'(שמאלה)'": "'(leftward)'",
        "'(ימינה)'": "'(rightward)'",
        "'(יציב)'": "'(stable)'",
        ">פירוט גושים</div>": ">Bloc breakdown</div>",
        ">דמוגרפיה (2019)</div>": ">Demographics (2019)</div>",
        ">יהודים: <b>": ">Jews: <b>",
        ">ערבים: <b>": ">Arabs: <b>",
        ">מוסלמים: <b>": ">Muslims: <b>",
        ">דרוזים: <b>": ">Druze: <b>",
        ">ללא סיווג: <b>": ">Unclassified: <b>",
        ">פילוג מפלגתי</span>": ">Party breakdown</span>",
        " מפלגות</span>": " parties</span>",
        ">הצג עוד ": ">Show ",
        " מפלגות ▾</button>": " more parties ▾</button>",
        " ביישוב לאורך השנים</div>": " in this locality over the years</div>",
        "label:'ביישוב'": "label:'in locality'",
        "label:'ארצי'": "label:'national'",
        "catA ? catA.name : 'א'": "catA ? catA.name : 'A'",
        "catB ? catB.name : 'ב'": "catB ? catB.name : 'B'",
        " ביישוב\n": " in this locality\n",
        "שגיאה בטעינת הנתונים.<br>ודא שקובץ election_map_geo.json נמצא בתיקיית data/":
            "Error loading the data.<br>Make sure election_map_geo.json is in the data/ directory",
        " · גבולות: למ\"ס": " · Boundaries: CBS",
        # ---- direct-PM mode (2026-07). JS-string values kept apostrophe-free. ----
        # picker buttons + tooltips (the PM_CONTESTS candidate names are handled in FIXES)
        "title=\"נתניהו מול פרס\"": "title=\"Netanyahu vs Peres\"",
        "title=\"ברק מול נתניהו\"": "title=\"Barak vs Netanyahu\"",
        "title=\"שרון מול ברק: בחירות מיוחדות לרה&quot;מ בלבד\"": "title=\"Sharon vs Barak: a special PM-only election\"",
        "title=\"תוצאה = מרווח בין שני המועמדים · סווינג = שינוי המרווח מהבחירות הישירות הקודמות · פער מהארץ = הפרש מהתוצאה הארצית · שינוי בפער = כיצד השתנה הפער מהארץ בין שתי בחירות ישירות · הפרש קולות = יתרון המועמד המוביל בקולות (מומלץ בתצוגת בועות) · שיעור הצבעה = מצביעים מתוך בעלי זכות · פיצול = הפרש בין הקול לרה&quot;מ ובין הקול הגושי לכנסת שנבחרה באותו יום (1996/1999 בלבד)\"":
            "title=\"Result = the margin between the two candidates · Swing = the margin change vs the previous direct election · Gap vs national = difference from the national result · Gap change = how the gap vs national moved between two direct elections · Net votes = the leading candidate&#39;s raw-vote lead (best in the bubbles display) · Turnout = voters out of eligible · Split = the gap between the PM vote and the bloc vote for the Knesset elected on the same day (1996/1999 only)\"",
        ">תוצאה</button>": ">Result</button>",
        ">פיצול מול הכנסת</button>": ">Split vs the Knesset</button>",
        # pm swing/gap/turnout submodes (2026-07)
        "סווינג מ-${PM_PREV[pmContest]} ל-${pmContest}": "Swing ${PM_PREV[pmContest]} → ${pmContest}",
        "יותר ${m.lShort} מהארץ": "More ${m.lShort} than national",
        "יותר ${m.rShort} מהארץ": "More ${m.rShort} than national",
        "פער מהארץ · בחירה ישירה ${pmContest}": "Gap vs national · direct PM vote ${pmContest}",
        "שיעור הצבעה · בחירה ישירה ${pmContest}": "Turnout · direct PM vote ${pmContest}",
        "שמאלי מהארץ": "left of national",
        "ימני מהארץ": "right of national",
        "סווינג מ-${prevY}: ${Math.abs(sw).toFixed(1)}% ל${sw >= 0 ? m.rShort : m.lShort}":
            "Swing from ${prevY}: ${Math.abs(sw).toFixed(1)}% toward ${sw >= 0 ? m.rShort : m.lShort}",
        # pm gap_change / net submodes (2026-07)
        ">שינוי בפער</button>": ">Gap change</button>",
        ">הפרש קולות</button>": ">Net votes</button>",
        "שינוי בפער מהארץ מ-${PM_PREV[pmContest]} ל-${pmContest}":
            "Gap-vs-national change ${PM_PREV[pmContest]} → ${pmContest}",
        "הפרש קולות · בחירה ישירה ${pmContest}": "Net vote differential · direct PM vote ${pmContest}",
        "יתרון קולות ל${m.lShort}": "Vote lead for ${m.lShort}",
        "יתרון קולות ל${m.rShort}": "Vote lead for ${m.rShort}",
        # Knesset net-votes mode (2026-07-12)
        "label:'הפרש קולות'": "label:'Net votes'",
        "'יתרון קולות למרכז-שמאל'": "'Vote lead for Center-Left'",
        "'יתרון קולות לימין-חרדים'": "'Vote lead for Right-Haredim'",
        "`הפרש קולות · כנסת ${currentElection}`": "`Net vote differential · Knesset ${currentElection}`",
        "הפרש קולות: ${Math.abs(netV).toLocaleString()} ל${netV >= 0 ? 'ימין-חרדים' : 'מרכז-שמאל-ערבים'}":
            "Net vote differential: ${Math.abs(netV).toLocaleString()} for ${netV >= 0 ? 'Right-Haredim' : 'Center-Left-Arabs'}",
        "'מרכז-שמאל'": "'Center-Left'",
        "' קולות ל'": "' votes for '",
        "הפרש קולות: ${Math.abs(net).toLocaleString()} ל${net >= 0 ? m.rShort : m.lShort}":
            "Net vote differential: ${Math.abs(net).toLocaleString()} for ${net >= 0 ? m.rShort : m.lShort}",
        "שינוי בפער מהארץ מ-${prevY}: ${Math.abs(gc).toFixed(1)}% לכיוון ${gc >= 0 ? m.rShort : m.lShort}":
            "Gap-vs-national change from ${prevY}: ${Math.abs(gc).toFixed(1)}% toward ${gc >= 0 ? m.rShort : m.lShort}",
        "label:'בחירה ישירה'": "label:'Direct PM vote'",
        # time-lapse label
        "בחירה ישירה ${ys[j]} · ${m.rShort} מול ${m.lShort}": "Direct election ${ys[j]} · ${m.rShort} vs ${m.lShort}",
        # legend
        "לרה\"מ שמאלי מהקול לכנסת": "PM vote left of the Knesset vote",
        "לרה\"מ ימני מהקול לכנסת": "PM vote right of the Knesset vote",
        "פיצול קול · רה\"מ ${pmContest} מול כנסת ${m.kn}": "Ticket splitting · PM ${pmContest} vs Knesset ${m.kn}",
        "בחירה ישירה לרה\"מ ${pmContest} · ${m.rShort} מול ${m.lShort}": "Direct PM election ${pmContest} · ${m.rShort} vs ${m.lShort}",
        # filter slider readout
        "'פיצול שמאלה'": "'split leftward'",
        "'פיצול ימינה'": "'split rightward'",
        # panel
        "בחירה ישירה לרה\"מ · ${pmContest} · ${p.type}": "Direct PM election · ${pmContest} · ${p.type}",
        "אין נתוני בחירה ישירה ליישוב זה": "No direct-election data for this locality",
        "tile('בעלי זכות',": "tile('Eligible voters',",
        "tile('הצביעו',": "tile('Voted',",
        "tile('שיעור הצבעה',": "tile('Turnout',",
        "מרווח: ${Math.abs(margin).toFixed(1)}% ל${margin >= 0 ? m.rShort : m.lShort}":
            "Margin: ${Math.abs(margin).toFixed(1)}% for ${margin >= 0 ? m.rShort : m.lShort}",
        "פסולים ולבנים: ${invalid.toLocaleString()} (${(invalid/s.voted*100).toFixed(1)}% מהמצביעים)":
            "Invalid and blank ballots: ${invalid.toLocaleString()} (${(invalid/s.voted*100).toFixed(1)}% of voters)",
        "ארצי: ${m.rShort} ${nat.r2.toFixed(1)}% · ${m.lShort} ${nat.l2.toFixed(1)}%":
            "National: ${m.rShort} ${nat.r2.toFixed(1)}% · ${m.lShort} ${nat.l2.toFixed(1)}%",
        "פער מהארץ: ${Math.abs(gap).toFixed(1)}% ל${gap >= 0 ? m.rShort : m.lShort}":
            "Gap vs national: ${Math.abs(gap).toFixed(1)}% for ${gap >= 0 ? m.rShort : m.lShort}",
        "הקול לרה\"מ ימני מהקול לכנסת": "The PM vote ran right of the Knesset vote",
        "הקול לרה\"מ שמאלי מהקול לכנסת": "The PM vote ran left of the Knesset vote",
        "'אין פיצול משמעותי'": "'No meaningful split'",
        "פיצול הקול מול הבחירות לכנסת ${m.kn} (באותו יום)": "Ticket splitting vs the Knesset ${m.kn} election (same day)",
        "ימין-חרדים בכנסת (דו-גושי)": "Right-Haredi bloc, Knesset vote (two-bloc)",
        "${m.rShort} לרה\"מ (דו-מועמדי)": "${m.rShort} for PM (two-candidate)",
        "בחירות מיוחדות לרה\"מ בלבד, ללא בחירות מקבילות לכנסת": "A special PM-only election, with no parallel Knesset vote",
        "שינוי בשיעור ההצבעה מ-1999": "Turnout change from 1999",
        "שלוש הבחירות הישירות ביישוב": "The three direct PM elections in this locality",
    },
    # ------------------------------------------------------------------ dashboard
    "dashboard": {
        "השוואת בחירות: כנסת 13 עד כנסת 25": "Election Comparison: Knesset 13 to Knesset 25",
        "תוצאות ארציות | 13 מערכות בחירות (1992-2022)": "National results | 13 elections (1992–2022)",
        # nav
        ">אודות ומתודולוגיה</button>": ">About & Methodology</button>",
        ">תוצאות ארציות</button>": ">National Results</button>",
        ">ניתוח לפי ישובים (1,391)</button>": ">Locality Analysis (1,391)</button>",
        ">ניתוח סוציו-אקונומי (<span": ">Socioeconomic Analysis (<span",
        ">קיטוב ומיון</button>": ">Polarization & Sorting</button>",
        ">מפה אינטראקטיבית</button>": ">Interactive Map</button>",
        ">סקרי 2026</button>": ">2026 Polling</button>",
        # ---------- disclosures ----------
        ">אודות הדשבורד ומתודולוגיה</h2>": ">About the Dashboard & Methodology</h2>",
        ">📊 מקורות המידע</h3>": ">📊 Data Sources</h3>",
        "<strong>תוצאות בחירות ואחוזי הצבעה לפי יישוב (כנסת 13–25):</strong> ועדת הבחירות המרכזית לכנסת; חלק מקובצי התוצאות ההיסטוריים דרך מאגר המידע הממשלתי":
            "<strong>Election results and turnout by locality (Knesset 13–25):</strong> the Central Elections Committee; some historical result files via the government open-data portal",
        "<strong>מדד חברתי-כלכלי:</strong> הלשכה המרכזית לסטטיסטיקה (הלמ\"ס): פרסומי המדד לרשויות מקומיות (2008, 2013, 2015, 2021) ולאזורים סטטיסטיים בתוך ערים (2008, 2017, 2019, 2021), כולל לוחות הפיזור התוך-עירוני הרשמיים (לוח ב5 של 2008, לוח 14 של 2019).":
            "<strong>Socioeconomic index:</strong> the Central Bureau of Statistics (CBS): index publications for local authorities (2008, 2013, 2015, 2021) and for statistical areas within cities (2008, 2017, 2019, 2021), including the official within-city dispersion tables (2008 table B5, 2019 table 14).",
        "<strong>מפקדי אוכלוסין:</strong> הלמ\"ס: הקובץ המסוכם ליישובים של מפקד 2008, כולל גיליון \"השוואות בין מפקדים\" (1972, 1983, 1995, 2008), ונתוני יישובים ואזורים סטטיסטיים ממפקד 2022.":
            "<strong>Censuses:</strong> CBS: the 2008 census locality summary file, including the \"inter-census comparisons\" sheet (1972, 1983, 1995, 2008), plus locality and statistical-area data from the 2022 census.",
        "<strong>פרופילי רשויות שנתיים:</strong> הלמ\"ס: פרסומי \"הרשויות המקומיות בישראל\", קובץ לשנה, 1999–2024 (שכר ממוצע, זכאות לבגרות, מדד ג'יני, מאזני הגירה, אוכלוסייה).":
            "<strong>Annual authority profiles:</strong> CBS: the \"Local Authorities in Israel\" publications, one file per year, 1999–2024 (average wage, bagrut eligibility, Gini index, migration balances, population).",
        "<strong>נתוני דת ו\"רוסים\":</strong> הלמ\"ס: נתוני אוכלוסייה ביישובים, 2019.":
            "<strong>Religion and \"Russians\" data:</strong> CBS: locality population data, 2019.",
        "<strong>גבולות גיאוגרפיים:</strong> שכבת האזורים הסטטיסטיים של הלמ\"ס (2022); רקע המפה: CARTO / OpenStreetMap (ראו קרדיטים).":
            "<strong>Geographic boundaries:</strong> the CBS statistical-areas layer (2022); map basemap: CARTO / OpenStreetMap (see credits).",
        "<strong>סקרי בחירות:</strong> מדד הבחירות הישראלי (INES): 14 סקרי בחירות 1992–2022, לשכבת האימות של עמוד נדידת הקולות (ראו קרדיטים). ציטוט מחקרי INES בפורמט הרשמי, מחקר-מחקר (למשל: <span style=\"direction:ltr; unicode-bidi:isolate\">Israel National Election Studies. 2022. INES 2022 Election Study Full Release [dataset and documentation]. https://www.tau.ac.il/~ines/</span>); הרשימה המלאה בתחתית עמוד נדידת הקולות.":
            "<strong>Election surveys:</strong> the Israel National Election Studies (INES): 14 election surveys 1992–2022, used for the validation layer of the vote-transfers page (see credits). INES studies are cited in the official per-study format (e.g.: <span style=\"direction:ltr; unicode-bidi:isolate\">Israel National Election Studies. 2022. INES 2022 Election Study Full Release [dataset and documentation]. https://www.tau.ac.il/~ines/</span>); the full list is at the bottom of the vote-transfers page.",
        ">🙏 קרדיטים</h3>": ">🙏 Credits</h3>",
        "<strong>שיטת אומדן נדידת הקולות:</strong>": "<strong>Vote-transfer estimation method:</strong>",
        ">הראל קין — \"קולות נודדים\"</a> ואיתמר מושקין. המימוש כאן הוא מימוש עצמאי (clean-room) של השיטה על נתוני יישובים; תוצאותיו אומתו מול אומדני רמת-הקלפי של קין במעברים החופפים (r≈0.99). פרויקט המקור מתפרסם ברישיון":
            ">Harel Cain, \"Kolot Nodedim\"</a> and Itamar Mushkin. The implementation here is an independent (clean-room) reimplementation of the method on locality data; its results were validated against Cain's ballot-box-level estimates on the overlapping transitions (r≈0.99). The original project is published under a",
        "<strong>סקרי הבחירות:</strong>": "<strong>Election surveys:</strong>",
        ">מדד הבחירות הישראלי (INES)</a>, אוניברסיטת תל אביב: פרויקט סקרי הבחירות שייסדו וניהלו אשר אריאן ז\"ל ומיכל שמיר. הסקרים משמשים כאומדן עצמאי להצלבת מטריצות המעבר בלבד; כל ניתוח ופרשנות באחריות אתר זה.":
            ">the Israel National Election Studies (INES)</a>, Tel Aviv University: the election-survey project founded and led by the late Asher Arian and Michal Shamir. The surveys serve only as an independent estimate for cross-checking the transfer matrices; all analysis and interpretation are this site's responsibility.",
        "<strong>נתונים רשמיים:</strong> הלשכה המרכזית לסטטיסטיקה (מפקדים, מדד חברתי-כלכלי, שכבות גיאוגרפיות) וועדת הבחירות המרכזית לכנסת (תוצאות). העיבודים, ההצלבות והמסקנות הם באחריות אתר זה בלבד ואינם מטעם הגופים הרשמיים.":
            "<strong>Official data:</strong> the Central Bureau of Statistics (censuses, socioeconomic index, geographic layers) and the Central Elections Committee (results). The processing, cross-referencing and conclusions are this site's responsibility alone and are not endorsed by the official bodies.",
        "<strong>רקע המפה:</strong> אריחי מפה של": "<strong>Map basemap:</strong> map tiles by",
        "על בסיס נתוני": "based on data from",
        "(רישיון ODbL).": "(ODbL license).",
        "<strong>ספריות קוד פתוח:</strong> תצוגה:": "<strong>Open-source libraries:</strong> display:",
        "; ניתוח: Python‏ (pandas, NumPy) ו-CVXPY/SCS לפתרון בעיות האופטימיזציה של מטריצות המעבר.</li>":
            "; analysis: Python (pandas, NumPy) and CVXPY/SCS for solving the transfer-matrix optimization problems.</li>",
        ">🔬 עמודי המחקר הנלווים</h3>": ">🔬 Companion Research Pages</h3>",
        ">🔀 נדידת קולות</a>:</strong> אומדן מעברי מצביעים בין כל שתי מערכות בחירות סמוכות (1992–2022) בהסקה אקולוגית (ריבועים פחותים עם אילוצים על פני כ-1,000–1,150 יישובים), לצד אומדן עצמאי מסקרי INES להצלבה. מתודולוגיה מלאה בתחתית העמוד.":
            ">🔀 Vote Transfers</a>:</strong> estimated voter flows between every two consecutive elections (1992–2022) via ecological inference (constrained least squares over ~1,000–1,150 localities), alongside an independent INES-survey estimate for cross-checking. Full methodology at the bottom of the page.",
        ">🎓 דמוגרפיה והצבעה</a>:</strong> שיפוע ההשכלה לאורך 30 שנה (מפקדי 1972–2022) ברמת היישוב וברמת הפרט (סקרי INES), ופיזור המדד החברתי-כלכלי בתוך הערים מול המיון הפוליטי בין היישובים. מתודולוגיה מלאה בתחתית העמוד.":
            ">🎓 Demographics & Voting</a>:</strong> the education gradient over 30 years (1972–2022 censuses) at the locality and individual (INES) level, and within-city socioeconomic dispersion vs political sorting between localities. Full methodology at the bottom of the page.",
        ">📊 קיטוב ומיון</a>:</strong> ממצא ההלאמה-לצד-מיון (ראו כרטיס המתודולוגיה למטה), זמין גם כעמוד עצמאי.":
            ">📊 Polarization & Sorting</a>:</strong> the nationalization-alongside-sorting finding (see the methodology card below), also available as a standalone page.",
        ">🏛️ הגדרת הגושים</h3>": ">🏛️ Bloc Definitions</h3>",
        ">המפלגות מחולקות ל-5 קבוצות משנה שמתאגדות ל-2 גושים עיקריים:</p>":
            ">Parties are grouped into 5 sub-blocs that aggregate into 2 main blocs:</p>",
        ">ליכוד, ימינה, הבית היהודי...</div>": ">Likud, Yamina, Jewish Home...</div>",
        ">ש\"ס, יהדות התורה</div>": ">Shas, United Torah Judaism</div>",
        ">ישראל ביתנו (כ21-25), ימינה ותקווה חדשה (כ24)</div>": ">Yisrael Beiteinu (K21–25), Yamina & New Hope (K24)</div>",
        ">יש עתיד, כחול לבן, קדימה...</div>": ">Yesh Atid, Blue and White, Kadima...</div>",
        ">העבודה, מרצ</div>": ">Labor, Meretz</div>",
        ">רע\"מ, חד\"ש, בל\"ד...</div>": ">Ra'am, Hadash, Balad...</div>",
        ">ימין + חרדים</div>": ">Right + Haredim</div>",
        ">מרכז + שמאל + ערבים</div>": ">Center + Left + Arabs</div>",
        ">📋 פירוט מפלגות לפי בחירות (לחץ להרחבה)</summary>": ">📋 Party breakdown by election (click to expand)</summary>",
        "ההבחנה בין ימין קואליציוני לימין אופוזיציוני תואמת את ספרות המחקר: כרך 2019–2021 של The Elections in Israel מבחין בין הגוש הימני-דתי ובין הגוש הנתניהו-תואם: סירובו של ליברמן להצטרף לקואליציה של נתניהו אחרי אפריל 2019 הפך רוב ימני מספרי לבלתי-ניתן למימוש, והוא שהוליד את מערך חמש מערכות הבחירות של 2019–2022. [The Elections in Israel 2019–2021, עמ׳ 20–21]":
            "The distinction between coalition right and opposition right matches the research literature: the 2019–2021 volume of The Elections in Israel distinguishes the right-religious bloc from the Netanyahu-compatible bloc: Liberman's refusal to join a Netanyahu coalition after April 2019 turned a numeric right-wing majority into one that could not be realized, and it is what produced the five-election sequence of 2019–2022. [The Elections in Israel 2019–2021, pp. 20–21]",
        ">🇷🇺 הגדרת \"רוסים\"</h3>": ">🇷🇺 Defining \"Russians\"</h3>",
        "המונח <strong>\"רוסים\"</strong> בדשבורד מתייחס לתושבים <strong>ללא סיווג דת</strong> בנתוני הלמ\"ס.":
            "The term <strong>\"Russians\"</strong> in this dashboard refers to residents with <strong>no religious classification</strong> in CBS data.",
        "קבוצה זו כוללת בעיקר עולים מברית המועצות לשעבר ומדינות חבר העמים שאינם מוגדרים כיהודים על פי ההלכה,":
            "This group consists mostly of immigrants from the former Soviet Union and CIS countries who are not classified as Jewish under halakha",
        "אך עלו לישראל מכוח חוק השבות (נכדי יהודים, בני זוג וכו').":
            "but immigrated under the Law of Return (grandchildren of Jews, spouses, etc.).",
        "נתוני הדת זמינים רק מ-2019, ולכן ניתוח \"רוסים\" מוצג רק עבור כנסת 21 ואילך.":
            "Religion data is available only from 2019, so the \"Russians\" analysis is shown only for Knesset 21 onward.",
        ">📅 התאמת נתונים דמוגרפיים לבחירות</h3>": ">📅 Matching Demographic Data to Elections</h3>",
        "הנתונים הסוציו-אקונומיים (הכנסה, השכלה, אשכול וכו') מותאמים לתקופת הבחירות:":
            "The socioeconomic data (income, education, cluster, etc.) is matched to the election period:",
        ">בחירות</th>": ">Election</th>",
        ">שנת נתונים</th>": ">Data year</th>",
        " (אשכול) + 2008 (שאר)": " (cluster) + 2008 (rest)",
        ">📈 חישוב מתאמים</h3>": ">📈 Correlation Computation</h3>",
        "המתאמים (correlations) מחושבים באמצעות <strong>מתאם פירסון משוקלל</strong>,":
            "Correlations are computed as <strong>weighted Pearson correlations</strong>,",
        "כאשר המשקל הוא <strong>מספר בעלי זכות הבחירה</strong> בכל יישוב.":
            "with the weight being <strong>the number of registered voters</strong> in each locality.",
        "שיטה זו מבטיחה שיישובים גדולים (כמו תל אביב או ירושלים) משפיעים יותר על המתאם מאשר יישובים קטנים,":
            "This ensures that large localities (like Tel Aviv or Jerusalem) influence the correlation more than small ones,",
        "מה שמשקף טוב יותר את התמונה הארצית.": "which better reflects the national picture.",
        ">🗺️ מיון גיאוגרפי - הגדרת \"משכילים\"</h3>": ">🗺️ Geographic Sorting: Defining \"Educated\"</h3>",
        "בגרף המיון הגיאוגרפי, יישוב מוגדר כ<strong>\"משכיל\"</strong> אם אחוז בעלי התואר האקדמי בו":
            "In the geographic-sorting chart, a locality is defined as <strong>\"educated\"</strong> if its share of academic-degree holders is",
        "גבוה ב-<strong>0.5 סטיות תקן</strong> מעל הממוצע של כלל היישובים באותה תקופה.":
            "more than <strong>0.5 standard deviations</strong> above the all-locality mean of that period.",
        "הסף הדינמי מאפשר השוואה הוגנת בין תקופות, למרות שאחוז האקדמאים עלה משמעותית לאורך השנים.":
            "The dynamic threshold allows fair comparison across periods, even though the share of academics rose substantially over the years.",
        ">📊 קיטוב ומיון: מתודולוגיית המחקר</h3>": ">📊 Polarization & Sorting: Research Methodology</h3>",
        "לשונית <strong>\"קיטוב ומיון\"</strong> בוחנת שאלה אחת: האם הפוליטיקה הישראלית <strong>הולאמה</strong> (היישובים נעים יחד) או <strong>מוינה גיאוגרפית</strong> (היישובים מתרחקים זה מזה) בין 1992 ל-2022.":
            "The <strong>\"Polarization & Sorting\"</strong> tab examines one question: did Israeli politics <strong>nationalize</strong> (localities moving together) or <strong>geographically sort</strong> (localities drifting apart) between 1992 and 2022?",
        "<strong>פאנל מאוזן:</strong> 896 יישובים שיש להם נתונים בכל 13 מערכות הבחירות (כ13–כ25).":
            "<strong>Balanced panel:</strong> 896 localities with data in all 13 elections (K13–K25).",
        "<strong>שקלול לפי אוכלוסייה:</strong> כל מדד משוקלל לפי מספר בעלי זכות הבחירה ביישוב, כך שהתוצאה משקפת בוחרים ולא יישובים.":
            "<strong>Population weighting:</strong> every metric is weighted by the locality's registered voters, so results reflect voters, not localities.",
        "<strong>מדדי מיון</strong> (פיזור גוש ימין-חרדים בין היישובים): סטיית תקן משוקללת, פער אחוזון 90 מול אחוזון 10, ומדד ההפרדה (dissimilarity) בין שני הגושים.":
            "<strong>Sorting metrics</strong> (dispersion of the Right-Haredi bloc across localities): weighted SD, the 90th-vs-10th percentile gap, and the dissimilarity index between the two blocs.",
        "<strong>מדד הלאמה:</strong> סטיית התקן המשוקללת של תנודות היישובים בין כל שתי מערכות עוקבות; ככל שהיא קטנה יותר, התנועה אחידה יותר (מולאמת).":
            "<strong>Nationalization metric:</strong> the weighted SD of locality swings between each two consecutive elections; the smaller it is, the more uniform (nationalized) the movement.",
        "<strong>מובהקות (Bootstrap):</strong> 2,000 דגימות-חוזרות של היישובים מפיקות רווחי-סמך של 95%. כל ארבע המגמות מובהקות (הרווח אינו כולל 0): המיון עולה, ובמקביל התנודות נעשות אחידות יותר: קיטוב הולך וגובר סביב תנודה ארצית משותפת.":
            "<strong>Significance (bootstrap):</strong> 2,000 resamples of the localities produce 95% confidence intervals. All four trends are significant (the interval excludes 0): sorting rises while swings become more uniform: growing polarization around a shared national swing.",
        "<strong>מנגנון</strong> (31 הערים היהודיות הגדולות): המהלך של כל עיר (1992→2022) מתואם עם שלושה משתנים דמוגרפיים: אחוז האקדמאים (השכלה, r≈−0.80), אחוז המשפחות עם 4+ ילדים (פוריות, r≈+0.60), ושיעור ההצבעה החרדית (ש\"ס+יהדות התורה, r≈+0.56) כמדד לחרדיות.":
            "<strong>Mechanism</strong> (the 31 largest Jewish cities): each city's move (1992→2022) is correlated with three demographic variables: % academics (education, r≈−0.80), % families with 4+ children (fertility, r≈+0.60), and the Haredi-party vote (Shas+UTJ, r≈+0.56) as a Harediness measure.",
        "המחקר המלא זמין גם כעמוד עצמאי (": "The full study is also available as a standalone page (",
        "). <strong>הסתייגות אקולוגית:</strong> כל המדדים הם ברמת היישוב המצרפי, לא ברמת הבוחר הבודד; אין להסיק מהם על התנהגות פרטים.":
            "). <strong>Ecological caveat:</strong> all metrics are at the aggregate-locality level, not the individual voter; do not infer individual behavior from them.",
        ">🗺️ שכבות המפה</h3>": ">🗺️ Map Layers</h3>",
        "<strong>יישובים קטנים:</strong> נוספו למפה כ-1,000 יישובים קטנים (מושבים, קיבוצים ויישובים כפריים) על ידי איחוד שכבת האזורים הסטטיסטיים של הלמ\"ס (2022) לפי סמל יישוב. מועצות אזוריות אינן נכללות.":
            "<strong>Small localities:</strong> ~1,000 small localities (moshavim, kibbutzim and rural communities) were added by dissolving the CBS statistical-areas layer (2022) by locality code. Regional councils are not included.",
        "<strong>מצב בועות:</strong> אפשר להציג את היישובים כבועות שגודלן פרופורציונלי לגודל היישוב (מספר בעלי זכות הבחירה), במקום כפוליגונים.":
            "<strong>Bubble mode:</strong> localities can be shown as bubbles sized by locality size (registered voters) instead of polygons.",
        ">⚠️ מגבלות</h3>": ">⚠️ Limitations</h3>",
        "תוצאות 10 מערכות בחירות (2003–2022) ברמת אזור סטטיסטי, מוצלבות עם המפקד בן-זמנן (2022 / 2008 / 1995), עם מיקומי משכני קלפי ושכבת אומדן מגורים. ראו כרטיס \"מפת השכונות: מיקומי קלפיות\" למטה.":
            "results of 10 elections (2003–2022) at statistical-area level, cross-referenced with the contemporaneous census (2022 / 2008 / 1995), with polling-venue locations and a residence-estimate layer. See the \"Neighborhood Map: Polling-Station Locations\" card below.",
        ">🏘️ מפת השכונות: מיקומי קלפיות</h3>": ">🏘️ Neighborhood Map: Polling-Station Locations</h3>",
        "<strong>איך זה נבנה:</strong> כ-32,700 משכני קלפי בכל מערכת בחירות מודרנית מוקמו גאוגרפית ושויכו לאזור הסטטיסטי שבו הם יושבים (point-in-polygon) על גבולות הלמ\"ס: מפקד 2022 (כ21–25), מפקד 2008 (כ18–20) ומפקד 1995 (כ16–17); כל בחירות מוצלבות עם המפקד בן-זמנן.":
            "<strong>How it was built:</strong> ~32,700 polling venues per modern election were geocoded and assigned to the statistical area they sit in (point-in-polygon) on CBS boundaries: the 2022 census (K21–25), the 2008 census (K18–20) and the 1995 census (K16–17); each election is cross-referenced with its contemporaneous census.",
        "<strong>מקור המיקומים ב-2022:</strong> קובץ הכתובות הרשמי של ועדת הבחירות (כתובת לכל קלפי), בתוספת מאות תיקוני מיקום שאומתו ידנית מול רישום מוסדות החינוך, גאומטריות רחובות ובדיקות פרופיל הצבעה. זו השכבה המדויקת ביותר במערכת; משכנים החולקים שם זהה בעיר מופרדים לפי כתובתם הרשמית.":
            "<strong>Location source for 2022:</strong> the official Central Elections Committee address file (an address per polling station), plus hundreds of position fixes verified manually against the Education Ministry institution registry, street geometries and voting-profile checks. This is the most accurate layer in the system; same-named venues within a city are separated by their official addresses.",
        "<strong>בחירות קודמות, בגילוי לב:</strong> קובץ כתובות רשמי קיים רק ל-2022. בכ21–24 המיקומים משוחזרים לפי <strong>שם המשכן</strong> (גיאוקודינג); בכ18–20 לפי התאמת שמות משכנים בין מערכות בחירות; בכ16–17 מתוך כתובות הקלפי המופיעות בקובצי התוצאות של אז. תיקוני מיקום שאומתו מול כתובות 2022 מוחלים אחורה לפי שם; משכן שהחליף בניין בין מערכות עלול להופיע במיקומו של 2022, ושני משכנים בעלי אותו שם אינם ניתנים להפרדה בשנים ללא קובץ כתובות.":
            "<strong>Earlier elections, candidly:</strong> an official address file exists only for 2022. For K21–24 locations are reconstructed from <strong>venue names</strong> (geocoding); for K18–20 from venue-name matching across elections; for K16–17 from the polling-station addresses in the era's own results files. Fixes verified against 2022 addresses are applied backwards by name; a venue that changed buildings between elections may appear at its 2022 location, and two same-named venues cannot be separated in years without an address file.",
        "<strong>אומדן מגורים:</strong> שכבה נפרדת מחלקת את קולות כל משכן חזרה לאזורי המגורים שהוא משרת, לפי קרבה ואוכלוסייה: מודל ולא ספירה ישירה; שגיאה חציונית של כ-4–5.5 נק' באימות hold-out, מוצגת בעמוד.":
            "<strong>Residence estimate:</strong> a separate layer redistributes each venue's votes back to the residential areas it serves, by proximity and population: a model, not a direct count; median hold-out error of ~4–5.5 points, shown on the page.",
        "<strong>מה אינו ניתן למיפוי:</strong> מעטפות כפולות (כ-458 אלף קולות ב-2022) אינן משויכות ליישוב מהותית; כיסוי המיפוי נמוך מהממוצע בחלק מהיישובים הערביים ובהתנחלויות; האחוזים בתוך כל אזור אמינים, אך סיכומים ארציים מהשכבה הזו מוטים מעט.":
            "<strong>What cannot be mapped:</strong> double-envelope ballots (~458K votes in 2022) are inherently unassignable to a locality; mapping coverage is below average in some Arab localities and in the settlements; within-area percentages are reliable, but national sums from this layer are slightly biased.",
        "אותיות רשימה עוברות בירושה בין מפלגות שונות (למשל פה: מפלגת המרכז 1999 ← יש עתיד ← כחול לבן; ת: התחיה 1992 ← תקווה חדשה); בתצוגות חוצות-שנים המפלגות מזוהות לפי שם הרשימה של אותה מערכת בחירות, לא לפי האות בלבד":
            "Ballot letters are inherited across unrelated parties (e.g. Peh: Center Party 1999 → Yesh Atid → Blue &amp; White; Tav: Tehiya 1992 → New Hope); cross-year views identify parties by that election's list name, never by the letter alone",
        "<strong>כנסת 13 (1992)</strong> נוספה לתוצאות הארציות, לניתוח לפי ישובים ולמפה. הניתוח הסוציו-אקונומי אינו כולל את 1992 (נתוני הלמ\"ס אינם מגיעים לשנה זו). התוצאה הארצית מבוססת על התוצאות הרשמיות (כולל קולות חיילים, שאינם משויכים לישובים); כ-67 ישובים קטנים/היסטוריים מ-1992 שלא נמצאה להם התאמה בנתונים הנוכחיים הושמטו מטבלת הישובים. בגושי 1992 נכללו שלוש רשימות שלא עברו את אחוז החסימה: התחיה והמפלגה הליברלית החדשה (ימין) והרשימה המתקדמת לשלום (ערבים); יתר הקולות שמתחת לסף (קטגוריית \"Other\", כ-2.2%) אינם משויכים לאף גוש.":
            "<strong>Knesset 13 (1992)</strong> was added to the national results, the locality analysis and the map. The socioeconomic analysis excludes 1992 (CBS data does not reach back that far). The national result is based on the official totals (including soldiers' votes, which are not assigned to localities); ~67 small/historical 1992 localities with no match in the current data were dropped from the locality table. The 1992 blocs include three sub-threshold lists: Tehiya and the New Liberal Party (right) and the Progressive List for Peace (Arab); the remaining sub-threshold votes (the \"other\" category, ~2.2%) are not assigned to any bloc.",
        "נתונים סוציו-אקונומיים זמינים רק עבור <strong>201 רשויות מקומיות</strong> (לא כולל מועצות אזוריות; לקיבוצים ומושבים אין מדד רשותי; בעמוד הדמוגרפיה הם מכוסים דרך נתוני המפקד)":
            "Socioeconomic data is available only for <strong>201 municipalities</strong> (regional councils excluded; kibbutzim and moshavim have no authority-level index; the demographics page covers them via census data)",
        "המדד החברתי-כלכלי <strong>מתוקנן מחדש בכל שנתון</strong>; השוואות בין שנים נעשות באשכולות או ביחידות יחסיות בלבד, לא בערכי מדד גולמיים":
            "The socioeconomic index is <strong>re-standardized each vintage</strong>; cross-year comparisons use clusters or relative units only, never raw index values",
        "נתוני דת ו\"רוסים\" זמינים רק מ-<strong>2019</strong>": "Religion and \"Russians\" data available only from <strong>2019</strong>",
        "חלק מהמפלגות התמזגו או התפצלו בין בחירות, מה שמקשה על השוואה ישירה":
            "Some parties merged or split between elections, complicating direct comparison",
        "סיווג המפלגות לגושים הוא סובייקטיבי במידה מסוימת, במיוחד עבור מפלגות מרכז":
            "Assigning parties to blocs is somewhat subjective, especially for center parties",
        "אומדני נדידת הקולות מניחים <strong>דפוס מעבר אחיד בין יישובים</strong> (\"טבלה ארצית אחת\"): הנחה מפושטת שנבחנת במבחני פיצול (מגזר, השכלה) ובהצלבה מול סקרי INES, אך אינה ניתנת לאימות מלא":
            "The vote-transfer estimates assume a <strong>uniform transfer pattern across localities</strong> (\"one national table\"): a simplifying assumption tested via split tests (sector, education) and cross-checked against INES surveys, but not fully verifiable",
        "המתאמים ומדדי הקיטוב/המיון הם ברמת <strong>היישוב המצרפי</strong> ולא ברמת הבוחר הבודד; הסקה על התנהגות פרטים אינה אפשרית (הכשל האקולוגי)":
            "The correlations and polarization/sorting metrics are at the <strong>aggregate locality</strong> level, not the individual voter; inferring individual behavior is not possible (the ecological fallacy)",
        # ---------- national section ----------
        ">בחר בחירות להשוואה</div>": ">Choose elections to compare</div>",
        ">מ:</span>": ">From:</span>",
        ">עד:</span>": ">To:</span>",
        ">נושאים ראשיים</div>": ">Headline Metrics</div>",
        ">תת-קבוצות</div>": ">Sub-blocs</div>",
        " ימין (ליכוד, ימינה וכו׳)</div>": " Right (Likud, Yamina, etc.)</div>",
        " חרדים (ש״ס, יהדות התורה)</div>": " Haredim (Shas, UTJ)</div>",
        " מרכז (כחול לבן, יש עתיד וכו׳)</div>": " Center (Blue and White, Yesh Atid, etc.)</div>",
        " שמאל (עבודה, מרצ)</div>": " Left (Labor, Meretz)</div>",
        " ערבים (רע״מ, חד״ש, בל״ד)</div>": " Arabs (Ra'am, Hadash, Balad)</div>",
        ">מגמות היסטוריות - תת-קבוצות</div>": ">Historical trends: sub-blocs</div>",
        ">השוואה בין הבחירות הנבחרות</div>": ">Comparison of the selected elections</div>",
        ">מגמת הצבעה ארצית</div>": ">National turnout trend</div>",
        ">בניית קואליציה</div>": ">Coalition Builder</div>",
        ">בחר מפלגות</div>": ">Select parties</div>",
        ">אפס בחירה</button>": ">Reset selection</button>",
        # ---------- localities section ----------
        ">נקה בחירה</button>": ">Clear selection</button>",
        ">תוצאות לפי מפלגה - כנסת 17</div>": ">Results by party: Knesset 17</div>",
        "<th>מפלגה</th>": "<th>Party</th>",
        "<th>גוש</th>": "<th>Bloc</th>",
        "<th>אחוז</th>": "<th>Share</th>",
        ">מגמות היסטוריות - גושים</div>": ">Historical trends: blocs</div>",
        ">מגמה: פער מהארץ (מרכז-שמאל-ערבים)</div>": ">Trend: gap vs national (Center-Left-Arabs)</div>",
        ">מגמה: פער הצבעה מהארץ</div>": ">Trend: turnout gap vs national</div>",
        ">כשרים לפי בחירות</div>": ">Valid votes by election</div>",
        ">נתוני כנסת <span": ">Knesset <span",
        " ישובים)</span>": " localities)</span>",
        ">הכל (<span": ">All (<span",
        ">13 בחירות מלאות (<span": ">All 13 elections (<span",
        ">נתונים חלקיים (<span": ">Partial data (<span",
        "חיפוש ישוב...": "Search locality...",
        "<th>ישוב</th>": "<th>Locality</th>",
        "<th>בחירות</th>": "<th>Elections</th>",
        ">כשרים <span": ">Valid votes <span",
        ">שיעור ההצבעה <span": ">Turnout <span",
        ">ימין+חרדים <span": ">Right+Haredim <span",
        ">ימין <span": ">Right <span",
        ">חרדים <span": ">Haredim <span",
        ">מרכז-שמאל-ערבים <span": ">Center-Left-Arabs <span",
        ">מרכז <span": ">Center <span",
        ">ימין אופוזיציוני <span": ">Opposition Right <span",
        ">שמאל <span": ">Left <span",
        ">ערבים <span": ">Arabs <span",
        ">שינויים גדולים בין הבחירות הנבחרות (ישובים מעל 10,000 בוחרים)</div>":
            ">Largest changes between the selected elections (localities over 10,000 voters)</div>",
        ">עלייה במרכז-שמאל-ערבים</div>": ">Center-Left-Arabs gains</div>",
        ">עלייה בימין-חרדים</div>": ">Right-Haredim gains</div>",
        # ---------- socio section ----------
        ">בחירות:</div>": ">Election:</div>",
        " אשכול 1-3 (נמוך)</div>": " Cluster 1–3 (low)</div>",
        " אשכול 4-6 (בינוני)</div>": " Cluster 4–6 (medium)</div>",
        " אשכול 7-10 (גבוה)</div>": " Cluster 7–10 (high)</div>",
        " יישוב ערבי (60%+)</div>": " Arab locality (60%+)</div>",
        " יישוב דרוזי (55%+)</div>": " Druze locality (55%+)</div>",
        ">גודל העיגול לפי מספר המצביעים</div>": ">Bubble size = number of voters</div>",
        ">הכנסה חודשית לנפש מול % ימין-חרדים</div>": ">Monthly income per capita vs % Right-Haredim</div>",
        ">% אקדמאים מול % ימין-חרדים</div>": ">% academics vs % Right-Haredim</div>",
        ">ממוצע הצבעה לפי אשכול סוציו-אקונומי</div>": ">Mean vote by socioeconomic cluster</div>",
        ">ימי שהייה בחו״ל מול % ימין-חרדים</div>": ">Days abroad vs % Right-Haredim</div>",
        ">% משפחות עם 4 ילדים ומעלה מול % ימין-חרדים (עד 20% - ללא חרדים)</div>":
            ">% families with 4+ children vs % Right-Haredim (up to 20%, excl. Haredim)</div>",
        ">% משפחות עם 4 ילדים ומעלה מול % ימין-חרדים</div>": ">% families with 4+ children vs % Right-Haredim</div>",
        ">% \"רוסים\" (ללא סיווג דת) מול % ימין-חרדים</div>": ">% \"Russians\" (no religious classification) vs % Right-Haredim</div>",
        ">מטריצות מתאמים (משוקלל לפי מספר מצביעים)</div>": ">Correlation matrices (voter-weighted)</div>",
        ">כל הרשויות</div>": ">All authorities</div>",
        ">רוב יהודי (כולל ערים מעורבות)</div>": ">Jewish majority (incl. mixed cities)</div>",
        ">* לחץ על תא לפרטים</div>": ">* Click a cell for details</div>",
        ">מתאמים לאורך זמן - מרכז-שמאל</div>": ">Correlations over time: Center-Left</div>",
        ">מיון גיאוגרפי - הפער בין רשויות משכילות לפחות משכילות</div>":
            ">Geographic sorting: the gap between more- and less-educated authorities</div>",
        # regression model (HTML)
        ">🔬 מודל רגרסיה סוציו-אקונומי</h2>": ">🔬 Socioeconomic Regression Model</h2>",
        "רגרסיה לוגיסטית (logit) עם רגולריזציית <strong>Ridge (L2)</strong>, משוקללת לפי מספר בוחרים, המנבאת את שיעור ההצבעה לגוש ימין-חרדים (0%-100%).":
            "A logit regression with <strong>Ridge (L2)</strong> regularization, weighted by voter counts, predicting the Right-Haredi bloc's vote share (0%–100%).",
        "Ridge מטפל בקורלציה גבוהה בין משתנים (כגון הכנסה ↔ אחוז אקדמאים) ומונע מקדמים לא יציבים. פרמטר הענישה (λ) נבחר אוטומטית ב-Cross-Validation.":
            "Ridge handles high correlation between variables (e.g. income ↔ % academics) and prevents unstable coefficients. The penalty (λ) is chosen automatically via cross-validation.",
        "המודל רץ בנפרד על <strong>כל הרשויות</strong> ועל <strong>רשויות עם רוב יהודי</strong> (ללא רשויות ערביות/דרוזיות, אבל כולל ערים מעורבות כמו ירושלים, חיפה ולוד; משתנה % ערבים מאפשר למודל לתקן עבור ההשפעה של האוכלוסייה הערבית).":
            "The model runs separately on <strong>all authorities</strong> and on <strong>Jewish-majority authorities</strong> (excluding Arab/Druze authorities but including mixed cities like Jerusalem, Haifa and Lod; the % Arabs variable lets the model adjust for the Arab population's effect).",
        "💡 למה \"שנות לימוד ממוצע\" לא נכלל במודל?</strong><br>": "💡 Why isn't \"mean years of schooling\" in the model?</strong><br>",
        "המשתנה דחוס מדי ומטעה: הטווח הוא רק 12–15 שנים, כך שהפער בין חדרה (12.9) לרמת השרון (14.6) נראה קטן: 1.7 שנים בלבד.":
            "The variable is too compressed and misleading: the range is only 12–15 years, so the gap between Hadera (12.9) and Ramat HaSharon (14.6) looks small: just 1.7 years.",
        "אבל ב-% אקדמאים ההבדל הוא <strong>30 נקודות</strong> (29.7% מול 60.4%), ובהצבעה <strong>35 נקודות</strong>.":
            "But in % academics the difference is <strong>30 points</strong> (29.7% vs 60.4%), and in voting <strong>35 points</strong>.",
        "בנוסף, לימודי ישיבה נספרים כ\"שנות לימוד\" ע״י הלמ״ס, כך שמודיעין עילית (12.4, אבל 6% אקדמאים) נראית דומה לאילת (11.9, אבל 20% אקדמאים).":
            "Also, yeshiva study counts as \"years of schooling\" in CBS data, so Modi'in Illit (12.4, but 6% academics) looks similar to Eilat (11.9, but 20% academics).",
        "המשתנה <strong>% אקדמאים</strong> מבטא את ההבדלים בהשכלה בצורה הרבה יותר מדויקת.":
            "The <strong>% academics</strong> variable captures education differences far more accurately.",
        "📐 כיצד לקרוא את המקדמים?</strong><br>": "📐 How to read the coefficients?</strong><br>",
        "המקדמים מוצגים כ-<em>Beta מתוקנן</em> על סולם לוגיט: מספרים כמו 0.176 או -0.148 שקשה לפרש ישירות.":
            "Coefficients are shown as <em>standardized betas</em> on the logit scale: numbers like 0.176 or −0.148 that are hard to interpret directly.",
        "הטבלה הבאה מתרגמת אותם: מה קורה להצבעה כשמשתנה עולה ב-<strong>סטיית תקן אחת</strong> (1 SD), עבור רשות יהודית טיפוסית (~59% ימין-חרדים):":
            "The table translates them: what happens to the vote when a variable rises by <strong>one standard deviation</strong> (1 SD), for a typical Jewish authority (~59% Right-Haredim):",
        ">משתנה</th>": ">Variable</th>",
        ">1 SD בעולם האמיתי</th>": ">1 SD in the real world</th>",
        ">השפעה על הצבעה (±1 SD)</th>": ">Effect on the vote (±1 SD)</th>",
        ">דוגמה</th>": ">Example</th>",
        ">% משפחות 4+ ילדים</td>": ">% families 4+ children</td>",
        ">יחס תלות</td>": ">Dependency ratio</td>",
        ">% אקדמאים</td>": ">% academics</td>",
        ">גיל חציוני</td>": ">Median age</td>",
        ">ימי שהייה בחו״ל</td>": ">Days abroad</td>",
        ">רכבים ל-100 תושבים</td>": ">Vehicles per 100 residents</td>",
        ">% מתחת לשכר מינימום</td>": ">% below minimum wage</td>",
        ">הכנסה חודשית לנפש</td>": ">Monthly income per capita</td>",
        ">% הבטחת הכנסה</td>": ">% income support</td>",
        " נק׳ ימינה</td>": " pts rightward</td>",
        " נק׳ שמאלה</td>": " pts leftward</td>",
        " נק׳</td>": " pts</td>",
        " שנים</td>": " years</td>",
        " ימים</td>": " days</td>",
        ">רמה״ש 6% → בני ברק 46%</td>": ">Ramat HaSharon 6% → Bnei Brak 46%</td>",
        ">ילדים+קשישים ביחס לעובדים</td>": ">children+elderly relative to workers</td>",
        ">נתיבות 21% → רמה״ש 60%</td>": ">Netivot 21% → Ramat HaSharon 60%</td>",
        ">בית שמש 25 → רמה״ש 39</td>": ">Beit Shemesh 25 → Ramat HaSharon 39</td>",
        ">חדרה 2.2 → רמה״ש 5.9</td>": ">Hadera 2.2 → Ramat HaSharon 5.9</td>",
        ">אשדוד 41 → רמה״ש 71</td>": ">Ashdod 41 → Ramat HaSharon 71</td>",
        ">רמה״ש 32% → אשדוד 43%</td>": ">Ramat HaSharon 32% → Ashdod 43%</td>",
        ">נתיבות ₪4.5K → רמה״ש ₪12K</td>": ">Netivot ₪4.5K → Ramat HaSharon ₪12K</td>",
        ">רמה״ש 1.3% → אשדוד 9.4%</td>": ">Ramat HaSharon 1.3% → Ashdod 9.4%</td>",
        "<strong>חישוב:</strong> sigmoid( logit(59%) + Beta × SD(logit_y) ) − 59%. למשל עבור % משפחות 4+ ילדים: sigmoid(0.354 + 0.176×1.52) − 58.8% = 65.1% − 58.8% = <strong>+6.3 נק׳</strong>.<br>":
            "<strong>Computation:</strong> sigmoid( logit(59%) + Beta × SD(logit_y) ) − 59%. E.g. for % families 4+ children: sigmoid(0.354 + 0.176×1.52) − 58.8% = 65.1% − 58.8% = <strong>+6.3 pts</strong>.<br>",
        "<strong>דוגמה:</strong> המעבר מפרופיל של חדרה לפרופיל של רמת השרון כולל ~+1.8 SD באקדמאים, ~+1.8 SD בהכנסה, ~+1.2 SD בגיל ועוד, שמצטברים ל-~35 נקודות הפרש בהצבעה, קרוב להפרש בפועל (59% מול 25%).":
            "<strong>Example:</strong> moving from Hadera's profile to Ramat HaSharon's involves ~+1.8 SD in academics, ~+1.8 SD in income, ~+1.2 SD in age and more, accumulating to ~35 points of vote difference, close to the actual gap (59% vs 25%).",
        "ההשפעות חושבו עבור רשות חציונית (~59% ימין-חרדים); בקצוות (ליד 0% או 100%) ההשפעה קטנה יותר בגלל טרנספורמציית הלוגיט.":
            "Effects were computed for a median authority (~59% Right-Haredim); near the extremes (0% or 100%) the effect is smaller due to the logit transformation.",
        ">📊 חשיבות משתנים</button>": ">📊 Feature importance</button>",
        ">🎯 חריגים</button>": ">🎯 Outliers</button>",
        ">🔮 מנבא</button>": ">🔮 Predictor</button>",
        ">📈 מגמות לאורך זמן</button>": ">📈 Trends over time</button>",
        ">כל הרשויות (201)</h3>": ">All authorities (201)</h3>",
        ">רשויות עם רוב יהודי (כולל ערים מעורבות)</h3>": ">Jewish-majority authorities (incl. mixed cities)</h3>",
        ">צפוי מול בפועל: % ימין-חרדים (כל הרשויות)</div>": ">Predicted vs actual: % Right-Haredim (all authorities)</div>",
        ">צפוי מול בפועל: % ימין-חרדים (רוב יהודי)</div>": ">Predicted vs actual: % Right-Haredim (Jewish majority)</div>",
        ">🔵 מצביעים ימין-חרדים יותר מהצפוי (בהתחשב בנתונים הסוציו-אקונומיים)</h3>":
            ">🔵 Vote more Right-Haredi than predicted (given their socioeconomics)</h3>",
        ">🔴 מצביעים ימין-חרדים פחות מהצפוי</h3>": ">🔴 Vote less Right-Haredi than predicted</h3>",
        ">שאריות (Residuals) לפי רשות</div>": ">Residuals by authority</div>",
        ">הזן ערכים סוציו-אקונומיים ודמוגרפיים</h3>": ">Enter socioeconomic and demographic values</h3>",
        ">תחזית: % הצבעה ימין-חרדים</div>": ">Prediction: % Right-Haredi vote</div>",
        "כיצד כוח ההסבר (R²) של כל משתנה משתנה לאורך הבחירות: עד כמה כל גורם מנבא את ההצבעה בכל מערכת בחירות?":
            "How each variable's explanatory power (R²) changes across elections: how well does each factor predict the vote in each election?",
        ">R² של כל משתנה בנפרד לאורך בחירות: כל הרשויות</div>": ">Per-variable R² across elections: all authorities</div>",
        ">R² של כל משתנה בנפרד לאורך בחירות: רוב יהודי</div>": ">Per-variable R² across elections: Jewish majority</div>",
        ">R² של המודל המלא לאורך הבחירות</div>": ">Full-model R² across elections</div>",
        # ---------- polarization section (HTML) ----------
        ">מיון גאוגרפי: ישראל נפרדת לשני מחנות (1992–2022)</div>":
            ">Geographic Sorting: Israel Splits into Two Camps (1992–2022)</div>",
        "פאנל מאוזן של <strong>896 ישובים</strong> הנוכחים בכל 13 מערכות הבחירות, <strong>משוקלל לפי מספר בעלי זכות הבחירה</strong>.":
            "A balanced panel of <strong>896 localities</strong> present in all 13 elections, <strong>weighted by registered voters</strong>.",
        "הישובים לא רק החליפו הצבעה, הם התרחקו זה מזה: הפיזור וההפרדה הגאוגרפית בין הגושים גדלו בעקביות לאורך 30 שנה (כל המגמות מובהקות ברווח סמך 95%).":
            "Localities didn't just change their vote, they drifted apart: dispersion and geographic separation between the blocs grew consistently over 30 years (all trends significant at 95% CI).",
        "במקביל, התנודות הקצרות-טווח דווקא הסתנכרנו יותר (נציונליזציה): <strong>הרמות מתפצלות, אבל השינויים מתלאמים</strong>.":
            "Meanwhile, short-term swings actually synchronized (nationalization): <strong>levels diverge, but changes nationalize</strong>.",
        ">התפלגות ההצבעה לימין-חרדים בין הישובים: נפתחת כמניפה (עשירון 10–90 + חציון)</div>":
            ">Distribution of the Right-Haredi vote across localities: opening like a fan (10th–90th percentile + median)</div>",
        ">1992 מול 2022: המיון (משקל הבוחרים בכל טווח % ימין-חרדים)</div>":
            ">1992 vs 2022: the sorting (voter weight per Right-Haredi % bin)</div>",
        ">הפרדה גאוגרפית בין הגושים (מדד אי-דמיון) ↑ · רצועה = 95% CI</div>":
            ">Geographic separation between the blocs (dissimilarity index) ↑ · band = 95% CI</div>",
        ">נציונליזציה: פיזור התנודות המקומיות ↓ (נמוך = מסונכרן) · רצועה = 95% CI</div>":
            ">Nationalization: dispersion of local swings ↓ (low = synchronized) · band = 95% CI</div>",
        ">ערים במגמות מנוגדות: % ימין-חרדים לאורך זמן (אדום = התרחקו שמאלה, כחול = התרחקו ימינה)</div>":
            ">Cities on opposite paths: Right-Haredi % over time (red = moved left, blue = moved right)</div>",
        ">מה מסביר את הכיוון? השכלה, חילוניות וחרדיות</div>":
            ">What explains the direction? Education, secularism and Harediness</div>",
        "<strong>שיטה:</strong> פאנל מאוזן של 896 ישובים (כנסת 13–25, 1992–2022); כל המדדים משוקללים לפי בעלי זכות הבחירה, כך שערים גדולות שוקלות יותר מקיבוצים.":
            "<strong>Method:</strong> a balanced panel of 896 localities (Knesset 13–25, 1992–2022); all metrics weighted by registered voters, so large cities weigh more than kibbutzim.",
        "רווחי סמך 95% מ-2,000 דגימות bootstrap של הישובים (כל שיפועי המגמה מובהקים). \"מיון\" נמדד כפיזור/הפרדה של ההצבעה <strong>בין</strong> הישובים (לא בתוכם).":
            "95% confidence intervals from 2,000 bootstrap resamples of the localities (all trend slopes significant). \"Sorting\" is measured as dispersion/separation of the vote <strong>between</strong> localities (not within them).",
        "יחידת הניתוח היא היישוב, ולא הבוחר הבודד; יש להיזהר מכשל אקולוגי.":
            "The unit of analysis is the locality, not the individual voter; beware the ecological fallacy.",
        # bloc names as plain HTML text (bloc definition cards + party-table bloc cells)
        ">ימין</div>": ">Right</div>",
        ">חרדים</div>": ">Haredim</div>",
        ">מרכז</div>": ">Center</div>",
        ">שמאל</div>": ">Left</div>",
        ">ערבים</div>": ">Arabs</div>",
        ">ימין</td>": ">Right</td>",
        ">מרכז</td>": ">Center</td>",
        ">שמאל</td>": ">Left</td>",
        ">ערבים</td>": ">Arabs</td>",
        # coalition select options: the 2019 twins
        "(2019א)</option>": "(Apr 2019)</option>",
        "(2019ב)</option>": "(Sep 2019)</option>",
        # map iframe
        "title=\"מפת בחירות אינטראקטיבית\"": "title=\"Interactive elections map\"",
        "title=\"מעקב סקרים לקראת בחירות 2026\"": "title=\"2026 election polling tracker\"",
        # ---------- JS ----------
        "'<div class=\"loading\">שגיאה בטעינת הנתונים</div>'": "'<div class=\"loading\">Error loading data</div>'",
        "`נתונים דמוגרפיים: קובץ רשויות ${demoYear}`": "`Demographic data: ${demoYear} authorities file`",
        # polarization JS
        "'פער העשירון הימני–שמאלי (נק׳ אחוז)'": "'Right-most vs left-most decile gap (pp)'",
        "'פיזור ההצבעה לימין-חרדים בין הישובים'": "'Dispersion of the Right-Haredi vote across localities'",
        "'מדד ההפרדה הגאוגרפית בין הגושים'": "'Geographic segregation index between the blocs'",
        "'פיזור התנודות המקומיות (נציונליזציה)'": "'Dispersion of local swings (nationalization)'",
        "label: 'חציון'": "label: 'Median'",
        "label: 'מדד הפרדה'": "label: 'Segregation index'",
        "label: 'תנודות'": "label: 'Swings'",
        "'התרחקו שמאלה ↓ (ירידה בימין-חרדים)'": "'Moved left ↓ (Right-Haredim decline)'",
        "'התרחקו ימינה ↑ (עלייה בימין-חרדים)'": "'Moved right ↑ (Right-Haredim rise)'",
        "בערים היהודיות (${MC.corr.n} ערים מעל 30 אלף בוחרים), המהלך <b style=\"color:#e74c3c\">שמאלה חזק ככל שההשכלה גבוהה יותר</b> (r=${MC.corr.acad} עם % אקדמאים), <b>הפוריות נמוכה</b> (r=+${MC.corr.fert} עם % משפחות 4+ ילדים) <b>וההצבעה החרדית נמוכה</b> (r=+${MC.corr.har}). הערים החרדיות (ירושלים, בית שמש, בני ברק) נעו ימינה, וזה נראה ישירות בהצבעה החרדית (ש\"ס+יהדות התורה). (ערי העלייה מברה\"מ/פריפריה, כמו באר שבע, נעו ימינה במנגנון שלישי (קפיצת 1996) ואינן בין הדוגמאות הנקיות כאן.)":
            "In Jewish cities (${MC.corr.n} cities over 30k voters), the <b style=\"color:#e74c3c\">leftward move is stronger the higher the education</b> (r=${MC.corr.acad} with % academics), <b>the lower the fertility</b> (r=+${MC.corr.fert} with % families 4+ children) <b>and the lower the Haredi vote</b> (r=+${MC.corr.har}). The Haredi cities (Jerusalem, Beit Shemesh, Bnei Brak) moved right, and this shows directly in the Haredi vote (Shas+UTJ). (FSU-immigration/periphery cities like Be'er Sheva moved right via a third mechanism (the 1996 jump) and are not among the clean examples here.)",
        "% אקדמאים, מהלך ": "% academics, move ",
        "text: '% אקדמאים (השכלה)'": "text: '% academics (education)'",
        "haredi: 'חרדי'": "haredi: 'Haredi'",
        "'חילוני-משכיל'": "'Secular-educated'",
        "'פריפריה'": "'Periphery'",
        ">עיר</th>": ">City</th>",
        ">% אקדמאים</th>": ">% academics</th>",
        ">% 4+ ילדים</th>": ">% 4+ children</th>",
        ">הצבעה חרדית</th>": ">Haredi vote</th>",
        ">המהלך</th>": ">Move</th>",
        ">סוג</th>": ">Type</th>",
        # national/localities JS
        "כשרים - כנסת ": "Valid votes · Knesset ",
        "ימין-חרדים - כנסת ": "Right-Haredim · Knesset ",
        "מרכז-שמאל-ערבים - כנסת ": "Center-Left-Arabs · Knesset ",
        "label: 'ימין אופוזיציוני'": "label: 'Opposition Right'",
        "'2019א'": "'Apr 2019'",
        "'2019ב'": "'Sep 2019'",
        "label: 'שיעור הצבעה ארצי'": "label: 'National turnout'",
        "'כנסת ' + k + ' ('": "'Knesset ' + k + ' ('",
        "`שיעור הצבעה: ": "`Turnout: ",
        "'עלייה' : (totalTrend < -0.5 ? 'ירידה' : 'יציב')": "'rise' : (totalTrend < -0.5 ? 'decline' : 'stable')",
        "label: 'פער הצבעה מהארץ (%)'": "label: 'Turnout gap vs national (%)'",
        "`יישוב: ": "`Locality: ",
        "`ארץ: ": "`National: ",
        "`פער: ": "`Gap: ",
        "`מגמה כוללת: ": "`Overall trend: ",
        "text: 'פער שיעור הצבעה מהארץ'": "text: 'Turnout gap vs national'",
        "label: 'כשרים'": "label: 'Valid votes'",
        "`כשרים: ": "`Valid votes: ",
        "label: 'פער מהארץ (%)'": "label: 'Gap vs national (%)'",
        "text: 'פער מהארץ (מרכז-שמאל-ערבים)'": "text: 'Gap vs national (Center-Left-Arabs)'",
        # party table / subgroup cards JS
        "titleText = 'מפלגות';": "titleText = 'Parties';",
        "titleText = `מפלגות (כנסת ": "titleText = `Parties (Knesset ",
        " ו-${laterK})`": " & ${laterK})`",
        "`תוצאות לפי מפלגה - כנסת ${earlierK} ו-${laterK}`": "`Results by party: Knesset ${earlierK} & ${laterK}`",
        "`תוצאות לפי מפלגה - ${partiesData.election_name}`": "`Results by party: ${partiesData.election_name}`",
        "<th>כנסת ${earlierK}</th>": "<th>Knesset ${earlierK}</th>",
        "<th>כנסת ${laterK}</th>": "<th>Knesset ${laterK}</th>",
        "<th>שינוי</th>": "<th>Change</th>",
        "<th>שינוי יחסי</th>": "<th>Relative change</th>",
        ">מפלגות כנסת ${earlierK} בלבד</td>": ">Knesset ${earlierK}-only parties</td>",
        ">מפלגות כנסת ${laterK} בלבד</td>": ">Knesset ${laterK}-only parties</td>",
        ">השוואת מפלגות שהתמזגו</td>": ">Merged-party comparison</td>",
        ">השוואת מפלגות שהתפצלו</td>": ">Split-party comparison</td>",
        ">השוואת מפלגות</td>": ">Party comparison</td>",
        "<td>תקווה חדשה + כחול לבן ← המחנה הממלכתי</td>": "<td>New Hope + Blue and White → National Unity</td>",
        "<td>הציונות הדתית + ימינה ← הציונות הדתית + הבית היהודי</td>": "<td>Religious Zionism + Yamina → Religious Zionism + Jewish Home</td>",
        "<td>העבודה-גשר-מרצ ← העבודה + מרצ</td>": "<td>Labor-Gesher-Meretz → Labor + Meretz</td>",
        "<td>כחול לבן ← כחול לבן + יש עתיד</td>": "<td>Blue and White → Blue and White + Yesh Atid</td>",
        "<td>הרשימה המשותפת ← רע\"מ + הרשימה המשותפת</td>": "<td>Joint List → Ra'am + Joint List</td>",
        "<td>הרשימה המשותפת ← רע\"מ + חד\"ש-תע\"ל + בל\"ד</td>": "<td>Joint List → Ra'am + Hadash-Ta'al + Balad</td>",
        "<td>כחול לבן ← יש עתיד + המחנה הממלכתי</td>": "<td>Blue and White → Yesh Atid + National Unity</td>",
        "<td>העבודה-גשר + מרצ ← העבודה-גשר-מרצ</td>": "<td>Labor-Gesher + Meretz → Labor-Gesher-Meretz</td>",
        "<td>כחול לבן ← יש עתיד + כחול לבן</td>": "<td>Blue and White → Yesh Atid + Blue and White</td>",
        "<td>הרשימה המשותפת ← הרשימה המשותפת + רע\"מ</td>": "<td>Joint List → Joint List + Ra'am</td>",
        "<td>הבית היהודי + האיחוד הלאומי ← הבית היהודי</td>": "<td>Jewish Home + National Union → Jewish Home</td>",
        "<td>הליכוד ← הליכוד-ישראל ביתנו</td>": "<td>Likud → Likud-Yisrael Beiteinu</td>",
        "<td>האיחוד הלאומי + הבית היהודי ← הציונות הדתית + הבית היהודי</td>": "<td>National Union + Jewish Home → Religious Zionism + Jewish Home</td>",
        "<td>העבודה + התנועה ← המחנה הציוני</td>": "<td>Labor + Hatnua → Zionist Union</td>",
        "<td>חד\"ש + רע\"מ-תע\"ל + בל\"ד ← הרשימה המשותפת</td>": "<td>Hadash + Ra'am-Ta'al + Balad → Joint List</td>",
        "<td>הבית היהודי + עוצמה לישראל ← הבית היהודי + עוצמה יהודית</td>": "<td>Jewish Home + Otzma LeYisrael → Jewish Home + Otzma Yehudit</td>",
        "<td>חד\"ש-תע\"ל + רע\"מ-בל\"ד ← הרשימה המשותפת</td>": "<td>Hadash-Ta'al + Ra'am-Balad → Joint List</td>",
        "<td>העבודה + גשר ← העבודה-גשר</td>": "<td>Labor + Gesher → Labor-Gesher</td>",
        "<td>העבודה + מרצ + גשר ← העבודה-גשר-מרצ</td>": "<td>Labor + Meretz + Gesher → Labor-Gesher-Meretz</td>",
        "<td>כולנו (התמזגה לליכוד)</td>": "<td>Kulanu (merged into Likud)</td>",
        "<td>חד\"ש-תע\"ל + רע\"מ-בל\"ד ← חד\"ש-תע\"ל + רע\"מ + בל\"ד</td>": "<td>Hadash-Ta'al + Ra'am-Balad → Hadash-Ta'al + Ra'am + Balad</td>",
        "כנסת ${fromK}:": "Knesset ${fromK}:",
        "כנסת ${toK}:": "Knesset ${toK}:",
        "כנסת ${earlierK}:": "Knesset ${earlierK}:",
        "כנסת ${laterK}:": "Knesset ${laterK}:",
        "כנסת ${activeK}:": "Knesset ${activeK}:",
        "`כנסת ${k}`": "`Knesset ${k}`",
        "|| `כנסת ${k}`": "|| `Knesset ${k}`",
        # coalition JS
        ">אין נתונים</div>": ">No data</div>",
        "`קואליציה! (": "`Coalition! (",
        " מנדטים)`": " seats)`",
        "`חסרים ${61 - total} מנדטים`": "`${61 - total} seats short`",
        # socio scatters JS
        ": הכנסה ₪": ": income ₪",
        ", ימין-חרדים ": ", Right-Haredim ",
        "text: 'הכנסה חודשית לנפש (₪)'": "text: 'Monthly income per capita (₪)'",
        ": אקדמאים ": ": academics ",
        "text: '% בעלי תואר אקדמי (גילאי 27-54)'": "text: '% with academic degree (ages 27–54)'",
        "'אשכול 1', 'אשכול 2', 'אשכול 3', 'אשכול 4', 'אשכול 5', 'אשכול 6', 'אשכול 7', 'אשכול 8', 'אשכול 9', 'אשכול 10'":
            "'Cluster 1', 'Cluster 2', 'Cluster 3', 'Cluster 4', 'Cluster 5', 'Cluster 6', 'Cluster 7', 'Cluster 8', 'Cluster 9', 'Cluster 10'",
        ": ימי חו\"ל ": ": days abroad ",
        "text: 'ממוצע ימי שהייה בחו״ל'": "text: 'Mean days abroad'",
        ": משפחות 4+ ילדים ": ": families 4+ children ",
        "text: '% משפחות עם 4 ילדים ומעלה'": "text: '% families with 4+ children'",
        ": \"רוסים\" ": ": \"Russians\" ",
        "text: '% ללא סיווג דת (\"רוסים\")'": "text: '% no religious classification (\"Russians\")'",
        "'דרוזי'": "'Druze'",
        "'ערבי'": "'Arab'",
        # correlation matrix JS
        "label: 'הכנסה לנפש'": "label: 'Income per capita'",
        "label: '% אקדמאים'": "label: '% academics'",
        "label: 'אשכול'": "label: 'Cluster'",
        "label: '% 4+ ילדים'": "label: '% 4+ children'",
        "label: '% \"רוסים\"'": "label: '% \"Russians\"'",
        "label: '% יהודים'": "label: '% Jews'",
        "label: '% ערבים'": "label: '% Arabs'",
        "label: '% ימין-חרדים'": "label: '% Right-Haredim'",
        "label: '% חרדים'": "label: '% Haredim'",
        "label: '% מרכז-שמאל'": "label: '% Center-Left'",
        "'מתאם חיובי חזק מאוד'": "'Very strong positive correlation'",
        "'מתאם חיובי חזק'": "'Strong positive correlation'",
        "'מתאם חיובי בינוני'": "'Moderate positive correlation'",
        "'מתאם חיובי חלש'": "'Weak positive correlation'",
        "'אין מתאם משמעותי'": "'No meaningful correlation'",
        "'מתאם שלילי חלש'": "'Weak negative correlation'",
        "'מתאם שלילי בינוני'": "'Moderate negative correlation'",
        "'מתאם שלילי חזק מאוד'": "'Very strong negative correlation'",
        "'מתאם שלילי חזק'": "'Strong negative correlation'",
        # geo sorting JS
        "'כנסת ' + k": "'Knesset ' + k",
        "'כנסת ' + e": "'Knesset ' + e",
        "`משכילים (>0.5 סטיות תקן, ${highLabel})`": "`Educated (>0.5 SD, ${highLabel})`",
        "`פחות משכילים (≤0.5 סטיות תקן, ${lowLabel})`": "`Less educated (≤0.5 SD, ${lowLabel})`",
        "label: 'הפער'": "label: 'The gap'",
        "text: '% מרכז-שמאל-ערבים'": "text: '% Center-Left-Arabs'",
        "text: 'הפער'": "text: 'The gap'",
        # regression model JS
        # NOTE: the labels below that are names_en keys (הכנסה חודשית לנפש, גיל חציוני,
        # יחס תלות) are translated by the literal pass first — key on `short:` only.
        "short: 'הכנסה'": "short: 'Income'",
        "short: 'אקדמאים'": "short: 'Academics'",
        "label: '% משפחות 4+ ילדים', short: '4+ ילדים'": "label: '% families 4+ children', short: '4+ children'",
        "short: 'גיל חציוני'": "short: 'Median age'",
        "short: 'יחס תלות'": "short: 'Dependency'",
        "label: '% מתחת לשכר מינימום', short: 'מתחת למינימום'": "label: '% below minimum wage', short: 'Below min. wage'",
        "label: 'ימי שהייה בחו״ל', short: 'ימים בחו״ל'": "label: 'Days abroad', short: 'Days abroad'",
        "label: 'רכבים ל-100 תושבים', short: 'רכבים/100'": "label: 'Vehicles per 100 residents', short: 'Vehicles/100'",
        "label: '% נתמכי הבטחת הכנסה', short: 'הבטחת הכנסה'": "label: '% on income support', short: 'Income support'",
        "short: 'ערבים'": "short: 'Arabs'",
        "label: '% דרוזים', short: 'דרוזים'": "label: '% Druze', short: 'Druze'",
        "label: '% \"רוסים\" (ללא סיווג דת)', short: 'רוסים'": "label: '% \"Russians\" (no religious classification)', short: 'Russians'",
        "label: 'מעבר לקו הירוק', short: 'קו ירוק'": "label: 'Beyond the Green Line', short: 'Green Line'",
        ">R² · כל הרשויות (": ">R² · all authorities (",
        " משתנים · λ=": " variables · λ=",
        ">R² מתואם · כל הרשויות</div>": ">Adjusted R² · all authorities</div>",
        ">Ridge + logit + משוקלל</div>": ">Ridge + logit + weighted</div>",
        ">R² · רוב יהודי (": ">R² · Jewish majority (",
        ">R² מתואם · רוב יהודי</div>": ">Adjusted R² · Jewish majority</div>",
        ">ללא רשויות ערביות/דרוזיות</div>": ">Excl. Arab/Druze authorities</div>",
        "label: 'קו מושלם'": "label: 'Perfect fit'",
        "`בפועל: ${p.y.toFixed(1)}% | צפוי: ${p.x.toFixed(1)}%`": "`Actual: ${p.y.toFixed(1)}% | predicted: ${p.x.toFixed(1)}%`",
        "`שארית: ": "`Residual: ",
        "text: '% ימין-חרדים: תחזית (Ridge logit)'": "text: '% Right-Haredim: predicted (Ridge logit)'",
        "text: 'בפועל'": "text: 'Actual'",
        "<th>רשות</th>": "<th>Authority</th>",
        "<th>% בפועל</th>": "<th>% actual</th>",
        "<th>% צפוי</th>": "<th>% predicted</th>",
        "<th>הפרש</th>": "<th>Difference</th>",
        "<th>אשכול</th>": "<th>Cluster</th>",
        "<th>בוחרים</th>": "<th>Voters</th>",
        "text: 'שארית'": "text: 'Residual'",
        "'1 (כן)' : '0 (לא)'": "'1 (yes)' : '0 (no)'",
        "'1 (כן)'": "'1 (yes)'",
        "'0 (לא)'": "'0 (no)'",
        "`הפרופיל הקרוב ביותר: ${closestName} (בפועל: ": "`Closest real profile: ${closestName} (actual: ",
        "'כל הרשויות (' + ": "'All authorities (' + ",
        "'רוב יהודי (' + ": "'Jewish majority (' + ",
        "text: 'R² של המודל המלא (logit, משוקלל)'": "text: 'Full-model R² (logit, weighted)'",
    },
}

FIXES = {
    "index": [
        # language toggle: EN page links back to the Hebrew page
        ("<a class=\"lang\" lang=\"en\" href=\"index_en.html\">EN</a>",
         "<a class=\"lang\" lang=\"he\" dir=\"rtl\" href=\"index.html\">&#1506;&#1489;&#1512;&#1497;&#1514;</a>"),
        # landing.js language switch + placeholder direction
        ("    en: false,", "    en: true,"),
        ("<input id=\"locSearch\" type=\"text\" autocomplete=\"off\" placeholder=",
         "<input id=\"locSearch\" type=\"text\" autocomplete=\"off\" dir=\"auto\" placeholder="),
    ],
    "findings": [
        # language toggle: EN page links back to the Hebrew page (label as entities so the leftover scan stays clean)
        ("<a class=\"lang\" lang=\"en\" href=\"findings_en.html\">EN</a>",
         "<a class=\"lang\" lang=\"he\" dir=\"rtl\" href=\"findings.html\">&#1506;&#1489;&#1512;&#1497;&#1514;</a>"),
        # numbers block + table alignment flip for LTR
        (".card .n{font-size:2.2rem;font-weight:800;direction:ltr;text-align:right;",
         ".card .n{font-size:2.2rem;font-weight:800;direction:ltr;text-align:left;"),
        ("<th style=\"text-align:right;padding:.45rem\">",
         "<th style=\"text-align:left;padding:.45rem\">"),
        ("<td style=\"padding:.45rem;text-align:right;font-weight:600\">",
         "<td style=\"padding:.45rem;text-align:left;font-weight:600\">"),
    ],
    "transfers": [
        # language toggle: EN page links back to the Hebrew page
        ("<a class=\"lang\" lang=\"en\" href=\"transfers_en.html\">EN</a>",
         "<a class=\"lang\" lang=\"he\" dir=\"rtl\" href=\"transfers.html\">&#1506;&#1489;&#1512;&#1497;&#1514;</a>"),
        # guided story-mode button; step content lives in data/transfers_stories.json (he/en, runtime)
        ("<button class=\"pill\" id=\"storyBtn\" style=\"display:none\" title=\"סיפור מודרך: הזרימות הגדולות של שלושים שנה, צעד אחר צעד\">🎬 סיפור מודרך</button>",
         "<button class=\"pill\" id=\"storyBtn\" style=\"display:none\" title=\"A guided story: thirty years of big flows, step by step\">🎬 Guided story</button>"),
        # Sankey mirrored for LTR: source column moves to the LEFT, destination to the RIGHT
        ("const xSrc = W - 190, xDst = 174;          // RTL: source right, destination left",
         "const xSrc = 174, xDst = W - 190;          // LTR: source left, destination right"),
        ("const x1 = xSrc, x2 = xDst + nodeW, cx = (x1 + x2) / 2;",
         "const x1 = xSrc + nodeW, x2 = xDst, cx = (x1 + x2) / 2;"),
        # source labels: outside-left of the node (were outside-right)
        ("<text x=\"${xSrc + nodeW + 8}\" y=\"${srcPos[i].y0 + srcPos[i].h / 2 + 4}\" fill=\"#fff\" font-size=\"13\" text-anchor=\"start\">",
         "<text x=\"${xSrc - 8}\" y=\"${srcPos[i].y0 + srcPos[i].h / 2 + 4}\" fill=\"#fff\" font-size=\"13\" text-anchor=\"end\">"),
        ("<text x=\"${xSrc + nodeW + 8}\" y=\"${srcPos[i].y0 + srcPos[i].h / 2 + 19}\" fill=\"#8ba3c7\" font-size=\"10.5\" text-anchor=\"start\">",
         "<text x=\"${xSrc - 8}\" y=\"${srcPos[i].y0 + srcPos[i].h / 2 + 19}\" fill=\"#8ba3c7\" font-size=\"10.5\" text-anchor=\"end\">"),
        # destination labels: outside-right of the node (were outside-left)
        ("<text x=\"${xDst - 8}\" y=\"${dstPos[j].y0 + dstPos[j].h / 2 + 4}\" fill=\"#fff\" font-size=\"13\" text-anchor=\"end\">",
         "<text x=\"${xDst + nodeW + 8}\" y=\"${dstPos[j].y0 + dstPos[j].h / 2 + 4}\" fill=\"#fff\" font-size=\"13\" text-anchor=\"start\">"),
        ("<text x=\"${xDst - 8}\" y=\"${dstPos[j].y0 + dstPos[j].h / 2 + 19}\" fill=\"#8ba3c7\" font-size=\"10.5\" text-anchor=\"end\">",
         "<text x=\"${xDst + nodeW + 8}\" y=\"${dstPos[j].y0 + dstPos[j].h / 2 + 19}\" fill=\"#8ba3c7\" font-size=\"10.5\" text-anchor=\"start\">"),
        # column headers follow their columns
        ("<text x=\"${xSrc + nodeW}\" y=\"${padY - 2}\" fill=\"#8ba3c7\" font-size=\"12\" text-anchor=\"end\">${t.from.year} (מקור)</text>",
         "<text x=\"${xSrc}\" y=\"${padY - 2}\" fill=\"#8ba3c7\" font-size=\"12\" text-anchor=\"start\">${t.from.year} (מקור)</text>"),
        ("<text x=\"${xDst}\" y=\"${padY - 2}\" fill=\"#8ba3c7\" font-size=\"12\" text-anchor=\"start\">${t.to.year} (יעד)</text>",
         "<text x=\"${xDst + nodeW}\" y=\"${padY - 2}\" fill=\"#8ba3c7\" font-size=\"12\" text-anchor=\"end\">${t.to.year} (יעד)</text>"),
        # tooltip arrows read left-to-right
        ("<b>${cur.fromLab[i]} ← ${cur.toLab[j]}</b><br>לפי הסקר",
         "<b>${cur.fromLab[i]} → ${cur.toLab[j]}</b><br>לפי הסקר"),
        ("<b>${cur.fromLab[i]} ← ${cur.toLab[j]}</b><br>${fmt(v)}",
         "<b>${cur.fromLab[i]} → ${cur.toLab[j]}</b><br>${fmt(v)}"),
    ],
    "party_analysis": [
        # language toggle: EN page links back to the Hebrew page
        ("<a class=\"lang\" lang=\"en\" href=\"party_analysis_en.html\">EN</a>",
         "<a class=\"lang\" lang=\"he\" dir=\"rtl\" href=\"party_analysis.html\">&#1506;&#1489;&#1512;&#1497;&#1514;</a>"),
        # LTR alignment
        ("th,td{text-align:right;padding:.4rem .5rem;", "th,td{text-align:left;padding:.4rem .5rem;"),
        (".card .n{font-size:1.9rem;font-weight:800;direction:ltr;text-align:right;",
         ".card .n{font-size:1.9rem;font-weight:800;direction:ltr;text-align:left;"),
        # Chart.js RTL tooltip mode off
        ("tooltip:{rtl:true,callbacks:{", "tooltip:{callbacks:{"),
        # chronological chains read left-to-right
        (".join(' ← ')", ".join(' → ')"),
        ("{n:`${first.psns} ← ${last.psns}`", "{n:`${first.psns} → ${last.psns}`"),
        # standardized-profile diverging bar: positive extends right in LTR
        ("const side=d>=0?`right:50%`:`left:50%`;", "const side=d>=0?`left:50%`:`right:50%`;"),
    ],
    "demographics": [
        # language toggle: EN page links back to the Hebrew page
        ("<a class=\"lang\" lang=\"en\" href=\"demographics_en.html\">EN</a>",
         "<a class=\"lang\" lang=\"he\" dir=\"rtl\" href=\"demographics.html\">&#1506;&#1489;&#1512;&#1497;&#1514;</a>"),
        ("locale:'he'", "locale:'en'"),
        ("tooltip:{ rtl:true,", "tooltip:{"),
        ("legend:{ rtl:true,", "legend:{"),
    ],
    "election_map": [
        # language toggle: EN page links back to the Hebrew page
        ("<a class=\"lang\" lang=\"en\" href=\"election_map_en.html\">English</a>",
         "<a class=\"lang\" lang=\"he\" dir=\"rtl\" href=\"election_map.html\">&#1506;&#1489;&#1512;&#1497;&#1514;</a>"),
        # LTR flips: topbar push, panel party rows, legend swatch counts, inputs
        (".mode-select{display:flex;flex-wrap:wrap;gap:4px;margin-right:auto}",
         ".mode-select{display:flex;flex-wrap:wrap;gap:4px;margin-left:auto}"),
        ("scrollbar-width:none;width:100%;margin-right:0;",
         "scrollbar-width:none;width:100%;margin-left:0;"),
        (".party-name{font-size:0.78rem;color:var(--text2);width:100px;text-align:right;",
         ".party-name{font-size:0.78rem;color:var(--text2);width:100px;text-align:left;"),
        (".party-pct{font-size:0.75rem;color:var(--text);width:42px;text-align:left;",
         ".party-pct{font-size:0.75rem;color:var(--text);width:42px;text-align:right;"),
        (".lg-sw b{margin-right:auto;", ".lg-sw b{margin-left:auto;"),
        ("font-size:0.9rem;outline:none;direction:rtl}", "font-size:0.9rem;outline:none;direction:ltr}"),
        ("cursor:pointer;max-width:320px;direction:rtl}", "cursor:pointer;max-width:320px;direction:ltr}"),
        # Knesset pill labels: כ25 -> K25 (also the comparison in selectElection)
        ("`כ${k}`", "`K${k}`"),
        ("`כ${prevKey}`", "`K${prevKey}`"),
        ("'כ'+r.el", "'K'+r.el"),
        ("'כ'+r.k", "'K'+r.k"),
        ("'כ' + duelHist.ra[i].k", "'K' + duelHist.ra[i].k"),
        # legend-title arrows: chronology reads left-to-right in English
        ("prevKey ? `סווינג כ${prevKey} ← כ${currentElection}` : 'סווינג';",
         "prevKey ? `Swing K${prevKey} → K${currentElection}` : 'Swing';"),
        ("prevKey ? `שינוי פער כ${prevKey} ← כ${currentElection}` : 'שינוי פער';",
         "prevKey ? `Trend K${prevKey} → K${currentElection}` : 'Trend';"),
        ("prevKey ? `שינוי בשיעור ההצבעה כ${prevKey} ← כ${currentElection}` : 'שינוי בשיעור ההצבעה';",
         "prevKey ? `Turnout change K${prevKey} → K${currentElection}` : 'Turnout change';"),
        ("(prevKey ? `סווינג ${pname} · כ${prevKey} ← כ${currentElection}` : `סווינג ${pname}`);",
         "(prevKey ? `${pname} swing · K${prevKey} → K${currentElection}` : `${pname} swing`);"),
        # swing-bar side labels: flex order flips under LTR, keep red-left / blue-right physical layout
        ("<span>ימין-חרדים →</span><span>← מרכז-שמאל</span>",
         "<span>← Center-Left</span><span>Right-Haredim →</span>"),
        ("title=\"ציר זמן 1992 ← 2022\"", "title=\"Timeline 1992 → 2022\""),
        # guided-tour button; story content itself lives in data/map_tours.json (he/en fields, read at runtime)
        ("title=\"הסיפורים הגדולים של כל מערכת בחירות: סיור מודרך על המפה\" style=\"font-weight:700;display:none\">🎬 סיפורים</button>",
         "title=\"The big stories of every election: a guided tour of the map\" style=\"font-weight:700;display:none\">🎬 Stories</button>"),
        # tourElectionLabel: drop the RTL branch (with its כ״ literal) entirely on the EN page
        ("return (TOUR_LANG === 'en' ? 'K' + k : 'כ״' + k) + ' · ' + KNESSET_YEARS[k];",
         "return 'K' + k + ' · ' + KNESSET_YEARS[k];"),
        # MUST run before the name-literal pass: bare 'ימינה' here means "rightward",
        # not the party Yamina (which IS in the names map and would be substituted)
        ("const side = val > 0 ? 'שמאלה' : 'ימינה';", "const side = val > 0 ? 'left' : 'right';"),
        # direct-PM candidate names: replaced wholesale BEFORE the name-literal pass
        # (bare 'ברק' is a names-map key — moshav Barak — and would become 'Baraq')
        ("  '1996': {kn:'14', concurrent:true,  right:'בנימין נתניהו', left:'שמעון פרס', rShort:'נתניהו', lShort:'פרס'},",
         "  '1996': {kn:'14', concurrent:true,  right:'Binyamin Netanyahu', left:'Shimon Peres', rShort:'Netanyahu', lShort:'Peres'},"),
        ("  '1999': {kn:'15', concurrent:true,  right:'בנימין נתניהו', left:'אהוד ברק',  rShort:'נתניהו', lShort:'ברק'},",
         "  '1999': {kn:'15', concurrent:true,  right:'Binyamin Netanyahu', left:'Ehud Barak',  rShort:'Netanyahu', lShort:'Barak'},"),
        ("  '2001': {kn:'15', concurrent:false, right:'אריאל שרון',   left:'אהוד ברק',  rShort:'שרון',   lShort:'ברק'},",
         "  '2001': {kn:'15', concurrent:false, right:'Ariel Sharon',   left:'Ehud Barak',  rShort:'Sharon',   lShort:'Barak'},"),
    ],
    "dashboard": [
        # language toggle: EN page links back to the Hebrew page
        ("<a class=\"lang\" lang=\"en\" href=\"dashboard_en.html\">EN</a>",
         "<a class=\"lang\" lang=\"he\" dir=\"rtl\" href=\"dashboard.html\">&#1506;&#1489;&#1512;&#1497;&#1514;</a>"),
        # LTR alignment flips
        ("    margin-bottom: 1rem;\n    text-align: right;\n}\n\n.selector-row",
         "    margin-bottom: 1rem;\n    text-align: left;\n}\n\n.selector-row"),
        (".party-table td {\n    padding: 0.6rem 1rem;\n    text-align: right;",
         ".party-table td {\n    padding: 0.6rem 1rem;\n    text-align: left;"),
        (".data-table td {\n    padding: 0.75rem 1rem;\n    text-align: right;",
         ".data-table td {\n    padding: 0.75rem 1rem;\n    text-align: left;"),
        (".outlier-table th {\n    text-align: right;", ".outlier-table th {\n    text-align: left;"),
        (".sort-indicator {\n    margin-right: 0.3rem;", ".sort-indicator {\n    margin-left: 0.3rem;"),
        ("    justify-content: flex-end;\n    padding-right: 0.5rem;",
         "    justify-content: flex-end;\n    padding-left: 0.5rem;"),
        ("padding: 0.5rem; text-align: right;", "padding: 0.5rem; text-align: left;"),
        ("text-align: right; padding: 0.4rem 0.5rem;", "text-align: left; padding: 0.4rem 0.5rem;"),
        ("<th style=\"text-align:right;padding:.45rem\">", "<th style=\"text-align:left;padding:.45rem\">"),
        ("<td style=\"padding:.45rem;text-align:right;font-weight:600\">",
         "<td style=\"padding:.45rem;text-align:left;font-weight:600\">"),
        # party cards: bloc color stripe hugs the reading edge
        ("border-right: 3px solid ${blocColors[party.bloc]}", "border-left: 3px solid ${blocColors[party.bloc]}"),
        # Chart.js RTL flags off
        ("rtl: true,", "rtl: false,"),
        ("textDirection: 'rtl',", "textDirection: 'ltr',"),
        # prediction bar: marker moves right as Right-Haredim % rises → labels must swap under LTR
        ("<span>100% ימין-חרדים</span>\n                                <span>100% מרכז-שמאל</span>",
         "<span>100% Center-Left</span>\n                                <span>100% Right-Haredim</span>"),
        # MUST run before the name-literal pass — these bare words collide with names_en keys:
        # 'אשכול' would become 'Eshkol' (the RC), 'ימינה' would become 'Yamina' (the party)
        ("label: 'אשכול',", "label: 'Cluster',"),
        ("'שמאלה' : (totalTrend < -0.5 ? 'ימינה' : 'יציב')",
         "'leftward' : (totalTrend < -0.5 ? 'rightward' : 'stable')"),
    ],
}


# ============================================================ statarea_map (2026-07-04)
GLOBAL["מפת שכונות"] = "Neighborhood Map"

PAGES["statarea_map"] = {
    "מפת אזורים סטטיסטיים — בחירות 2022 × מפקד 2022":
        "Statistical-Area Map — 2022 Election × 2022 Census",
    "שכונות ואזורים סטטיסטיים · 2022": "Neighborhoods & Statistical Areas · 2022",
    # ethnic-origin mode (2026-07-07)
    ">מוצא</button>": ">Origin</button>",
    ">מוצא לפי ארץ</button>": ">Origin by country</button>",
    "const OC_LABELS = {'ma':'מרוקו','su':'ברית המועצות לשעבר','ro':'רומניה','pl':'פולין','iq':'עירק','ye':'תימן','ir':'אירן','tr':'טורקיה','dz':\"אלג'יריה ותוניסיה\",'ly':'לוב','eg':'מצרים','et':'אתיופיה','bg':'בולגריה ויוון','de':'גרמניה ואוסטריה','eu':'שאר אירופה','as':'שאר אסיה','af':'שאר אפריקה','na':'צפון אמריקה ואוקיאניה','la':'אמריקה הלטינית'};":
        "const OC_LABELS = {'ma':'Morocco','su':'Former USSR','ro':'Romania','pl':'Poland','iq':'Iraq','ye':'Yemen','ir':'Iran','tr':'Turkey','dz':'Algeria & Tunisia','ly':'Libya','eg':'Egypt','et':'Ethiopia','bg':'Bulgaria & Greece','de':'Germany & Austria','eu':'Other Europe','as':'Other Asia','af':'Other Africa','na':'North America & Oceania','la':'Latin America'};",
    "case 'oc': return g('#141a24','#fb923c','0%', scales['oc_'+selectedOrigin].max+'%', 'מוצא ' + OC_LABELS[selectedOrigin] + ' (מפקד 1995, יהודים ואחרים)');":
        "case 'oc': return g('#141a24','#fb923c','0%', scales['oc_'+selectedOrigin].max+'%', OC_LABELS[selectedOrigin] + ' origin (1995 census, Jews & others)');",
    "['מוצא ישראל (דור שלישי)', c.orig_il!=null? c.orig_il+'%':'—', 'orig95'],": "['Israel origin (3rd generation)', c.orig_il!=null? c.orig_il+'%':'—', 'orig95'],",
    "return `<div class=\"fact\"><div class=\"k\">מוצא ${OC_LABELS[selectedOrigin]}</div><div class=\"v n\">${v!=null? v+'%':'—'}</div></div>`;":
        "return `<div class=\"fact\"><div class=\"k\">${OC_LABELS[selectedOrigin]} origin</div><div class=\"v n\">${v!=null? v+'%':'—'}</div></div>`;",
    "`<div style=\"margin-top:10px;font-weight:700;font-size:.82rem\">מוצא לפי ארצות (מפקד 1995)</div>` +":
        "`<div style=\"margin-top:10px;font-weight:700;font-size:.82rem\">Origin by country (1995 census)</div>` +",
    "const t = YEARS[YEAR].censusYr==='1995' ? 'מוצא עדתי (מפקד 1995, יהודים ואחרים)' : `מוצא עדתי (מפקד ${YEARS[YEAR].censusYr}, אזורים יהודיים)`;":
        "const t = YEARS[YEAR].censusYr==='1995' ? 'Ethnic origin (1995 census, Jews & others)' : `Ethnic origin (${YEARS[YEAR].censusYr} census, Jewish areas)`;",
    "<div class=\"lbls\"><span>אירופה-אמריקה +${scales.origin.max}</span><span>אסיה-אפריקה +${scales.origin.max}</span></div>":
        "<div class=\"lbls\"><span>Europe-America +${scales.origin.max}</span><span>Asia-Africa +${scales.origin.max}</span></div>",
    "['מוצא אסיה', c.orig_asia!=null? c.orig_asia+'%':'—', 'orig95'],": "['Asia origin', c.orig_asia!=null? c.orig_asia+'%':'—', 'orig95'],",
    "['מוצא אפריקה', c.orig_afr!=null? c.orig_afr+'%':'—', 'orig95'],": "['Africa origin', c.orig_afr!=null? c.orig_afr+'%':'—', 'orig95'],",
    "['מוצא אסיה-אפריקה', c.orig_asia!=null? (Math.round((c.orig_asia+(c.orig_afr||0))*10)/10)+'%':'—', 'orig'],":
        "['Asia-Africa origin', c.orig_asia!=null? (Math.round((c.orig_asia+(c.orig_afr||0))*10)/10)+'%':'—', 'orig'],",
    "['מוצא אירופה-אמריקה', c.orig_eur!=null? (Math.round((c.orig_eur+(c.orig_am||0))*10)/10)+'%':'—', 'orig'],":
        "['Europe-America origin', c.orig_eur!=null? (Math.round((c.orig_eur+(c.orig_am||0))*10)/10)+'%':'—', 'orig'],",
    ">גושים<": ">Blocs<",
    ">מפלגה מנצחת<": ">Winning Party<",
    ">מפלגה<": ">Party<",
    ">הצבעה<": ">Turnout<",
    ">דתיות<": ">Religiosity<",
    ">השכלה<": ">Education<",
    ">שכר<": ">Wage<",
    ">גיל<": ">Age<",
    ">עלייה<": ">Aliyah<",
    "חפש יישוב או כתובת...": "Search locality or address...",
    # address search (added 2026-07-07)
    "לא נמצאה כתובת בישראל": "No such address found in Israel",
    ">ימינה במרכז-שמאל</button>": ">Yamina in Center-Left</button>",
    ">ימינה בימין</button>": ">Yamina in Right</button>",
    "ברירת המחדל: ימינה נספרת במרכז-שמאל (ממשלת השינוי), כמו במפה האינטראקטיבית":
        "Default: Yamina counted in the Center-Left bloc (the change government), as in the interactive map",
    "ימינה נספרת בגוש הימין-חרדים": "Yamina counted in the Right-Haredi bloc",
    "' · ימינה בימין'": "' · Yamina in Right'",
    "בחר אזור במפה": "Pick an area on the map",
    "לחץ על שכונה/אזור סטטיסטי לפרופיל מלא": "Click a neighborhood / statistical area for its full profile",
    "המפה מציגה את תוצאות הבחירות לכנסת ה-25 (נובמבר 2022) ברמת אזור סטטיסטי:":
        "The map shows the 25th Knesset election results (November 2022) at statistical-area level:",
    "כ-2,400 שכונות ואזורים, מוצלבות עם נתוני מפקד האוכלוסין 2022 של הלמ\"ס.":
        "roughly 2,400 neighborhoods and areas, cross-referenced with the CBS 2022 census.",
    "<b>איך זה נבנה:</b> כ-32,700 קלפיות מוקמו גאוגרפית (98% הצלחה) ושויכו לאזור":
        "<b>How it was built:</b> ~32,700 polling stations were geocoded (98% success) and assigned to the",
    "הסטטיסטי שבו הן יושבות; הקולות סוכמו לכל אזור. הכיסוי: 97.3% מהקולות":
        "statistical area they sit in; votes were summed per area. Coverage: 97.3% of the",
    "הגאוגרפיים. מעטפות כפולות (458 אלף קולות) אינן ניתנות למיפוי מהותית.":
        "geographic vote. Double-envelope ballots (458K votes) are inherently unmappable.",
    "<b>אזהרות:</b> אחוז ההצבעה מחושב רק על הקלפיות שמוקמו; חלק מהאזורים הקטנים":
        "<b>Caveats:</b> turnout is computed only over mapped stations; some small areas",
    "מקבלים נתוני מפקד ברמת צירוף אזורים או ברמת היישוב (מסומן בפרופיל);":
        "get census data at combined-area or locality level (flagged in the profile);",
    "אנשים מצביעים לפעמים בקלפי שאינה בשכונת מגוריהם — כ-1% מהקולות \"זולגים\"":
        "people sometimes vote at a station outside their home neighborhood — about 1% of votes \"spill\"",
    "כך לאזור שכן. כיסוי המיקום נמוך מהממוצע בחלק מהיישובים הערביים (מג'ד":
        "into a neighboring area. Geocoding coverage is below average in some Arab localities (Majd",
    "אל-כרום 44%) ובהתנחלויות — ולכן סיכומים ארציים מהשכבה הזו מוטים מעט;":
        "al-Krum 44%) and in the settlements — so national sums from this layer are slightly biased;",
    "האחוזים בתוך כל אזור אמינים.": "within-area percentages are reliable.",
    "<b>מקור המיקומים:</b> קובץ הכתובות הרשמי של קלפיות הכנסת ה-25, בתוספת מאות תיקוני מיקום מאומתים. זו השכבה המדויקת ביותר במערכת.<br><br>":
        "<b>Location source:</b> the official 25th-Knesset polling-station address file, plus hundreds of verified position fixes. This is the most accurate layer in the system.<br><br>",
    "<b>מגבלת מיקום:</b> קובץ כתובות רשמי קיים רק לבחירות 2022; לבחירות אלה המיקומים משוחזרים לפי <b>שם המשכן</b>, ותיקונים שאומתו מול כתובות 2022 מיושמים לפי שם. משכן שהחליף בניין, או שני משכנים באותו שם בעיר, עלולים להופיע במיקומם של 2022.`;":
        "<b>Location caveat:</b> an official address file exists only for the 2022 election; for this election locations are reconstructed from <b>venue names</b>, and fixes verified against 2022 addresses are applied by name. A venue that changed buildings, or two same-named venues in one city, may appear at their 2022 location.`;",
    "<b>מגבלת מיקום:</b> ללא קובץ כתובות רשמי לבחירות אלה; המיקומים נשענים על התאמת שמות משכנים בין מערכות בחירות, והדיוק נמוך משכבת 2022.`;":
        "<b>Location caveat:</b> no official address file exists for this election; locations rely on venue-name matching across elections, and precision is lower than the 2022 layer.`;",
    "גוש מוביל": "Leading bloc",
    "מרכז-שמאל-ערבים +60": "Center-Left-Arabs +60",
    "ימין-חרדים +60": "Right-Haredim +60",
    "המפלגה המנצחת (מס' אזורים)": "Winning party (No. of areas)",
    ": אחוז קולות": ": vote share",
    "אחוז הצבעה (קלפיות ממופות)": "Turnout (mapped stations)",
    "מידת דתיות (משקי בית, למ\"ס)": "Religiosity (households, CBS)",
    "בעלי תואר אקדמי": "Academic degree holders",
    "שכר שנתי חציוני (₪)": "Median annual wage (NIS)",
    "גיל חציוני": "Median age",
    "עולי 2002+ מהאוכלוסייה": "Post-2002 immigrants, % of population",
    "אזור סטטיסטי": "Statistical area",
    "תושבים (מפקד)": "Residents (census)",
    "קולות כשרים": "Valid votes",
    "אחוז הצבעה~": "Turnout~",
    "קלפיות ממופות": "Mapped stations",
    "מפלגות מובילות": "Leading parties",
    "דמוגרפיה (מפקד 2022)": "Demographics (2022 census)",
    "תואר אקדמי": "Academic degree",
    "שכר שנתי חציוני": "Median annual wage",
    "בעשירונים 9-10": "In wage deciles 9-10",
    "עולי 2002+": "Post-2002 immigrants",
    "ילדים למשפחה": "Children per family",
    "בעלות על דירה": "Home ownership",
    "ללא רכב": "No car",
    "נתוני מפקד ברמת היישוב (אין פירוט שכונתי)": "Census data at locality level (no neighborhood detail)",
    "נתוני מפקד לצירוף אזורים סמוכים": "Census data for a combination of adjacent areas",
    "נתוני מפקד ישירים לאזור": "Direct census data for this area",
    "אין נתוני מפקד": "No census data",
    "~ אחוז ההצבעה מבוסס על בזב הקלפיות שמופו לאזור בלבד.":
        "~ Turnout is based only on the registered voters of stations mapped to this area.",
    "לאזור זה לא מופו קלפיות — נתוני מפקד בלבד.": "No stations were mapped to this area — census data only.",
    "אין נתונים לאזור זה": "No data for this area",
    "אין נתוני הצבעה ממופים לאזור זה": "No mapped vote data for this area",
    "אין נתוני הצבעה ממופים": "no mapped vote data",
    "מנצחת:": "winner:",
    # --- year toggle + 2009 layer (added 2026-07-05) ---
    "מפת אזורים סטטיסטיים · 2009×2008 · 2022×2022": "Statistical-Area Map · 2009×2008 · 2022×2022",
    "שכונות ואזורים סטטיסטיים": "Neighborhoods & Statistical Areas",
    "2022 · מפקד 2022": "2022 · Census 2022",
    "2009 · מפקד 2008": "2009 · Census 2008",
    ">דת<": ">Religion<",
    ">אשכול חב\"כ<": ">SES cluster<",
    "ימין-חרדים": "Right-Haredim",
    "מרכז-שמאל-ערבים": "Center-Left-Arabs",
    "קבוצה דתית מובילה ביישוב (2019)": "Leading religious group in locality (2019)",
    "אשכול חברתי-כלכלי (1-20, גבוה=מבוסס)": "Socioeconomic cluster (1-20, higher=affluent)",
    "דמוגרפיה (מפקד ": "Demographics (census ",
    "אשכול חב\"כ (1-20)": "SES cluster (1-20)",
    # --- electoral space layer (added 2026-07-09) ---
    ">פלחים</button>": ">Segments</button>",
    ">ציר חרדי-חילוני</button>": ">Haredi-secular axis</button>",
    "פלחים אלקטורליים (דפוס הצבעה, כל 30 השנים)":
        "Electoral segments (voting pattern, all 30 years)",
    "הציר החרדי-חילוני (מהמרחב האלקטורלי המשותף)":
        "The Haredi-secular axis (from the common electoral space)",
    ">חילוני-מרכז ${lo}<": ">Secular-center ${lo}<",
    ">חרדי +${hi}<": ">Haredi +${hi}<",
    ">פלח אלקטורלי:": ">Electoral segment:",
    "ציר חרדי-חילוני <span": "Haredi-secular axis <span",
    "· מובהקות שיוך": "· assignment confidence",
    ">מובהקות שיוך <span": ">assignment confidence <span",
    ">פלח: <b>": ">Segment: <b>",
    "ציר חרדי-חילוני: <span": "Haredi-secular axis: <span",
    "'חילוני מובהק'": "'strongly secular'",
    "' · למ\"ס'": "' · CBS'",
    "'מסורתי/מעורב'": "'traditional/mixed'",
    ">הציר החרדי-חילוני</div>": ">The Haredi-secular axis</div>",
    ">חילוני-מרכז <span": ">Secular-center <span",
    ">חרדי <span": ">Haredi <span",
    ">ייחוס (חציונים): חילוני <span": ">Reference (medians): secular <span",
    "· מסורתי <span": "· traditional <span",
    "· חרדי <span": "· Haredi <span",
    # --- metric explainers (added 2026-07-09) ---
    "<span class=\"mhint\">· הקישו על מדד להסבר</span>":
        "<span class=\"mhint\">· tap a metric for an explanation</span>",
    # --- SES 2019/2021 modern layer (added 2026-07-09) ---
    "'אשכול חברתי-כלכלי '+YEARS[YEAR].sesVin+' (1-10, גבוה=מבוסס)'":
        "'Socioeconomic cluster '+YEARS[YEAR].sesVin+' (1-10, higher=affluent)'",
    "'אשכול חב\"כ '+(YEARS[YEAR].sesVin||'')": "'SES cluster '+(YEARS[YEAR].sesVin||'')",
    "אשכול חב\"כ: אין פרסום לאזור זה; הושלם מממוצע הרובע (למ\"ס ${YEARS[YEAR].sesVin}).":
        "SES cluster: no per-area publication; filled from the quarter mean (CBS ${YEARS[YEAR].sesVin}).",
    "אשכול חב\"כ ברמת הרשות המקומית (פרסום למ\"ס 2019).":
        "SES cluster at local-authority level (CBS 2019 publication).",
    "אשכול חב\"כ ברמת היישוב (פרסום למ\"ס 2019).":
        "SES cluster at locality level (CBS 2019 publication).",
    "אשכול חב\"כ: פרסום למ\"ס ${YEARS[YEAR].sesVin} לאזורים סטטיסטיים, מותאם לגבולות מפקד 2022.":
        "SES cluster: CBS ${YEARS[YEAR].sesVin} statistical-area publication, crosswalked to 2022-census boundaries.",
    "נפשות למשק בית": "Persons per household",
    "ילדים לאישה": "Children per woman",
    "המפה מציגה את תוצאות הבחירות לכנסת ה-18 (פברואר 2009) ברמת אזור סטטיסטי:":
        "The map shows the 18th Knesset election results (February 2009) at statistical-area level:",
    "כ-2,300 אזורים, מוצלבות עם מפקד האוכלוסין 2008 של הלמ\"ס. <b>הצלבה שלא נעשתה קודם:</b>":
        "roughly 2,300 areas, cross-referenced with the CBS 2008 census. <b>A cross never done before:</b>",
    "כל בחירות עם המפקד בן-זמנן.<br><br>": "each election with its contemporary census.<br><br>",
    # --- 2009 intro rewritten for the official-address build (2026-07-12) ---
    "<b>איך זה נבנה:</b> רשימת הקלפיות הרשמית של ועדת הבחירות (דצמבר 2008) כוללת":
        "<b>How it was built:</b> the CEC official polling-place list (December 2008) includes",
    "<b>כתובת בת-הזמן לכל קלפי</b>; הכתובות קודדו גאוגרפית, אומתו מול פוליגוני היישוב,":
        "<b>a period-true address for every station</b>; the addresses were geocoded, validated against the locality polygons,",
    "ושויכו לאזור הסטטיסטי של מפקד 2008 (point-in-polygon). 55% מהקולות יושבים על":
        "and assigned to the 2008-census statistical area (point-in-polygon). 55% of the votes sit on",
    "כתובת רשמית והיתר על התאמת שמות משכנים; כיסוי: 99.7% מהקולות הגאוגרפיים":
        "an official address, the rest on venue-name matching; coverage: 99.7% of the geographic vote",
    "(סגירה מול סך הקולות ביישוב: 99.9%).<br><br>":
        "(closure against each locality's total: 99.9%).<br><br>",
    "<b>אזהרות:</b> נתוני דת הם ברמת היישוב (2019); חלק מהאזורים מקבלים מפקד ברמת":
        "<b>Caveats:</b> religion data is at locality level (2019); some areas get census at",
    "היישוב; אשכול חברתי-כלכלי קיים ל-56% מהאזורים (יישובים ≥10k). בגבעת זאב":
        "locality level; a socioeconomic cluster exists for 56% of areas (localities ≥ 10k). In Giv'at Ze'ev",
    "ובביתר עילית חלק ניכר מהקולות עדיין יושב על":
        "and Beitar Illit a large share of votes still sits on",
    "קואורדינטות מוערכות, <span class=\"warn\">והמפה השכונתית שם פחות מדויקת</span>;":
        "estimated coordinates, <span class=\"warn\">and the neighborhood map there is less accurate</span>;",
    "הסיכום ברמת היישוב אמין.": "the locality-level summary is reliable.",
    "הסטטיסטי שבו הן יושבות; הקולות סוכמו לכל אזור. הכיסוי: 97.3% מהקולות הגאוגרפיים.<br><br>":
        "statistical area they sit in; votes were summed per area. Coverage: 97.3% of the geographic vote.<br><br>",
    "<b>אזהרות:</b> אחוז ההצבעה מחושב רק על הקלפיות שמוקמו; חלק מהאזורים מקבלים":
        "<b>Caveats:</b> turnout is computed only over mapped stations; some areas get",
    "נתוני מפקד ברמת צירוף אזורים או ברמת היישוב; כ-1% מהקולות \"זולגים\" לאזור שכן.":
        "census data at combined-area or locality level; about 1% of votes \"spill\" into a neighboring area.",
    # --- 2003/2006 vote-only layers on 1995 geometry (added 2026-07-05) ---
    "2006 · גבולות 1995": "2006 · 1995 boundaries",
    "2003 · גבולות 1995": "2003 · 1995 boundaries",
    "המפה מציגה את תוצאות הבחירות לכנסת ה-17 (מרץ 2006) ברמת אזור סטטיסטי, על":
        "The map shows the 17th Knesset election results (March 2006) at statistical-area level, on",
    "גבולות האזורים הסטטיסטיים של מפקד 1995. <b>שכבת קולות בלבד</b> — למפקד 1995 אין":
        "the 1995-census statistical-area boundaries. <b>Votes-only layer</b> — the 1995 census has no",
    "קובץ נתונים שכונתי זמין, ולכן אין הצלבת דמוגרפיה.<br><br>":
        "neighborhood-level data file available, so there is no demographic cross-reference.<br><br>",
    "<b>איך זה נבנה:</b> קובץ הקלפיות הרשמי של 2006 כולל את <b>כתובת הקלפי בת-הזמן</b>":
        "<b>How it was built:</b> the official 2006 ballot file carries each station's <b>contemporaneous street address</b>",
    "(99.8% מהקולות); הכתובות קודדו גאוגרפית ואומתו מול פוליגוני היישוב, ואז שויכו":
        "(99.8% of votes); the addresses were geocoded, validated against the locality's own polygons, and assigned",
    "לאזור הסטטיסטי (point-in-polygon). שיטה עצמאית לחלוטין ממאגר המשכנים המודרני":
        "to their statistical area (point-in-polygon). A method fully independent of the modern venue master",
    "שעליו נשענות שכבות 2009 ואילך.<br><br>":
        "that the 2009+ layers rely on.<br><br>",
    "<b>אזהרות:</b> בקובץ 2006 אין נתוני בעלי זכות בחירה, ולכן אין אחוז הצבעה;":
        "<b>Caveats:</b> the 2006 file has no registered-voter counts, hence no turnout;",
    "חלק מהקלפיות מוקמו לפי קלפי שכנה (אימפוטציה) או ברמת רחוב בלבד.":
        "some stations are placed via a neighboring station (imputation) or at street level only.",
    "המפה מציגה את תוצאות הבחירות לכנסת ה-16 (ינואר 2003) ברמת אזור סטטיסטי, על":
        "The map shows the 16th Knesset election results (January 2003) at statistical-area level, on",
    "גבולות מפקד 1995. <b>שכבת קולות בלבד</b> — ללא הצלבת מפקד.<br><br>":
        "the 1995-census boundaries. <b>Votes-only layer</b> — no census cross-reference.<br><br>",
    "<b>איך זה נבנה:</b> מספרי הקלפי של 2003 הוצלבו לקלפיות 2006 באותו יישוב":
        "<b>How it was built:</b> 2003 ballot-box numbers were joined to the 2006 boxes of the same locality",
    "(כ-96.6% התאמה מדויקת, צעד אחד אחורה בלבד) וירשו את קואורדינטת כתובת הקלפי":
        "(~96.6% exact matches, a single step back) and inherited the station-address coordinate",
    "של 2006. בחירות 2003 קדמו לאיחודי הרשויות של נובמבר 2003, ולכן סמלי היישובים":
        "from 2006. The 2003 election predates the November 2003 municipal mergers, so locality codes",
    "תואמים את גאומטריית 1995 באופן טבעי.<br><br>":
        "natively match the 1995 geometry.<br><br>",
    "<b>אזהרות:</b> השיטה מניחה יציבות מספרי קלפי 2003→2006; קלפיות שלא הוצלבו":
        "<b>Caveats:</b> the method assumes 2003→2006 ballot-number stability; unmatched boxes",
    "מוקמו לפי קלפי שכנה או הושמטו.":
        "were placed via a neighboring box or dropped.",
    "שכבת קולות בלבד; למפקד 1995 אין נתונים שכונתיים זמינים":
        "Votes-only layer; no neighborhood-level 1995 census data is available",
    "לאזור זה לא מופו קלפיות": "No stations were mapped to this area",
    "; נתוני מפקד בלבד": "; census data only",
    # --- poster mode + K19-K24 years (added 2026-07-05) ---
    ">ספט׳ 2019<": ">Sep 2019<",
    ">אפר׳ 2019<": ">Apr 2019<",
    "🗺 פוסטר": "🗺 Poster",
    "מצב פוסטר: מנצחת מוצללת לפי אחוז + מילוי עירוני מתחת לאזורים":
        "Poster mode: winner shaded by vote share + municipal fill beneath the areas",
    # poster-area chooser (2026-07-12)
    "אזור הפוסטר:": "Poster area:",
    ">🗺 כל הארץ</button>": ">🗺 Whole country</button>",
    ">האזור הנוכחי</button>": ">Current view</button>",
    # HD poster renderer (2026-07-12)
    "'גוש דן'": "'Gush Dan'",
    "' מנדטים'": "' seats'",
    " אזורים`": " areas`",
    "תוצאות רשמיות: ועדת הבחירות המרכזית · גבולות ומפקד: למ\"ס":
        "Official results: Central Elections Committee · boundaries & census: CBS",
    "מפלגה מנצחת × אחוז קולות": "Winning party × vote share",
    "תוצאה ברמת היישוב": "Locality-level result",
    "המפה מציגה את תוצאות הבחירות לכנסת ה-${k} (${when}) ברמת אזור סטטיסטי,":
        "The map shows the election results for Knesset ${k} (${when}) at statistical-area level,",
    "מוצלבות עם מפקד 2022. <b>שימו לב:</b> המפקד מאוחר לבחירות: הדמוגרפיה משקפת את 2022, לא את יום הבחירות.<br><br>":
        "cross-referenced with the 2022 census. <b>Note:</b> the census postdates the election: demographics reflect 2022, not election day.<br><br>",
    "<b>איך זה נבנה:</b> כמו שכבת 2022: מיקומי קלפיות ממאגר המשכנים (+תיקוני מיקום), point-in-polygon לאזורי מפקד 2022.":
        "<b>How it was built:</b> like the 2022 layer: station locations from the venue master (+coordinate fixes), point-in-polygon into 2022-census areas.",
    "מוצלבות עם מפקד 2008 (המפקד הקרוב ביותר). <b>שימו לב:</b> המפקד מוקדם לבחירות.<br><br>":
        "cross-referenced with the 2008 census (the nearest one). <b>Note:</b> the census predates the election.<br><br>",
    "<b>איך זה נבנה:</b> כמו שכבת 2009: התאמת שמות משכנים (+תיקוני מיקום), point-in-polygon לאזורי מפקד 2008.":
        "<b>How it was built:</b> like the 2009 layer: venue-name matching (+coordinate fixes), point-in-polygon into 2008-census areas.",
    "'מרץ 2021'": "'March 2021'",
    "'מרץ 2020'": "'March 2020'",
    "'ספטמבר 2019'": "'September 2019'",
    "'אפריל 2019'": "'April 2019'",
    "'מרץ 2015'": "'March 2015'",
    "'ינואר 2013'": "'January 2013'",
    # --- interpolated-fill toggle (added 2026-07-05) ---
    "אזורים ללא קלפי נצבעים לפי האזור המצביע הקרוב ביותר באותו יישוב: אומדן תצוגה בלבד, לא נתון אמיתי":
        "Areas with no polling station are colored from the nearest voting area in the same locality: a display-only estimate, not real data",
    ">≈ מילוי משוער<": ">≈ Estimated fill<",
    "מילוי משוער מאזור סמוך (ללא קלפי)": "Estimated fill from a nearby area (no station)",
    "<b>≈ מילוי משוער</b> מהאזור המצביע הקרוב (אזור": "<b>≈ Estimated fill</b> from the nearest voting area (area",
    "אומדן תצוגה בלבד; תושבי האזור מצביעים בקלפי שמחוץ לו.":
        "Display-only estimate; this area's residents vote at a station outside it.",
    "≈ משוער מאזור": "≈ estimated from area",
    # --- corrected venue dots layer (added 2026-07-06) ---
    ">📍 קלפיות<": ">📍 Stations<",
    "מיקומי הקלפיות המתוקנים: כל נקודה היא משכן קלפי; צבע: המפלגה המנצחת בו, גודל: מספר קולות":
        "Corrected polling-station locations: each dot is one polling venue; color: its winning party, size: vote count",
    "קלפי · צבע: מנצחת · גודל: קולות": "Station · color: winner · size: votes",
    " משכנים (": " venues (",
    " מהקולות)": " of votes)",
    "||'קלפי'": "||'Station'",
    "קולות:": "Votes:",
    "קלפיות:": "Stations:",
    # --- satellite basemap toggle (added 2026-07-07) ---
    ">🛰️ לוויין<": ">🛰️ Satellite<",
    "רקע לוויין: תצלומי אוויר במקום המפה הכהה; שימושי לזיהוי בניינים ושכונות סביב הקלפיות":
        "Satellite basemap: aerial imagery instead of the dark map; useful for identifying buildings and neighborhoods around the stations",
    # --- 1995 census cross for 2003/2006 (added 2026-07-06) ---
    "2006 · מפקד 1995": "2006 · Census 1995",
    "2003 · מפקד 1995": "2003 · Census 1995",
    "גבולות האזורים הסטטיסטיים של מפקד 1995, <b>מוצלבות עם נתוני מפקד 1995</b>":
        "the 1995-census statistical-area boundaries, <b>cross-referenced with the 1995 census</b>",
    "(דת, גיל, עולי 1990+; ~91% מהאזורים).<br><br>":
        "(religion, age, post-1990 immigrants; ~91% of areas).<br><br>",
    "גבולות מפקד 1995, <b>מוצלבות עם נתוני מפקד 1995</b> (דת, גיל, עולי 1990+).<br><br>":
        "the 1995-census boundaries, <b>cross-referenced with the 1995 census</b> (religion, age, post-1990 immigrants).<br><br>",
    "'קבוצה דתית מובילה (מפקד 1995)' : 'קבוצה דתית מובילה ביישוב (2019)'":
        "'Leading religious group (1995 census)' : 'Leading religious group in locality (2019)'",
    "'עולי 1990+ מהאוכלוסייה (מפקד 1995)' : 'עולי 2002+ מהאוכלוסייה'":
        "'Post-1990 immigrants, % of population (1995 census)' : 'Post-2002 immigrants, % of population'",
    "עולי 1990+": "Post-1990 immigrants",
    "ילידי ברה\"מ לשעבר": "Born in former USSR",
    "בני 65+": "Aged 65+",
    "בתי אב עם ילדים": "Households with children",
    "ילידי ישראל": "Israel-born",
    "מוצא אירופה-אמריקה": "Europe-America origin",
    # --- mobile bottom-sheet panel (added 2026-07-06) ---
    "✕ סגירה": "✕ Close",
    # --- poster PNG export (added 2026-07-06) ---
    "ייצוא תצוגת הפוסטר הנוכחית לקובץ PNG, כולל כותרת, מקרא ומקורות":
        "Export the current poster view to a PNG file, with title, legend and sources",
    "המפלגה המנצחת לפי אזור סטטיסטי · גוון בהיר = אחוז קולות גבוה":
        "Winning party per statistical area · lighter shade = higher vote share",
    # --- venue-dot click panel (added 2026-07-06) ---
    "הקולות שנספרו בפועל במשכן זה. לפרופיל השכונה לחץ על שטח האזור שמסביב לנקודה.":
        "The votes actually counted at this venue. For the neighborhood profile, click the area surrounding the dot.",
    "קלפיות במשכן": "Ballot boxes in venue",
    "משכן קלפי": "Polling venue",
    ">מנצחת<": ">Winner<",
    ">אחוז הצבעה<": ">Turnout<",
    # --- residence-estimate layer (added 2026-07-06) ---
    "אומדן מגורים: קולות כל קלפי מחולקים חזרה לאזורי המגורים שהיא משרתת, לפי קרבה ואוכלוסייה: מודל, לא ספירה ישירה":
        "Residence estimate: each polling venue's votes are split back over the residential areas it serves, by proximity and population: a model, not a direct count",
    "קולות כל קלפי חולקו לאזורי המגורים שהיא משרתת, לפי קרבה ואוכלוסייה,":
        "Each venue's votes were split over the residential areas it serves, by proximity and population,",
    "🏠 אומדן מגורים: מודל, לא ספירה": "🏠 Residence estimate: model, not a count",
    ">🏠 אומדן מגורים<": ">🏠 Residence estimate<",
    "🏠 אומדן מגורים:": "🏠 Residence estimate:",
    "משכני קלפי תורמים:": "Contributing polling venues:",
    "בקלפיות שבאזור: ": "At the stations inside it: ",
    "קולות (אומדן):": "Votes (estimate):",
    "שגיאה חציונית": "median error",
    " נק׳ באימות.": " pts in hold-out validation.",
    " נק׳": " pts",
    " (מודל):": " (model):",
    "אזור": "area",
    "גבולות: למ\"ס": "Boundaries: CBS",
    # --- change-vs-baseline (swing) modes (added 2026-07-13) ---
    ">שינוי גושים</button>": ">Bloc swing</button>",
    ">שינוי מפלגה</button>": ">Party swing</button>",
    "שינוי פער הגושים מאז ": "Bloc-margin change since ",
    ": שינוי אחוז מאז ": ": share change since ",
    "<div class=\"lbls\"><span>לשמאל +30</span><span>לימין +30</span></div>":
        "<div class=\"lbls\"><span>+30 leftward</span><span>+30 rightward</span></div>",
    "שינוי מאז ": "Change since ",
    " נק׳ לימין": " pts rightward",
    " נק׳ לשמאל": " pts leftward",
    "; באזורים קטנים שינוי חד עשוי לשקף גם הזזת קלפי":
        "; in small areas a sharp change may also reflect a station relocation",
    "(היה ": "(was ",
    " מאז ": " since ",
    # --- station-location confidence badge (added 2026-07-13) ---
    "const CONF = {vhigh:{c:'#2ecc71',t:'גבוהה מאוד'},high:{c:'#2ecc71',t:'גבוהה'},mhigh:{c:'#fbbf24',t:'בינונית-גבוהה'},med:{c:'#f97316',t:'בינונית'}};":
        "const CONF = {vhigh:{c:'#2ecc71',t:'Very high'},high:{c:'#2ecc71',t:'High'},mhigh:{c:'#fbbf24',t:'Medium-high'},med:{c:'#f97316',t:'Medium'}};",
    "אמינות מיקומי הקלפיות: ": "Station-location confidence: ",
    "אין קובץ כתובות רשמי לבחירות אלה; המיקומים משוחזרים לפי שם המשכן מול מאגר 2022; משכן שהחליף בניין יופיע במיקומו של 2022":
        "No official address file exists for these elections; locations are reconstructed by venue name against the 2022 master; a venue that changed buildings will appear at its 2022 location",
    "קובץ הכתובות הרשמי של ועדת הבחירות + מאות תיקוני מיקום מאומתים; השכבה המדויקת במערכת":
        "The official CEC address file plus hundreds of verified position fixes; the most accurate layer in the system",
    "קובץ הכתובות הרשמי בן-הזמן של ועדת הבחירות; בגבעת זאב ובביתר עילית חלק מהמיקומים מוערכים":
        "The period-true official CEC address file; in Givat Zeev and Beitar Illit some locations are estimated",
    "קובץ הכתובות הרשמי בן-הזמן: כתובת לכל קלפי (99.8% מהקולות), שיטה עצמאית מהמאגר המודרני":
        "The period-true official address file: an address for every station (99.8% of votes), independent of the modern venue master",
    "ירושה של כתובות 2006 הרשמיות בהצלבת מספרי קלפי (כ-96.6% התאמה מדויקת)":
        "Inherits the official 2006 addresses via ballot-number matching (~96.6% exact match)",
    "רוב הקולות יורשים את כתובות 2009 הרשמיות בהצלבת מספרי קלפי (כ-90%); היתר לפי התאמת שמות משכנים":
        "Most votes inherit the official 2009 addresses via ballot-number matching (~90%); the rest by venue-name matching",
    "רוב הקולות יורשים את כתובות 2009 הרשמיות בהצלבת מספרי קלפי (כ-92%); היתר לפי התאמת שמות משכנים":
        "Most votes inherit the official 2009 addresses via ballot-number matching (~92%); the rest by venue-name matching",
    # --- census-vs-census education change (added 2026-07-13) ---
    ">שינוי השכלה</button>": ">Education change</button>",
    "שינוי בבעלי תואר אקדמי: ממפקד 2008 למפקד 2022 (נק׳)":
        "Change in academic-degree share: 2008 census to 2022 census (pts)",
    "שינוי השכלה ממפקד 2008: ": "Education change since the 2008 census: ",
    " במפקד 2022 מול כ-": " in the 2022 census vs ~",
    " במפקד 2008 (הקרנת גבולות): שינוי של ": " in the 2008 census (boundary projection): a change of ",
}

FIXES["statarea_map"] = [
    ("<a class=\"lang\" lang=\"en\" href=\"statarea_map_en.html\">EN</a>",
     "<a class=\"lang\" lang=\"he\" dir=\"rtl\" href=\"statarea_map.html\">&#1506;&#1489;&#1512;&#1497;&#1514;</a>"),
    # guided-tour + explain buttons; story/help content lives in data/statarea_tours.json + statarea_help.json (he/en, runtime)
    ("<button class=\"mode-btn\" id=\"tourBtn\" style=\"display:none\" title=\"הסיפורים הגדולים של המפה השכונתית: סיור מודרך, תחנה אחר תחנה\">🎬 סיפורים</button>",
     "<button class=\"mode-btn\" id=\"tourBtn\" style=\"display:none\" title=\"The big stories of the neighborhood map: a guided tour, stop by stop\">🎬 Stories</button>"),
    ("<button class=\"mode-btn\" id=\"helpBtn\" style=\"display:none\" title=\"מה אני רואה כאן? הסבר על מצב התצוגה הנוכחי\">?</button>",
     "<button class=\"mode-btn\" id=\"helpBtn\" style=\"display:none\" title=\"What am I looking at? Explanation of the current view\">?</button>"),
    # time-lapse (2026-07): overlay text reuses the year-btn labels at runtime, already translated
    ("<button class=\"mode-btn\" id=\"playBtn\" title=\"ציר זמן 2003 ← 2022: הרצת כל השנים ברצף\" style=\"font-weight:700\">▶</button>",
     "<button class=\"mode-btn\" id=\"playBtn\" title=\"Timeline 2003 → 2022: plays all the years in sequence\" style=\"font-weight:700\">▶</button>"),
    # MUST run before the name-literal pass: bare 'יהוד' is the Jewish-prefix check in originVal,
    # not the city Yehud (which IS in the names map and would be substituted)
    ("if(rel && !rel.startsWith('יהוד')) return null;", "if(rel && !rel.startsWith('Jew')) return null;"),
]

# ---------------- demographics: INES micro section (2026-07-04) ----------------
PAGES["demographics"].update({
    "🧪 וגם ברמת הפרט: הפער בסקרי INES": "🧪 At the Individual Level Too: the Gap in the INES Surveys",
    "כל הממצאים בעמוד הזה אקולוגיים: צירופי יישובים, לא בני-אדם. כאן אותו פער נמדד <b>ברמת הפרט</b>, מתוך 14 סקרי הבחירות הלאומיים (INES, 1992–2022): פער ההצבעה לימין-חרדים בין משיבים <b>ללא תואר אקדמי</b> ובין <b>בעלי תואר</b> (יהודים, מצביעים בלבד, משוקלל היכן שיש משקולות). בעידן השאלה הישירה: הפער עמד על כ-<span class=\"n\">11</span> נק\"א ב-1999, <b>קרס ל-<span class=\"n\">2.5</span> נק\"א ב-2006</b> (רעידת האדמה של קדימה טשטשה לרגע את שסע ההשכלה), <b>ומאז טיפס בהתמדה עד <span class=\"n\">22–21</span> נק\"א ב-2021–2022</b>. כיוון ההחרפה של השיפוע האקולוגי משוחזר גם בנתוני הפרט; המיון איננו תוצר של צירוף היישובים.":
        "Everything else on this page is ecological: locality aggregates, not people. Here the same divide is measured <b>at the individual level</b>, from the 14 national election surveys (INES, 1992–2022): the Right-Haredi voting gap between respondents <b>without an academic degree</b> and <b>degree holders</b> (Jews, voters only, weighted where weights exist). In the direct-question era: the gap stood at ~<span class=\"n\">11</span> points in 1999, <b>collapsed to <span class=\"n\">2.5</span> points in 2006</b> (the Kadima earthquake briefly blurred the education divide), <b>and has since climbed steadily to <span class=\"n\">21–22</span> points in 2021–2022</b>. The direction of the ecological steepening is reproduced in individual-level data; the sorting is not an artifact of aggregating localities.",
    "<label><input type=\"radio\" name=\"idim\" value=\"education\" checked> השכלה</label>":
        "<label><input type=\"radio\" name=\"idim\" value=\"education\" checked> Education</label>",
    "<label><input type=\"radio\" name=\"idim\" value=\"religiosity\"> דתיות</label>":
        "<label><input type=\"radio\" name=\"idim\" value=\"religiosity\"> Religiosity</label>",
    "<label><input type=\"radio\" name=\"idim\" value=\"age\"> גיל</label>":
        "<label><input type=\"radio\" name=\"idim\" value=\"age\"> Age</label>",
    "מקור: Israel National Election Studies: מדגם ארצי לכל מערכת בחירות (n≈500–1,500 מצביעים); הציטוט המלא לכל סקר בעמוד":
        "Source: Israel National Election Studies: a national sample per election (n≈500–1,500 voters); full per-study citations on the",
    "נדידת הקולות</a>. הצבעה: דיווח שלאחר הבחירות היכן שנשאל, אחרת כוונת הצבעה. <b>הגדרת ההשכלה</b>: שאלת תואר ישירה מ-1999 ואילך; ב-1992/1996/2013 קירוב לפי 16+ שנות לימוד (נקודות אלו אינן בנות-השוואה ישירה לשאר). <b>דתיות</b>: הגדרה עצמית (חרדי/דתי/מסורתי/חילוני) היכן שנשאלה; בגלים 1992–1996, 2009–2015 סולם שמירת-מסורת מקורב ללא רובד חרדי. <b>מוצא</b>: יבשת הלידה של הנשאל, וליליד הארץ, יבשת הלידה של אביו; ב-1996 הגדרה עצמית (ספרדי/אשכנזי, ללא רובד דור-שלישי); עולי בריה\"מ נכללים באירופה-אמריקה לאורך כל הסדרה; בקובץ 2003 תוקנה הסטת-קידוד של קטגוריות ילידי-הארץ (אומתה מול שולי 1999). קבוצות מתחת ל-30 משיבים מושמטות; נקודה חלולה מסמנת קבוצה דקה (n&lt;100). טעות דגימה לקבוצה: ±3–6 נק\"א; המגמה היא הממצא, לא נקודה בודדת. הצלבה מול התוצאה הארצית: סטיית הסקרים 0–9 נק\"א (הטיות סקרים מוכרות, למשל חסר-ימין ב-1996).":
        "Vote Transfers page</a>. Vote: post-election report where asked, otherwise vote intent. <b>Education definition</b>: a direct degree question from 1999 on; in 1992/1996/2013 proxied by 16+ years of schooling (those points are not directly comparable to the rest). <b>Religiosity</b>: self-definition (Haredi/religious/traditional/secular) where asked; the 1992–1996 and 2009–2015 waves use an approximate tradition-observance scale with no Haredi tier. <b>Origin</b>: the respondent&#39;s continent of birth, or the father&#39;s for the Israel-born; 1996 uses sephardi/ashkenazi self-definition (no third-generation tier); FSU olim count within Europe-America throughout; the 2003 file&#39;s Israel-born category code-shift was fixed (verified against the 1999 margins). Groups under 30 respondents are suppressed; a hollow point marks a thin group (n&lt;100). Sampling error per group: ±3–6 points; the trend is the finding, not any single point. Cross-checked against the national result: survey deviation 0–9 points (known survey biases, e.g. the 1996 right-undercount).",
    "פער 1999: <b class=\"n\">": "1999 gap: <b class=\"n\">",
    "פער 2006: <b class=\"n\">": "2006 gap: <b class=\"n\">",
    "פער 2022: <b class=\"n\">": "2022 gap: <b class=\"n\">",
    "</b> נק\"א": "</b> pts",
    "מצביעים במדגם 2022": "voters in the 2022 sample",
    "חרדים 2022: <b class=\"n\">": "Haredim 2022: <b class=\"n\">",
    "</b> ימין-חרדים": "</b> Right-Haredim",
    "חילונים 2022: <b class=\"n\">": "Seculars 2022: <b class=\"n\">",
    "סולם: הגדרה עצמית מ-1999; שמירת-מסורת בגלים ישנים": "Scale: self-definition from 1999; tradition-observance in older waves",
    "18–34 ב-2022: <b class=\"n\">": "18–34 in 2022: <b class=\"n\">",
    "55+ ב-2022: <b class=\"n\">": "55+ in 2022: <b class=\"n\">",
    "פער הדורות מתהפך לאורך התקופה": "the generational gap inverts over the period",
    "'ללא תואר אקדמי'": "'No academic degree'",
    "'בעלי תואר אקדמי'": "'Academic degree'",
    "'חרדים'": "'Haredim'",
    "'דתיים'": "'Religious'",
    "'מסורתיים'": "'Traditional'",
    "'חילונים'": "'Secular'",
    "% הצבעה לימין-חרדים (מצביעים, סקר)": "% Right-Haredi vote (voters, survey)",
    "% ימין-חרדים (n=": "% Right-Haredim (n=",
})


PAGES["demographics"]["{ 21:'2019א', 22:'2019ב' }"] = "{ 21:'Apr 2019', 22:'Sep 2019' }"
