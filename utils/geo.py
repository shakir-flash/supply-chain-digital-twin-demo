# utils/geo.py
import numpy as np

def haversine_distance_miles(lat1, lon1, lat2, lon2):
    R = 3958.8  # miles
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2
    c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
    return float(R * c)

def service_days(distance_miles, avg_speed_mph=45.0, hours_per_day=8.0):
    hours = distance_miles / max(avg_speed_mph, 1.0)
    return max(1.0, hours / max(hours_per_day, 1.0))
