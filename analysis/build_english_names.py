# -*- coding: utf-8 -*-
"""
build_english_names.py — builds data/names_en.json for the English site pages.

Sources:
  * ~/Downloads/statistical_areas_2022.geojson  (official CBS SHEM_YISHUV -> SHEM_YISHUV_ENGLISH)
  * data/parties_national.json                  (party display names per election)
  * PARTY_EN / CITY_OVERRIDES hand maps below   (document of record)

Also scans every data/*.json + findings_data.json for distinct Hebrew strings and
writes a coverage report (analysis/en_names_report.txt) classifying each as
locality / party / election-name / uncovered, so the runtime fetch-shim's map
provably covers the data-driven Hebrew.

Run:  python -X utf8 analysis/build_english_names.py
"""
import json, re, os, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEO_SRC = os.path.expanduser(r"~\Downloads\statistical_areas_2022.geojson")
OUT = os.path.join(ROOT, "data", "names_en.json")
REPORT = os.path.join(ROOT, "analysis", "en_names_report.txt")

HEB = re.compile(r"[֐-׿]")

# ---------------------------------------------------------------- CBS extraction
def cbs_pairs():
    """Stream the 120MB geojson; regex out (SHEM_YISHUV, SHEM_YISHUV_ENGLISH) pairs.
    Names may contain JSON-escaped quotes (בני עי\"ש) — the pattern must not stop there."""
    pat = re.compile(r'"SHEM_YISHUV":\s*"((?:[^"\\]|\\.)*)",\s*"SHEM_YISHUV_ENGLISH":\s*"((?:[^"\\]|\\.)*)"')
    pairs = {}
    with open(GEO_SRC, encoding="utf-8") as f:
        for line in f:
            m = pat.search(line)
            if m:
                he = m.group(1).replace('\\"', '"').strip()
                en = m.group(2).replace('\\"', '"').strip()
                if he and en:
                    pairs[he] = en
    return pairs

def title_case(s):
    """TEL AVIV - YAFO -> Tel Aviv - Yafo; keep letters after internal apostrophes lower."""
    def cap(word):
        # capitalize first alpha char only, lower the rest (BE'ER -> Be'er)
        out, done = [], False
        for ch in word:
            if ch.isalpha():
                out.append(ch.upper() if not done else ch.lower())
                done = True
            else:
                out.append(ch)
        return "".join(out)
    s = " ".join(cap(w) for w in s.split())
    # re-capitalize after hyphens and opening parens: RAMAT-GAN -> Ramat-Gan
    s = re.sub(r"([-(])([a-z])", lambda m: m.group(1) + m.group(2).upper(), s)
    return s

