"""V32 — MT5 (Ava Trade) macro-instrument pooled panel model: FX majors/crosses, gold/silver, energies, equity indices, agri, bonds.
One pre-registered LightGBM on a pooled panel (Amendment V2.1). Data: local terminal D1, no purchase."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATASET_ID = "tm-mt5-MACRO-D1-20260905-000001"
DATA = os.path.join(ROOT, "data", "market", "immutable", DATASET_ID)
OUT = os.path.join(ROOT, "data", "market", "research_engine", "mt5_macro_v32")
CACHE = os.path.join(ROOT, "data", "market", "cn_a_share", "alpha_cache", "mt5_macro_v32")

# Universe fixed before pull: everything liquid and non-thematic in these groups. Thematic baskets (swap -9.59, spreads >1%) excluded.
GROUPS = ("Forex\\Majors", "Forex\\Crosses", "CFD-Metals", "CFD-Energies", "CFD-Agricultural", "CFD-Bonds")
INDICES = ("US_500", "US_2000", "US_30", "US_TECH100", "GERMANY_40", "UK_100", "FRANCE_40", "EUROPE_50", "JAPAN_225", "HK_50", "AUS_200",
           "SWISS_20", "ITALY_40", "NED_25", "CANADA_60", "CHINA_A50", "TAIWAN_INDX", "DOLLAR_INDX", "VIX")
EXCLUDE = ("CrudeTEST", "SPAIN35")  # test symbol; trade_mode 0


def ensure():
    for p in (DATA, OUT, CACHE):
        if not os.path.isdir(p):
            os.makedirs(p)
