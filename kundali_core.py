"""
kundali_core.py
Core Vedic (Jyotish) astrology calculations using pyswisseph.

Produces:
- Sidereal (Lahiri ayanamsa) longitudes for Sun, Moon, Mars, Mercury, Jupiter,
  Venus, Saturn, Rahu (mean node), Ketu
- Ascendant (Lagna)
- Rashi (zodiac sign) for each planet
- Nakshatra + pada for each planet
- Whole-sign house placement for each planet
"""

import datetime
import swisseph as swe

RASHIS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

RASHI_SHORT = ["Ar", "Ta", "Ge", "Cn", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", "Pi"]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

PLANET_IDS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
}

PLANET_ORDER = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]


def geocode_place(place_name: str):
    """Look up latitude/longitude/timezone for a place name, using the single
    best match. Kept for backward compatibility; prefer search_places() so
    the person can confirm which match is correct."""
    results = search_places(place_name, limit=1)
    r = results[0]
    return r["lat"], r["lon"], r["tz_name"]


def search_places(place_name: str, limit: int = 5):
    """Look up candidate places matching a name, so the person can confirm
    the right one (place names are often ambiguous - many cities share a
    name). Returns a list of dicts: display_name, lat, lon, tz_name.
    Raises ValueError if nothing is found."""
    from geopy.geocoders import Nominatim
    from timezonefinder import TimezoneFinder

    geolocator = Nominatim(user_agent="kundali_app")
    locations = geolocator.geocode(place_name, exactly_one=False, limit=limit, timeout=10)
    if not locations:
        raise ValueError(f"Could not find any location matching: {place_name}")

    tf = TimezoneFinder()
    results = []
    for loc in locations:
        tz_name = tf.timezone_at(lat=loc.latitude, lng=loc.longitude) or "UTC"
        results.append({
            "display_name": loc.address,
            "lat": loc.latitude,
            "lon": loc.longitude,
            "tz_name": tz_name,
        })
    return results


def _to_ut(dt_local: datetime.datetime, tz_name: str) -> datetime.datetime:
    """Convert a naive local datetime to UTC using an IANA timezone name."""
    import pytz
    tz = pytz.timezone(tz_name)
    localized = tz.localize(dt_local)
    return localized.astimezone(pytz.utc)


def _sign_index(longitude: float) -> int:
    return int(longitude // 30) % 12


def _nakshatra_info(moon_longitude: float):
    span = 360.0 / 27.0  # 13°20'
    idx = int(moon_longitude // span) % 27
    pada = int((moon_longitude % span) // (span / 4)) + 1
    return NAKSHATRAS[idx], pada


def compute_kundali(name: str, dt_local: datetime.datetime, lat: float, lon: float, tz_name: str,
                     gender: str = None):
    """
    Main entry point. Returns a dict with all computed chart data.
    dt_local: naive datetime in the birth location's local time.
    gender: optional, one of "Female"/"Male"/"Other/Prefer not to say" (or None).
        Used only to let the chat assistant apply gender-specific classical
        significators (e.g. Venus vs Jupiter as spouse karaka) - it does not
        change any of the astronomical/positional calculations below.
    """
    dt_ut = _to_ut(dt_local, tz_name)

    jd_ut = swe.julday(
        dt_ut.year, dt_ut.month, dt_ut.day,
        dt_ut.hour + dt_ut.minute / 60.0 + dt_ut.second / 3600.0,
    )

    swe.set_sid_mode(swe.SIDM_LAHIRI)
    ayanamsa = swe.get_ayanamsa_ut(jd_ut)

    # --- Ascendant (Lagna) ---
    # swe.houses_ex with sidereal flag gives sidereal cusps + ascendant directly
    cusps, ascmc = swe.houses_ex(jd_ut, lat, lon, b'W', flags=swe.FLG_SIDEREAL)
    asc_lon = ascmc[0] % 360
    asc_sign = _sign_index(asc_lon)

    # --- Planets ---
    planets = {}
    for pname, pid in PLANET_IDS.items():
        pos, _flag = swe.calc_ut(jd_ut, pid, swe.FLG_SIDEREAL | swe.FLG_SWIEPH | swe.FLG_SPEED)
        lon_ = pos[0] % 360
        speed = pos[3]
        planets[pname] = {
            "longitude": lon_,
            "sign": _sign_index(lon_),
            "retrograde": speed < 0,
        }

    # Rahu (mean lunar node) and Ketu (180 deg opposite)
    node_pos, _ = swe.calc_ut(jd_ut, swe.MEAN_NODE, swe.FLG_SIDEREAL | swe.FLG_SWIEPH)
    rahu_lon = node_pos[0] % 360
    ketu_lon = (rahu_lon + 180) % 360
    planets["Rahu"] = {"longitude": rahu_lon, "sign": _sign_index(rahu_lon), "retrograde": True}
    planets["Ketu"] = {"longitude": ketu_lon, "sign": _sign_index(ketu_lon), "retrograde": True}

    # --- Whole-sign houses (most common Vedic house system) ---
    for pname, pdata in planets.items():
        pdata["house"] = ((pdata["sign"] - asc_sign) % 12) + 1
        pdata["rashi"] = RASHIS[pdata["sign"]]

    # --- Nakshatra (based on Moon) ---
    moon_nakshatra, moon_pada = _nakshatra_info(planets["Moon"]["longitude"])

    return {
        "name": name,
        "gender": gender,
        "birth_datetime_local": dt_local,
        "birth_datetime_utc": dt_ut,
        "lat": lat,
        "lon": lon,
        "tz_name": tz_name,
        "ayanamsa": ayanamsa,
        "ascendant": {
            "longitude": asc_lon,
            "sign": asc_sign,
            "rashi": RASHIS[asc_sign],
        },
        "planets": planets,
        "moon_sign": RASHIS[planets["Moon"]["sign"]],
        "moon_nakshatra": moon_nakshatra,
        "moon_pada": moon_pada,
    }