# Common-English spellings for well-known places (CBS uses Q/W official romanization).
CITY_OVERRIDES = {
    "ירושלים": "Jerusalem",
    "תל אביב - יפו": "Tel Aviv-Yafo",
    "חיפה": "Haifa",
    "באר שבע": "Be'er Sheva",
    "ראשון לציון": "Rishon LeZion",
    "פתח תקווה": "Petah Tikva",
    "אשדוד": "Ashdod",
    "נתניה": "Netanya",
    "בני ברק": "Bnei Brak",
    "חולון": "Holon",
    "רמת גן": "Ramat Gan",
    "רחובות": "Rehovot",
    "אשקלון": "Ashkelon",
    "בת ים": "Bat Yam",
    "בית שמש": "Beit Shemesh",
    "כפר סבא": "Kfar Saba",
    "הרצליה": "Herzliya",
    "חדרה": "Hadera",
    "מודיעין-מכבים-רעות": "Modi'in-Maccabim-Re'ut",
    "מודיעין עילית": "Modi'in Illit",
    "נצרת": "Nazareth",
    "לוד": "Lod",
    "רמלה": "Ramla",
    "רעננה": "Ra'anana",
    "אילת": "Eilat",
    "טבריה": "Tiberias",
    "עכו": "Akko",
    "עפולה": "Afula",
    "קריית גת": "Kiryat Gat",
    "קריית אתא": "Kiryat Ata",
    "קריית מוצקין": "Kiryat Motzkin",
    "קריית ים": "Kiryat Yam",
    "קריית ביאליק": "Kiryat Bialik",
    "קריית אונו": "Kiryat Ono",
    "קריית שמונה": "Kiryat Shmona",
    "קריית מלאכי": "Kiryat Malakhi",
    "נהריה": "Nahariya",
    "גבעתיים": "Givatayim",
    "הוד השרון": "Hod HaSharon",
    "ראש העין": "Rosh HaAyin",
    "רמת השרון": "Ramat HaSharon",
    "נס ציונה": "Ness Ziona",
    "יבנה": "Yavne",
    "אור יהודה": "Or Yehuda",
    "צפת": "Safed",
    "דימונה": "Dimona",
    "ערד": "Arad",
    "סחנין": "Sakhnin",
    "אום אל-פחם": "Umm al-Fahm",
    "טייבה": "Tayibe",
    "שפרעם": "Shefar'am",
    "אלעד": "El'ad",
    "ביתר עילית": "Beitar Illit",
    "מעלה אדומים": "Ma'ale Adumim",
    "אריאל": "Ariel",
    "גני תקווה": "Ganei Tikva",
    "יהוד-מונוסון": "Yehud-Monosson",
    "מבשרת ציון": "Mevaseret Zion",
    "זכרון יעקב": "Zikhron Ya'akov",
    "פרדס חנה-כרכור": "Pardes Hanna-Karkur",
    "רמת הגולן": "Ramat HaGolan",
    "נצרת עילית": "Nazareth Illit",  # pre-2019 name of Nof HaGalil
    "נוף הגליל": "Nof HaGalil",
    "דאלית אל-כרמל": "Daliyat al-Karmel",
    "דאלית אל כרמל": "Daliyat al-Karmel",
    "מגדל העמק": "Migdal HaEmek",
    "יקנעם עילית": "Yokneam Illit",
    "בית שאן": "Beit She'an",
    "מעלות-תרשיחא": "Ma'alot-Tarshiha",
    "קריית טבעון": "Kiryat Tivon",
    "גבעת שמואל": "Givat Shmuel",
    "באקה אל-גרביה": "Baqa al-Gharbiyye",
    "טירת כרמל": "Tirat Carmel",
    "כרמיאל": "Karmiel",
    "שדרות": "Sderot",
    "אופקים": "Ofakim",
    "נתיבות": "Netivot",
    "רהט": "Rahat",
    "כפר יונה": "Kfar Yona",
    "טירה": "Tira",
    "כפר קאסם": "Kafr Qasim",
    "קלנסווה": "Qalansawe",
    "עראבה": "Arraba",
    "מגאר": "Maghar",
    "ניר יצחק": "Nir Yitzhak",
    "גן שמואל": "Gan Shmuel",
    "בית אורן": "Beit Oren",
    "שדה ניצן": "Sde Nitzan",
    "כפר חב\"ד": "Kfar Chabad",
    "אבו גוש": "Abu Ghosh",
    "בנימינה-גבעת עדה": "Binyamina-Givat Ada",
    "קדימה-צורן": "Kadima-Tzoran",
    "הוד הכרמל": "Hod HaCarmel",
    "עין מאהל": "Ein Mahil",
    "משהד": "Mashhad",
    "עיילבון": "Eilabun",
    "כאבול": "Kabul",
    "אעבלין": "I'billin",
    "טורעאן": "Tur'an",
    "כפר כנא": "Kafr Kanna",
    "כפר מנדא": "Kafr Manda",
    "כפר קרע": "Kafr Qara",
    "ג'לג'וליה": "Jaljulia",
    "ירכא": "Yarka",
    "ג'וליס": "Julis",
    "חורפיש": "Hurfeish",
    "בית ג'ן": "Beit Jann",
    "פקיעין (בוקייעה)": "Peki'in",
    "מזרעה": "Mazra'a",
    "ג'סר א-זרקא": "Jisr az-Zarqa",
    "פוריידיס": "Fureidis",
    "זמר": "Zemer",
    "לקיה": "Lakiya",
    "חורה": "Hura",
    "כסיפה": "Kuseife",
    "ערערה-בנגב": "Ar'ara BaNegev",
    "ערערה": "Ar'ara",
    "תל שבע": "Tel Sheva",
    "שגב-שלום": "Segev Shalom",
    "עמנואל": "Emmanuel",
    "קרני שומרון": "Karnei Shomron",
    "אלפי מנשה": "Alfei Menashe",
    "אורנית": "Oranit",
    "בית אריה": "Beit Aryeh",
    "עמיקם": "Amikam",
    "מג'דל שמס": "Majdal Shams",
    "נעורים": "Ne'urim",
    "אתגר": "Etgar",
    "טפחות": "Tefahot",
    "מיתר": "Meitar",
    "להבים": "Lehavim",
    "עומר": "Omer",
    "מעגלים": "Ma'agalim",
    "פוריה - כפר עבודה": "Poria - Kfar Avoda",
    "פוריה - נווה עובד": "Poria - Neve Oved",
    "שוהם": "Shoham",
    "אבן יהודה": "Even Yehuda",
    "גדרה": "Gedera",
    "גן יבנה": "Gan Yavne",
    "מזכרת בתיה": "Mazkeret Batya",
    "קריית עקרון": "Kiryat Ekron",
    "באר יעקב": "Be'er Ya'akov",
    "אזור": "Azor",
    "בית דגן": "Beit Dagan",
    "כפר שמריהו": "Kfar Shmaryahu",
    "סביון": "Savyon",
    "תל מונד": "Tel Mond",
    "פרדסיה": "Pardesiya",
    "צור יגאל": "Tzur Yigal",
    "כוכב יאיר": "Kokhav Ya'ir",
    "מטולה": "Metula",
    "ראש פינה": "Rosh Pinna",
    "יסוד המעלה": "Yesud HaMa'ala",
    "קצרין": "Katzrin",
    "בוקעאתא": "Buq'ata",
    "מסעדה": "Mas'ade",
    "ע'ג'ר": "Ghajar",
    "גזר": "Gezer",
    # --- hand additions for names absent from the 2022 CBS layer ---
    # regional councils (appear in rashuyot_panel)
    "שומרון": "Shomron RC",
    "מטה בנימין": "Mateh Binyamin RC",
    "מגילות ים המלח": "Megilot Dead Sea RC",
    "ערבות הירדן": "Arvot HaYarden RC",
    "גוש עציון": "Gush Etzion RC",
    "הר חברון": "Har Hevron RC",
    "חוף עזה": "Hof Aza RC",
    "נווה מדבר": "Neve Midbar RC",
    "אל קסום": "Al-Kasom RC",
    "אבו בסמה": "Abu Basma RC",
    # Hebron + evacuated Gaza/N. Samaria settlements (pre-2005 elections)
    "חברון": "Hebron",
    "נווה דקלים": "Neve Dekalim",
    "נצרים": "Netzarim",
    "כפר דרום": "Kfar Darom",
    "מורג": "Morag",
    "קטיף": "Katif",
    "גדיד": "Gadid",
    "גן אור": "Gan Or",
    "בדולח": "Bedolah",
    "רפיח ים": "Rafiah Yam",
    "כדים": "Kadim",
    "חומש": "Homesh",
    "גנים": "Ganim",
    "אלי סיני": "Elei Sinai",
    "ניסנית": "Nisanit",
    "בני עצמון": "Bnei Atzmon",
    "פאת שדה": "Pe'at Sadeh",
    "בת חצור": "Bat Hatzor",
    "מחנה יפה": "Camp Yafeh",
    "מחנה תל נוף": "Camp Tel Nof",
    "מחנה טלי": "Camp Tali",
    "מחנה יוכבד": "Camp Yokheved",
    "מחנה מרים": "Camp Miriam",
    "מחנה יהודית": "Camp Yehudit",
    "מחנה הילה": "Camp Hila",
    "מחנה עדי": "Camp Adi",
    # West Bank / Golan localities missing from the 2022 layer
    "מעלה שומרון": "Ma'ale Shomron",
    "חלמיש": "Halamish",
    "אפרתה": "Efrata",
    "נעורים": "Ne'urim",
    "נירן": "Niran",
    "עופרים": "Ofarim",
    "בית אל ב'": "Beit El B",
    "שער שומרון": "Sha'ar Shomron",
    "צופין": "Tzofim",
    "עין קיניה": "Ein Qiniya",
    "רג'ר": "Ghajar",
    "אבו עמאר": "Abu Amar",
    # Bedouin tribes / unrecognized villages (old CEC rows)
    "אבו ג'ווייעד": "Abu Juway'id",
    "אבו גווייעד": "Abu Juway'id",
    "אבו עבדון": "Abu Abdun",
    "אבו קורינאת": "Abu Qrenat",
    "אבו רובייעה": "Abu Rubay'a",
    "אבו רוקייק": "Abu Ruqayyeq",
    "אטרש": "Atrash",
    "אסד": "Asad",
    "אעצם": "A'sam",
    "ג'נאביב": "Janabib",
    "גנאביב": "Janabib",
    "הוואשלה": "Hawashla",
    "הוזייל": "Huzayyel",
    "נצאצרה": "Nasasra",
    "סייד": "Sayyid",
    "עוקבי": "Uqbi",
    "עוקבי (בנו עוקבה)": "Uqbi (Banu Uqba)",
    "עוקבי בנו עוקבה": "Uqbi (Banu Uqba)",
    "עטאוונה": "Atawneh",
    "קבועה": "Qabu'a",
    "קוואעין": "Qawa'in",
    "קודייראת א-צאנע": "Qudeirat as-Sana",
    "קדייראת א-צאנע": "Qudeirat as-Sana",
    "קודייראת אצאנעשבט": "Qudeirat as-Sana (tribe)",
    "תראבין א-צאנע": "Tarabin as-Sana",
    "תראבין אצאנע שבט": "Tarabin as-Sana (tribe)",
    "תראבין אצאנעישוב": "Tarabin as-Sana (locality)",
    "ח'ואלד": "Khawaled",
    "מסעודין אל-עזאזמה": "Mas'udin al-Azazme",
    "מסעודין אלעזאזמה": "Mas'udin al-Azazme",
    "סואעד (חמרייה)": "Sawa'id (Hamriyya)",
    "סואעד חמרייה": "Sawa'id (Hamriyya)",
    "סואעד-חמרייה": "Sawa'id (Hamriyya)",
    "סוואעד חמיירה": "Sawa'id (Hamriyya)",
    "סואעד (כמאנה)": "Sawa'id (Kamane)",
    "סואעד-כמאנה": "Sawa'id (Kamane)",
    "מולדה": "Molada",
    "דוחן": "Duhan",
    "ערוער": "Aroer",
    "ביידה": "Bayada",
    # Arab localities: old spellings / missing from 2022 layer
    "דבוריה": "Daburiyya",
    "עראמשה": "Arab al-Aramshe",
    "כאוכב אבו אל-היג'": "Kaokab Abu al-Hija",
    "כאוכב אל-היג'א": "Kaokab Abu al-Hija",
    "כעביה-טבאש-חג'אג'": "Ka'abiyye-Tabbash-Hajajre",
    "כעביה-טבאש": "Ka'abiyye-Tabbash",
    "חג'אג'רה": "Hajajre",
    "ברטעה": "Barta'a",
    "סאלם": "Salem",
    "מועאוויה": "Mu'awiya",
    "מוצמוץ": "Musmus",
    "מושיירפה": "Musheirifa",
    "זלפה": "Zalafa",
    "עין א-סהלה": "Ein as-Sahala",
    "אם אל-גנם": "Umm al-Ghanam",
    "אום אל-ג'נם": "Umm al-Ghanam",
    "שבלי - אום אל רנם": "Shibli-Umm al-Ghanam",
    "טובה-זנגריה": "Tuba-Zangariyye",
    "טובא-זנגריה": "Tuba-Zangariyye",
    "גוש חלב (ג'יש)": "Gush Halav (Jish)",
    "עיר כרמל": "Ir HaCarmel",
    "עירון": "Iron",
    "בסמ\"ה": "Basma",
    "בסמה": "Basma",
    "ג'סאר א-זרקא": "Jisr az-Zarqa",
    "ג'סר אל-זרקא": "Jisr az-Zarqa",
    "בוקעאתה": "Buq'ata",
    "זובידאת": "Zubeidat",
    "אבן יצחק (גלעד)": "Even Yitzhak (Gal'ed)",
    "אבן יצחק": "Even Yitzhak (Gal'ed)",
    # Jewish localities: renamed / merged / dissolved / old spellings
    "חמד": "Hemed",
    "אילניה": "Ilaniya",
    "שומריה": "Shomriya",
    "ספסופה": "Safsufa",
    "שיזפון": "Shizafon",
    "חצרות יסף": "Hatzrot Yasaf",
    "חצר בארותיים": "Hatzar Be'erotayim",
    "חצרות חולדה": "Hatzrot Hulda",
    "חצרות חפר": "Hatzrot Hefer",
    "חצרות כ\"ח": "Hatzrot Koah",
    "בן שמן-כפר הנוער": "Ben Shemen Youth Village",
    "כפר סולד": "Kfar Szold",
    "לי-און": "Li-On",
    "פעמי תש\"ז": "Pa'amei Tashaz",
    "פעמי תשז": "Pa'amei Tashaz",
    "כפר רוזנואלד": "Kfar Rosenwald (Zar'it)",
    "ניצנה": "Nitzana",
    "קציר-חריש": "Katzir-Harish",
    "באקה-ג'ת": "Baqa-Jatt",
    "שגור": "Shaghur",
    "שגב": "Segev",
    "מכבים-רעות": "Maccabim-Re'ut",
    "בנימינה": "Binyamina",
    "גבעת עדה": "Givat Ada",
    "צורן": "Tzoran",
    "מודיעין": "Modi'in",
    "רמת אפעל": "Ramat Efal",
    "אפעל": "Efal",
    "אפעל-בית אבות": "Efal (retirement home)",
    "נווה אפעל": "Neve Efal",
    "נווה אפרים": "Neve Efraim",
    "רמת פנקס": "Ramat Pinkas",
    "גני יהודה": "Ganei Yehuda",
    "כרם יבנה": "Kerem Yavne",
    "ניר דוד": "Nir David",
    "שעורים": "Se'orim",
    "נח\"ל שמעה": "Nahal Shim'a",
    "שושנת העמקים רסקו": "Shoshanat HaAmakim (Rasco)",
    "שושנת העמקים-רסקו": "Shoshanat HaAmakim (Rasco)",
    "פקיעין": "Peki'in",
    "כפר אז\"ר": "Kfar Azar",
    "אלי על": "Eli Al",
    "סואעד )חמרייה()שב": "Sawa'id (Hamriyya) (tribe)",
    "סואעד )כמאנה( )שב": "Sawa'id (Kamane) (tribe)",
    "סואעד (כמאנה) (שב": "Sawa'id (Kamane) (tribe)",
}

