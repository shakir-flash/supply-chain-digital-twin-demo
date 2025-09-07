# config.py
# Central knobs for the whole project

from pathlib import Path
import random
import numpy as np

# Reproducibility - set randomness to static
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# Project paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
CLEAN_DIR = DATA_DIR / "clean"
RESULTS_DIR = DATA_DIR / "results"
CHARTS_DIR = DATA_DIR / "charts"
for p in [DATA_DIR, RAW_DIR, CLEAN_DIR, RESULTS_DIR, CHARTS_DIR]:
    p.mkdir(parents=True, exist_ok=True)

# Synthetic dataset sizing
N_STORES = 120           # scalable parameter
N_WEEKS = 1              # demand is 1 week intervals
MAX_STORE_PER_METRO = 8  # cap stores per metro to keep transport matrix reasonable

# Transport cost parameters
BASE_RATE_PER_MILE = 0.30   # USD per unit per mile
HANDLING_USD = 2.0          # USD per unit per shipment
AVG_SPEED_MPH = 45.0        # for service time estimate (8h/day driving considered downstream)

# Demand & capacity distributions
STORE_WEEKLY_MEAN = 3200
STORE_WEEKLY_STD = 850
DC_WEEKLY_CAP_MEAN = 65000
DC_WEEKLY_CAP_STD = 12000
MIN_STORE_DEMAND = 700
MIN_DC_CAPACITY = 30000

FIG_DPI = 140   # DPI (resolution) for saved PNG charts

# -----------------------------
# Facility seeds (curated USA sites by type)
# Sources (for README, not used by code at runtime):
# - Direct Fulfillment Centers (DFCs): Locust Grove GA, Perris CA, Troy OH, Dallas TX, East Point GA
# - Flatbed Distribution (FDCs): Dallas TX, Sparrows Point MD
# - New/announced DCs for Pro focus: Detroit MI, Los Angeles CA, San Antonio TX, Toronto ON
# - Florida DC expansion: West Palm Beach, Miami, Fort Myers
# - This is not an exhaustive set.
# -----------------------------
FACILITY_SEEDS = [
    # Direct Fulfillment Centers (e-comm)
    {"dc_id": "DFC_LocustGrove_GA", "city": "Locust Grove", "state": "GA", "lat": 33.345, "lon": -84.104, "type": "DFC"},
    {"dc_id": "DFC_Perris_CA",      "city": "Perris",       "state": "CA", "lat": 33.782, "lon": -117.228, "type": "DFC"},
    {"dc_id": "DFC_Troy_OH",        "city": "Troy",         "state": "OH", "lat": 40.039, "lon": -84.203, "type": "DFC"},
    {"dc_id": "DFC_Dallas_TX",      "city": "Dallas",       "state": "TX", "lat": 32.776, "lon": -96.797, "type": "DFC"},
    {"dc_id": "DFC_EastPoint_GA",   "city": "East Point",   "state": "GA", "lat": 33.678, "lon": -84.439, "type": "DFC"},

    # Flatbed Distribution (building materials)
    {"dc_id": "FDC_Dallas_TX",          "city": "Dallas",         "state": "TX", "lat": 32.776, "lon": -96.797, "type": "FDC"},
    {"dc_id": "FDC_SparrowsPoint_MD",   "city": "Sparrows Point", "state": "MD", "lat": 39.218, "lon": -76.495, "type": "FDC"},

    # Pro-focused regional DCs (US subset)
    {"dc_id": "PRO_Detroit_MI",     "city": "Detroit",      "state": "MI", "lat": 42.331, "lon": -83.046, "type": "PRO_DC"},
    {"dc_id": "PRO_LosAngeles_CA",  "city": "Los Angeles",  "state": "CA", "lat": 34.054, "lon": -118.243, "type": "PRO_DC"},
    {"dc_id": "PRO_SanAntonio_TX",  "city": "San Antonio",  "state": "TX", "lat": 29.424, "lon": -98.494,  "type": "PRO_DC"},

    # Florida expansion DCs
    {"dc_id": "FL_WestPalmBeach_FL", "city": "West Palm Beach", "state": "FL", "lat": 26.715, "lon": -80.053, "type": "RDC"},
    {"dc_id": "FL_Miami_FL",         "city": "Miami",           "state": "FL", "lat": 25.762, "lon": -80.192, "type": "RDC"},
    {"dc_id": "FL_FortMyers_FL",     "city": "Fort Myers",      "state": "FL", "lat": 26.640, "lon": -81.872, "type": "RDC"},
]

