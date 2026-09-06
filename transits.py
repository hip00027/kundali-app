"""
transits.py
Current planetary transits (Gochar) mapped onto a natal chart, plus Sade
Sati status. Unlike dasha.py's clean formula, this module does direct
numerical lookups against the same Swiss Ephemeris engine used for natal
charts - so accuracy depends only on the ephemeris itself, not on any
external table.
"""

import datetime
import swisseph as swe

from kundali_core import RASHIS, _compute_planets_for_jd, jd_from_utc, _sign_index

SLOW_MOVERS = ["Saturn", "Jupiter", "Rahu", "Ketu"]  # the ones usually discussed in transit analysis


def current_transits(at_datetime: datetime.datetime = None) -> dict:
    """Returns sidereal sign/longitude/retrograde for all 9 grahas at a given
    UTC moment (defaults to right now)."""
    at_datetime = at_datetime or datetime.datetime.now(datetime.timezone.utc)
    jd_ut = jd_from_utc(at_datetime)
    return _compute_planets_for_jd(jd_ut), at_datetime


def _house_from_natal(natal_asc_sign: int, transit_sign: int) -> int:
    return ((transit_sign - natal_asc_sign) % 12) + 1


def sade_sati_phase(natal_moon_sign: int, saturn_sign: int) -> str:
    """
    Sade Sati = Saturn transiting the 12th, 1st, or 2nd sign counted from the
    natal Moon sign. Returns the phase name, or None if not in Sade Sati.
    """
    diff = (saturn_sign - natal_moon_sign) % 12
    if diff == 11:
        return "Rising phase (Saturn in the 12th from natal Moon)"
    if diff == 0:
        return "Peak phase (Saturn transiting the natal Moon sign itself)"
    if diff == 1:
        return "Setting phase (Saturn in the 2nd from natal Moon)"
    return None


def _saturn_sign_on(dt_utc: datetime.datetime) -> int:
    jd_ut = jd_from_utc(dt_utc)
    pos, _ = swe.calc_ut(jd_ut, swe.SATURN, swe.FLG_SIDEREAL | swe.FLG_SWIEPH)
    return _sign_index(pos[0] % 360)


def find_sign_boundary(reference_dt: datetime.datetime, direction: int, max_days: int = 4000) -> datetime.datetime:
    """
    Scans day-by-day from reference_dt (forward if direction=1, backward if
    -1) to find the nearest date Saturn's sidereal sign changes. Saturn moves
    slowly (~2.5 years/sign) so a 1-day step is more than fine resolution,
    and max_days=4000 (~11 years) comfortably covers a full Sade Sati cycle
    in either direction.
    """
    start_sign = _saturn_sign_on(reference_dt)
    step = datetime.timedelta(days=1)
    cursor = reference_dt
    for _ in range(max_days):
        cursor = cursor + step * direction
        if _saturn_sign_on(cursor) != start_sign:
            return cursor
    return None  # shouldn't happen within max_days for Saturn


def build_transit_summary(result: dict, as_of: datetime.datetime = None) -> str:
    """
    result: a compute_kundali() output.
    Returns a text block with current transiting planet positions relative
    to this natal chart, and Sade Sati status if relevant - ready to drop
    into the chat's system prompt.
    """
    planets_now, as_of = current_transits(as_of)
    natal_asc_sign = result["ascendant"]["sign"]
    natal_moon_sign = result["planets"]["Moon"]["sign"]

    lines = [f"CURRENT TRANSITS (Gochar) for {result['name']}, as of {as_of.strftime('%Y-%m-%d')}"]
    lines.append("(transiting sign / house counted from this person's natal Ascendant):")
    for pname in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
        pdata = planets_now[pname]
        house = _house_from_natal(natal_asc_sign, pdata["sign"])
        retro = " (retrograde)" if pdata["retrograde"] and pname in SLOW_MOVERS else ""
        lines.append(f"  {pname}: transiting {pdata['rashi']}, natal house {house}{retro}")

    saturn_sign_now = planets_now["Saturn"]["sign"]
    phase = sade_sati_phase(natal_moon_sign, saturn_sign_now)
    if phase:
        try:
            phase_start = find_sign_boundary(as_of, direction=-1)
            phase_end = find_sign_boundary(as_of, direction=1)
            lines.append(
                f"\nSade Sati: currently ACTIVE - {phase}. Saturn entered this sign around "
                f"{phase_start.strftime('%Y-%m-%d')} and is expected to leave it around "
                f"{phase_end.strftime('%Y-%m-%d')} (dates approximate to the nearest day, and don't "
                f"account for retrograde stations, which can cause Saturn to briefly re-enter or "
                f"delay leaving a sign)."
            )
        except Exception:
            lines.append(f"\nSade Sati: currently ACTIVE - {phase}.")
    else:
        lines.append("\nSade Sati: not currently active for this person (Saturn is not transiting "
                      "the 12th, 1st, or 2nd sign from their natal Moon).")

    return "\n".join(lines)