# ---------------------------------------------------------------- parties (hand map)
# Every distinct party display name that appears in parties_national.json /
# party_analysis.json / party_system.json across K13-K25. Era names included.
PARTY_EN = {
    # Right
    "ליכוד": "Likud",
    "הליכוד": "Likud",
    "צומת": "Tzomet",
    "התחיה": "Tehiya",
    "מולדת": "Moledet",
    "חרות": "Herut",
    "האיחוד הלאומי": "National Union",
    "איחוד לאומי": "National Union",
    "איחוד לאומי-מפדל": "National Union-Mafdal",
    "מפד\"ל": "Mafdal (NRP)",
    "המפד\"ל": "Mafdal (NRP)",
    "הבית היהודי": "The Jewish Home",
    "ימינה": "Yamina",
    "הימין החדש": "New Right",
    "הציונות הדתית": "Religious Zionism",
    "עוצמה יהודית": "Otzma Yehudit",
    "ישראל בעלייה": "Yisrael BaAliyah",
    "ישראל ביתנו": "Yisrael Beiteinu",
    "כולנו": "Kulanu",
    "גשר": "Gesher",
    "קדימה": "Kadima",
    "התנועה": "Hatnua",
    "יש עתיד": "Yesh Atid",
    "כחול לבן": "Blue and White",
    "תקווה חדשה": "New Hope",
    "מפלגת המרכז": "Center Party",
    "הדרך השלישית": "Third Way",
    "שינוי": "Shinui",
    "גיל (גמלאים)": "Gil (Pensioners)",
    "גיל": "Gil (Pensioners)",
    "העבודה": "Labor",
    "עבודה": "Labor",
    "עבודה-גשר": "Labor-Gesher",
    "עבודה-גשר-מרצ": "Labor-Gesher-Meretz",
    "ישראל אחת": "One Israel",
    "עם אחד": "One Nation",
    "מרצ": "Meretz",
    "מרץ": "Meretz",
    "המחנה הציוני": "Zionist Union",
    "המחנה הממלכתי": "National Unity",
    "ש\"ס": "Shas",
    # NOTE: bare שס is deliberately NOT here — it's the ballot CODE (display name is ש"ס);
    # keeping it out of the map leaves the code untouched as a join key everywhere.
    "יהדות התורה": "United Torah Judaism",
    "אגודת ישראל": "Agudat Yisrael",
    "דגל התורה": "Degel HaTorah",
    "נעם": "Noam",
    "חד\"ש": "Hadash",
    "בל\"ד": "Balad",
    "רע\"מ": "Ra'am",
    "רע\"מ-תע\"ל": "Ra'am-Ta'al",
    "רע\"מ-בל\"ד": "Ra'am-Balad",
    "תע\"ל": "Ta'al",
    "הרשימה המשותפת": "The Joint List",
    "הרשימה הערבית המאוחדת": "United Arab List",
    "מד\"ע": "Mada (Arab Democratic Party)",
    "חד\"ש-תע\"ל": "Hadash-Ta'al",
    "חד\"ש-בל\"ד": "Hadash-Balad",
    "אחר": "Other",
    "אחרות": "Other",
    # second sweep — every remaining Hebrew name in parties_national/party_analysis/party_system
    "איחוד מפלגות הימין": "Union of Right-Wing Parties",
    "ברית לאומית מתקדמת": "Progressive National Alliance",
    "גמלאים": "Pensioners (Gil)",
    "הירוקים-מימד": "Greens-Meimad",
    "הליכוד ישראל ביתנו": "Likud Yisrael Beiteinu",
    "המחנה הדמוקרטי": "Democratic Union",
    "המפלגה הליברלית החדשה": "New Liberal Party",
    "העבודה-גשר": "Labor-Gesher",
    "העבודה-גשר-מרצ": "Labor-Gesher-Meretz",
    "הרשימה המתקדמת לשלום": "Progressive List for Peace",
    "זהות": "Zehut",
    "יחד": "Yachad",
    "ישראל ביתנו-האיחוד הלאומי": "Yisrael Beiteinu-National Union",
    "מד\"ע-רע\"מ": "Mada-Ra'am",
    "עוצמה לישראל": "Otzma LeYisrael",
}

