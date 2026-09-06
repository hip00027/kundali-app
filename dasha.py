"""
dasha.py
Vimshottari Mahadasha (planetary period) calculation - the classical Jyotish
system for timing life events, based purely on the Moon's exact nakshatra
position at birth. Unlike Ashtakoot compatibility tables, this is a single,
universally-agreed, mechanical formula - not something that varies between
classical sources - so it can be computed with confidence.

Approximation note: dasha lengths are converted from years to calendar dates
using 365.25 days/year (the standard approximation used by nearly all Jyotish
software). This can drift by roughly a day or two per decade compared to
sources using a different year-length convention - fine for identifying
which period someone is in, not a substitute for a professional's exact
calculation if a decision hinges on a specific day.
"""

import datetime

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

# Fixed cyclic order of the 9 Vimshottari dasha lords, and each one's total
# years in the 120-year cycle. This order and these year-counts are the
# single classical standard (Ketu 7, Venus 20, Sun 6, Moon 10, Mars 7,
# Rahu 18, Jupiter 16, Saturn 19, Mercury 17 = 120).
DASHA_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
DASHA_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}
TOTAL_CYCLE_YEARS = sum(DASHA_YEARS.values())  # 120
DAYS_PER_YEAR = 365.25

NAKSHATRA_SPAN = 360.0 / 27.0  # 13°20'


def _start_lord_for_moon(moon_longitude: float) -> int:
    """Each nakshatra is ruled by a fixed dasha lord, cycling through the
    9-lord order 3 times over the 27 nakshatras (nakshatra index % 9)."""
    nak_index = int(moon_longitude // NAKSHATRA_SPAN) % 27
    return nak_index % 9


def _add_years(dt: datetime.datetime, years: float) -> datetime.datetime:
    return dt + datetime.timedelta(days=years * DAYS_PER_YEAR)


def compute_mahadasha_timeline(moon_longitude: float, birth_datetime_utc: datetime.datetime) -> list:
    """
    Returns a list of {lord, start, end} dicts (datetimes in UTC) covering
    one full Vimshottari cycle from birth - the first entry is a partial
    period (whatever balance remained of that lord's dasha at birth), the
    remaining 8 are full periods, covering roughly the next 100+ years.
    """
    start_idx = _start_lord_for_moon(moon_longitude)
    start_lord = DASHA_ORDER[start_idx]

    # Fraction of the birth nakshatra already elapsed determines how much of
    # the starting Mahadasha's balance remains at birth.
    position_in_nakshatra = moon_longitude % NAKSHATRA_SPAN
    fraction_elapsed = position_in_nakshatra / NAKSHATRA_SPAN
    fraction_remaining = 1.0 - fraction_elapsed
    first_period_years = DASHA_YEARS[start_lord] * fraction_remaining

    timeline = []
    cursor = birth_datetime_utc
    end = _add_years(cursor, first_period_years)
    timeline.append({"lord": start_lord, "start": cursor, "end": end})
    cursor = end

    for i in range(1, 9):
        lord = DASHA_ORDER[(start_idx + i) % 9]
        years = DASHA_YEARS[lord]
        end = _add_years(cursor, years)
        timeline.append({"lord": lord, "start": cursor, "end": end})
        cursor = end

    return timeline


def compute_antardashas(mahadasha_entry: dict) -> list:
    """
    Subdivides one Mahadasha into its 9 Antardashas (sub-periods). The
    sequence always starts with the Mahadasha's own lord, then continues in
    the standard cyclic order; each Antardasha's share of the Mahadasha's
    total span is proportional to that lord's years in the 120-year cycle
    (this proportional-subdivision rule is the standard method, applied
    consistently regardless of whether the Mahadasha itself is a partial
    birth period or a full one).
    """
    lord = mahadasha_entry["lord"]
    start_idx = DASHA_ORDER.index(lord)
    total_span = (mahadasha_entry["end"] - mahadasha_entry["start"]).total_seconds()

    antardashas = []
    cursor = mahadasha_entry["start"]
    for i in range(9):
        sub_lord = DASHA_ORDER[(start_idx + i) % 9]
        fraction = DASHA_YEARS[sub_lord] / TOTAL_CYCLE_YEARS
        span_seconds = total_span * fraction
        end = cursor + datetime.timedelta(seconds=span_seconds)
        antardashas.append({"lord": sub_lord, "start": cursor, "end": end})
        cursor = end

    return antardashas


def find_active_period(timeline: list, at_datetime: datetime.datetime):
    """Returns the entry from a Mahadasha or Antardasha list that contains at_datetime,
    or None if it falls outside the timeline's range."""
    for entry in timeline:
        if entry["start"] <= at_datetime < entry["end"]:
            return entry
    return None


def build_dasha_summary(result: dict, as_of: datetime.datetime = None) -> str:
    """
    result: a compute_kundali() output.
    as_of: UTC datetime to evaluate "current" period against (defaults to now).
    Returns a text block describing the full Mahadasha timeline, the current
    Mahadasha and Antardasha, and the next couple of upcoming Antardashas -
    ready to drop into the chat's system prompt.
    """
    as_of = as_of or datetime.datetime.now(datetime.timezone.utc)
    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=datetime.timezone.utc)

    moon_lon = result["planets"]["Moon"]["longitude"]
    birth_utc = result["birth_datetime_utc"]
    if birth_utc.tzinfo is None:
        birth_utc = birth_utc.replace(tzinfo=datetime.timezone.utc)

    timeline = compute_mahadasha_timeline(moon_lon, birth_utc)

    lines = [f"VIMSHOTTARI MAHADASHA TIMELINE for {result['name']} (approximate, ±1-2 days/decade)"]
    lines.append("Full sequence from birth (one 120-year cycle):")
    for entry in timeline:
        lines.append(
            f"  {entry['lord']}: {entry['start'].strftime('%Y-%m-%d')} to {entry['end'].strftime('%Y-%m-%d')}"
        )

    current_maha = find_active_period(timeline, as_of)
    if current_maha is None:
        lines.append(f"\nAs of {as_of.strftime('%Y-%m-%d')}, this is outside the computed timeline "
                      f"(before birth or beyond ~120 years after the start of the birth nakshatra).")
        return "\n".join(lines)

    lines.append(
        f"\nCurrent Mahadasha (as of {as_of.strftime('%Y-%m-%d')}): {current_maha['lord']}, "
        f"running {current_maha['start'].strftime('%Y-%m-%d')} to {current_maha['end'].strftime('%Y-%m-%d')}"
    )

    antardashas = compute_antardashas(current_maha)
    current_antar = find_active_period(antardashas, as_of)
    lines.append(f"Antardasha breakdown within this Mahadasha ({current_maha['lord']}):")
    for a in antardashas:
        marker = "  <- CURRENT" if a is current_antar else ""
        lines.append(
            f"  {current_maha['lord']}-{a['lord']}: {a['start'].strftime('%Y-%m-%d')} "
            f"to {a['end'].strftime('%Y-%m-%d')}{marker}"
        )

    return "\n".join(lines)