# Major US metros to seed stores realistically
STORE_METROS = [
    # West
    {"metro": "Seattle-Tacoma, WA",   "lat": 47.606, "lon": -122.332, "region": "West"},
    {"metro": "Portland, OR",         "lat": 45.515, "lon": -122.679, "region": "West"},
    {"metro": "San Francisco, CA",    "lat": 37.774, "lon": -122.419, "region": "West"},
    {"metro": "Los Angeles, CA",      "lat": 34.054, "lon": -118.243, "region": "West"},
    {"metro": "San Diego, CA",        "lat": 32.716, "lon": -117.161, "region": "West"},
    {"metro": "Phoenix, AZ",          "lat": 33.448, "lon": -112.074, "region": "Southwest"},
    {"metro": "Las Vegas, NV",        "lat": 36.170, "lon": -115.140, "region": "Southwest"},
    {"metro": "Denver, CO",           "lat": 39.739, "lon": -104.990, "region": "Southwest"},

    # Midwest
    {"metro": "Minneapolis, MN",      "lat": 44.978, "lon": -93.265, "region": "Midwest"},
    {"metro": "Chicago, IL",          "lat": 41.878, "lon": -87.629, "region": "Midwest"},
    {"metro": "Detroit, MI",          "lat": 42.331, "lon": -83.046, "region": "Midwest"},
    {"metro": "Columbus, OH",         "lat": 39.961, "lon": -82.999, "region": "Midwest"},
    {"metro": "Cincinnati, OH",       "lat": 39.103, "lon": -84.512, "region": "Midwest"},
    {"metro": "St. Louis, MO",        "lat": 38.627, "lon": -90.199, "region": "Midwest"},

    # Northeast
    {"metro": "Boston, MA",           "lat": 42.360, "lon": -71.058, "region": "Northeast"},
    {"metro": "New York, NY",         "lat": 40.713, "lon": -74.006, "region": "Northeast"},
    {"metro": "Philadelphia, PA",     "lat": 39.952, "lon": -75.165, "region": "Northeast"},
    {"metro": "Baltimore, MD",        "lat": 39.290, "lon": -76.612, "region": "Northeast"},

    # Southeast
    {"metro": "Charlotte, NC",        "lat": 35.227, "lon": -80.843, "region": "Southeast"},
    {"metro": "Atlanta, GA",          "lat": 33.749, "lon": -84.388, "region": "Southeast"},
    {"metro": "Orlando, FL",          "lat": 28.538, "lon": -81.379, "region": "Southeast"},
    {"metro": "Tampa, FL",            "lat": 27.950, "lon": -82.457, "region": "Southeast"},
    {"metro": "Miami, FL",            "lat": 25.762, "lon": -80.192, "region": "Southeast"},

    # South/Central
    {"metro": "Dallas, TX",           "lat": 32.776, "lon": -96.797, "region": "South"},
    {"metro": "Houston, TX",          "lat": 29.760, "lon": -95.369, "region": "South"},
    {"metro": "San Antonio, TX",      "lat": 29.424, "lon": -98.494, "region": "South"},
    {"metro": "Austin, TX",           "lat": 30.267, "lon": -97.743, "region": "South"},
    {"metro": "Nashville, TN",        "lat": 36.162, "lon": -86.781, "region": "South"},
]