# Data-borne label/caveat strings (socioeconomic.json field labels, meta notes shown in UI)
MISC_EN = {
    "מדד חברתי-כלכלי 2021": "Socioeconomic index 2021",
    "% משפחות עם 4+ ילדים": "% families with 4+ children",
    "% בעלי תואר אקדמי": "% with academic degree",
    "ממוצע שנות לימוד": "Avg. years of schooling",
    "הכנסה חודשית לנפש": "Monthly income per capita",
    "גיל חציוני": "Median age",
    "% מקבלי הבטחת הכנסה": "% receiving income support",
    "יישוב": "Locality",
    "יחס תלות": "Dependency ratio",
    "מועצה מקומית": "Local council",
    "מועצה אזורית": "Regional council",
    "עירייה": "Municipality",
    "חילוני": "Secular",
    "מסורתי": "Traditional",
    "דתי/ דתי מאוד": "Religious / very religious",
    "דתי": "Religious",
    "חרדי": "Haredi",
    # CBS 2022 census religion values (statarea_2022.json) — without these they
    # fall to transliteration, and נוצרים collides with the locality נצרים
    "יהודים": "Jews",
    "מוסלמים": "Muslims",
    "נוצרים": "Christians",
    "דרוזים": "Druze",
    "דת אחרת": "Other religion",
    "לא הצביעו": "Did not vote",
    "מעטפות חיצוניות": "Double-envelope ballots",
    "ס\"ה מעטפות חיצוניות": "Total double-envelope ballots",
    "מעטפות כפולות": "Double envelopes",
    # bloc labels shipped as data values (vote_transfers labels etc.)
    "ימין": "Right",
    "חרדים": "Haredim",
    "מרכז": "Center",
    "שמאל": "Left",
    "ערבים": "Arabs",
    "ימין אופוזיציוני": "Opposition right",
    "שמאל (מרכז-שמאל)": "Left (center-left)",
    # SES tercile labels (vote_transfers_ses.json)
    "שליש תחתון (השכלה)": "Bottom third (education)",
    "שליש אמצעי": "Middle third",
    "שליש עליון (השכלה)": "Top third (education)",
    "באקה אל גרבייה (באקה אל ררבי": "Baqa al-Gharbiyye",
    "ימין אופוזיציוני (מרכז לצורך חישוב הגושים, החל מהכנסת ה-21)":
        "Opposition right (counted with the center bloc from the 21st Knesset on)",
    "ימין אופוזיציוני (מרכז לצורך חישוב הגושים, בכנסת ה-24)":
        "Opposition right (counted with the center bloc in the 24th Knesset)",
    "ימין אופוזיציוני (מרכז לצורך חישוב הגושים)":
        "Opposition right (counted with the center bloc)",
    "לא עברה את אחוז החסימה (נכללת בחישוב הגוש)":
        "Did not cross the electoral threshold (included in bloc totals)",
    "אקולוגי: אגרגטים יישוביים, לא פרטים.":
        "Ecological: locality-level aggregates, not individuals.",
    "אחוז אקדמאים: בסיס בני 15+ בהגדרת הלמס, אינטרפולציה ליניארית בין מפקדים.":
        "% academics: CBS definition, ages 15+; linear interpolation between censuses.",
    "מדדים חברתיים-כלכליים מתוקננים לכל שנתון בנפרד — השוואה בין שנים ביחידות יחסיות (rel_sd) בלבד.":
        "Socioeconomic indices are standardized per vintage — compare across years only in relative units (rel_sd).",
    "מדגם המפקד 1972-2008: יישובים בני ~2,000+ בחלק מהמשתנים; אל תסיקו על יישובים קטנים.":
        "1972–2008 census sample: localities of ~2,000+ residents for some variables; do not infer about small localities.",
    "מדדים אקולוגיים (רמת יישוב) — לא להסיק על מצביע יחיד (כשל אקולוגי).":
        "Ecological metrics (locality level) — do not infer about individual voters (ecological fallacy).",
    "פרופיל חברתי-כלכלי מבוסס על 201 עיריות (ללא מועצות אזוריות → הטיית בחירה).":
        "Socioeconomic profile based on 201 municipalities (regional councils excluded → selection bias).",
    "מפלגות עוקבות לפי אות הרשימה; חלק מהאותיות עברו למפלגות-המשך (למשל כן).":
        "Parties are tracked by ballot letter; some letters passed to successor parties (e.g. כן).",
    "מתאמים ופרופיל משוקללים במספר הקולות הכשרים ביישוב.":
        "Correlations and profiles are weighted by each locality's valid votes.",
    "מתאם 'כל היישובים' מערבב יישובים יהודיים וערביים ולכן מבלבל מפלגות יהודיות — ראו טור 'יישובים יהודיים'.":
        "The 'all localities' correlation mixes Jewish and Arab localities and thus confounds Jewish-party correlations — see the 'Jewish localities' column.",
    "פרופיל מתוקנן = הפרש (מפלגה − ממוצע) ביחידות סטיית-תקן.":
        "Standardized profile = (party − mean) difference in standard-deviation units.",
    "בתצוגה לפי בחירות: המאפיינים החברתיים-כלכליים הם צילום עדכני קבוע (~2021, דת 2019) גם לבחירות היסטוריות — ההצבעה משתנה, מאפייני היישוב לא. פרשנות לאחור בזהירות.":
        "In by-election view: the socioeconomic attributes are a fixed modern snapshot (~2021, religion 2019) even for historical elections — the vote changes, the locality attributes do not. Interpret backwards with caution.",
    "CBS annual local-authority profiles (הרשויות המקומיות בישראל), one file per year 1999-2024":
        "CBS annual local-authority profiles (Local Authorities in Israel), one file per year 1999-2024",
}

def ballot_codes():
    """Party ballot-letter codes are JOIN KEYS (national/national_votes/parties_by_locality,
    WINNER_COLORS/PARTY_ALIASES in page code) — they must never be translated."""
    codes = set()
    with open(os.path.join(ROOT, "data", "parties_national.json"), encoding="utf-8") as f:
        pn = json.load(f)
    for v in pn.values():
        for p in v.get("party_list", []):
            if p.get("code"):
                codes.add(p["code"])
        for key in ("national", "national_votes"):
            codes.update(k for k in (v.get(key) or {}))
    return codes

# Election display names (core.json election_name + UI pills)
def election_names():
    m = {}
    with open(os.path.join(ROOT, "data", "core.json"), encoding="utf-8") as f:
        core = json.load(f)
    src = core.get("elections") or core  # tolerate either shape
    for k, v in (src.items() if isinstance(src, dict) else []):
        if isinstance(v, dict) and isinstance(v.get("election_name"), str):
            he = v["election_name"]
            en = he.replace("כנסת", "Knesset").replace("א", "A").replace("ב", "B")
            m[he] = en
    # parties_national.json also carries election_name
    with open(os.path.join(ROOT, "data", "parties_national.json"), encoding="utf-8") as f:
        pn = json.load(f)
    for k, v in pn.items():
        he = v.get("election_name")
        if isinstance(he, str) and HEB.search(he):
            en = he.replace("כנסת", "Knesset").replace("(2019א)", "(2019 Apr)").replace("(2019ב)", "(2019 Sep)")
            m[he] = en
    return m

# ---------------------------------------------------------------- transliteration fallback
TRANSLIT = [
    ("תשׁ", "tesh"), ("שׁ", "sh"), ("ש", "sh"), ("צ'", "ch"), ("ץ'", "ch"), ("ג'", "j"), ("ז'", "zh"),
    ("א", ""), ("ב", "b"), ("ג", "g"), ("ד", "d"), ("ה", "h"), ("ו", "v"), ("ז", "z"),
    ("ח", "kh"), ("ט", "t"), ("י", "y"), ("כ", "k"), ("ך", "kh"), ("ל", "l"), ("מ", "m"),
    ("ם", "m"), ("נ", "n"), ("ן", "n"), ("ס", "s"), ("ע", "'"), ("פ", "p"), ("ף", "f"),
    ("צ", "tz"), ("ץ", "tz"), ("ק", "k"), ("ר", "r"), ("ת", "t"), ("\"", ""), ("'", "'"),
]
def transliterate(s):
    for he, en in TRANSLIT:
        s = s.replace(he, en)
    return title_case(s)

# ---------------------------------------------------------------- scan data JSONs
def hebrew_strings(obj, bag):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, str) and HEB.search(k):
                bag[k] += 1
            hebrew_strings(v, bag)
    elif isinstance(obj, list):
        for v in obj:
            hebrew_strings(v, bag)
    elif isinstance(obj, str) and HEB.search(obj):
        bag[obj] += 1

def main():
    print("extracting CBS names...")
    cbs = cbs_pairs()
    loc_map = {he: title_case(en) for he, en in cbs.items()}
    loc_map.update(CITY_OVERRIDES)

    # normalized index for fuzzy matches (strip space/hyphen/quote, normalize finals)
    def norm(s):
        s = re.sub(r"[\s\-'\"()׳״־]", "", s)  # incl. geresh/gershayim/maqaf
        return s.translate(str.maketrans("ךםןףץ", "כמנפצ"))
    norm_idx = {}
    for he in list(loc_map):
        norm_idx.setdefault(norm(he), he)
    # consonant skeleton (drop matres lectionis ו/י too): catches קרית vs קריית,
    # דליה vs דלייה, מעין vs מעיין. Only unique skeletons are used.
    def skel(s):
        return norm(s).replace("ו", "").replace("י", "")
    skel_counts = collections.Counter(skel(he) for he in loc_map)
    skel_idx = {}
    for he in list(loc_map):
        k = skel(he)
        if skel_counts[k] == 1:
            skel_idx[k] = he

    elec = election_names()
    # Codes that are ALSO display names (e.g. מרצ) get translated EVERYWHERE
    # (data keys+values AND page-source literals) so joins stay consistent;
    # pure codes are excluded everywhere. Partial translation is the only hazard.
    codes = ballot_codes()
    collisions = sorted(c for c in codes if c in PARTY_EN or c in loc_map or c in MISC_EN)
    codes -= set(collisions)

    # scan all data files for Hebrew strings
    bag = collections.Counter()
    data_dir = os.path.join(ROOT, "data")
    files = [os.path.join(data_dir, f) for f in os.listdir(data_dir)
             if f.endswith(".json") and ".bak" not in f and "prelocalities" not in f
             and f != "names_en.json"]
    files.append(os.path.join(ROOT, "findings_data.json"))
    for fp in files:
        with open(fp, encoding="utf-8") as f:
            try:
                obj = json.load(f)
            except Exception as e:
                print("skip", fp, e); continue
        hebrew_strings(obj, bag)

    def lookup(s):
        """exact -> norm -> skeleton; returns (en, via) or None."""
        if s in loc_map:
            return loc_map[s], "exact"
        if norm(s) in norm_idx:
            return loc_map[norm_idx[norm(s)]], "norm"
        if skel(s) in skel_idx:
            return loc_map[skel_idx[skel(s)]], "skel"
        return None

    # unique-prefix index for CEC 17-char-truncated names (e.g. "אשדות יעקב  (איחו")
    all_norm_keys = [norm(he) for he in loc_map]
    def prefix_unique(s):
        n = norm(s)
        if len(n) < 8:
            return None
        hits = [k for k in all_norm_keys if k.startswith(n)]
        if len(set(hits)) == 1:
            return loc_map[norm_idx[hits[0]]] if hits[0] in norm_idx else None
        return None

    # classify
    localities_out, uncovered, fuzzy_added = {}, [], []
    skipped_codes = []
    for s, cnt in bag.most_common():
        if s in codes:
            skipped_codes.append((s, cnt))
            continue
        if s in PARTY_EN or s in elec or s in MISC_EN:
            continue
        hit = lookup(s)
        if hit:
            localities_out[s] = hit[0]
            if hit[1] != "exact":
                fuzzy_added.append((s, hit[1], hit[0]))
            continue
        # bedouin (שבט)/(ישוב) suffix variants: strip and retry
        base = re.sub(r"[\s()]*(שבט|ישוב|יישוב)[\s()]*$", "", s).strip()
        if base != s:
            hit = lookup(base)
            if hit:
                suffix = " (tribe)" if "שבט" in s else ""
                localities_out[s] = hit[0] + suffix
                fuzzy_added.append((s, "suffix:" + hit[1], localities_out[s]))
                continue
        # CEC-truncated names: unique-prefix match
        pfx = prefix_unique(s)
        if pfx:
            localities_out[s] = pfx
            fuzzy_added.append((s, "prefix", pfx))
            continue
        uncovered.append((s, cnt))

    # transliteration fallback for uncovered strings that LOOK like locality names
    # (short, no digits) — everything else goes to the report for hand triage.
    translit_used = []
    still_uncovered = []
    for s, cnt in uncovered:
        if len(s) <= 25 and not re.search(r"\d", s) and "\n" not in s:
            localities_out[s] = transliterate(s)
            translit_used.append((s, localities_out[s], cnt))
        else:
            still_uncovered.append((s, cnt))

    out = {
        "meta": {
            "source": "CBS statistical_areas_2022.geojson SHEM_YISHUV_ENGLISH + hand maps",
            "built_by": "analysis/build_english_names.py",
            "n_localities": len(localities_out),
            "n_parties": len(PARTY_EN),
            "n_translit_fallback": len(translit_used),
            "code_collisions_translated": collisions,
        },
        "localities": localities_out,
        "parties": PARTY_EN,
        "misc": MISC_EN,
        "elections": elec,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=0)

    with open(REPORT, "w", encoding="utf-8") as f:
        f.write(f"CBS pairs: {len(cbs)}\n")
        f.write(f"ballot codes excluded everywhere: {len(codes)}\n")
        f.write(f"code<->name collisions (translated everywhere): {collisions}\n")
        f.write(f"codes skipped in data scan: {sorted(set(s for s,_ in skipped_codes))}\n")
        f.write(f"locality entries used by data: {len(localities_out)}\n")
        f.write(f"fuzzy-matched (norm): {len(fuzzy_added)}\n")
        for s, src, en in fuzzy_added:
            f.write(f"  FUZZY {s}  ->  {src}  ->  {en}\n")
        f.write(f"\ntransliteration fallback ({len(translit_used)}):\n")
        for s, en, cnt in sorted(translit_used, key=lambda x: -x[2]):
            f.write(f"  TRANSLIT [{cnt}] {s}  ->  {en}\n")
        f.write(f"\nSTILL UNCOVERED ({len(still_uncovered)}):\n")
        for s, cnt in still_uncovered:
            f.write(f"  [{cnt}] {s[:120]}\n")
    print("wrote", OUT)
    print("report:", REPORT)

if __name__ == "__main__":
    main()
