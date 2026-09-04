"""
compatibility.py
Computes the compatibility indicators between two charts that are purely
deterministic index/table lookups on Nakshatra and Rashi (no subjective
friendship-matrix tables), so the numbers are unambiguous:

- Gana (temperament group: Deva / Manushya / Rakshasa)
- Nadi (constitution group: Aadi / Madhya / Antya) - the single most-cited
  classical compatibility flag (matching Nadi is traditionally considered
  the most significant caution)
- Bhakoot (Moon-sign distance relationship: 6-8 / 2-12 / 5-9 patterns)

This intentionally does NOT compute a full 36-point Ashtakoot Guna Milan
score. Four of the eight classical koots (Varna, Vashya, Yoni, Graha Maitri)
depend on detailed friendship/animal-compatibility tables that vary slightly
between classical sources - rather than risk baking in a subtly wrong table
and presenting it as an authoritative number, this module sticks to the
parts that are unambiguous arithmetic, and leaves the fuller qualitative
picture to the chat assistant, which reasons over the real chart data.
"""

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

GANA = {
    "Deva": ["Ashwini", "Mrigashira", "Punarvasu", "Pushya", "Hasta", "Swati",
             "Anuradha", "Shravana", "Revati"],
    "Manushya": ["Bharani", "Rohini", "Ardra", "Purva Phalguni", "Uttara Phalguni",
                 "Purva Ashadha", "Uttara Ashadha", "Purva Bhadrapada", "Uttara Bhadrapada"],
    "Rakshasa": ["Krittika", "Ashlesha", "Magha", "Chitra", "Vishakha", "Jyeshtha",
                 "Mula", "Dhanishta", "Shatabhisha"],
}

NAKSHATRA_TO_GANA = {n: g for g, names in GANA.items() for n in names}

NADI_NAMES = ["Aadi", "Madhya", "Antya"]

RASHIS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def _nakshatra_index(name: str) -> int:
    return NAKSHATRAS.index(name)


def _nadi(nakshatra_name: str) -> str:
    return NADI_NAMES[_nakshatra_index(nakshatra_name) % 3]


def _gana_note(gana1: str, gana2: str) -> str:
    if gana1 == gana2:
        return "same Gana - traditionally considered the smoothest temperament match"
    pair = {gana1, gana2}
    if pair == {"Deva", "Manushya"}:
        return "Deva/Manushya - generally considered a workable, moderate match"
    if pair == {"Deva", "Rakshasa"}:
        return "Deva/Rakshasa - traditionally considered a more challenging temperament mismatch"
    if pair == {"Manushya", "Rakshasa"}:
        return "Manushya/Rakshasa - traditionally considered a more challenging temperament mismatch"
    return "mismatched Gana"


def _bhakoot_note(sign1: int, sign2: int) -> str:
    # distance counted forward from sign1 to sign2, 1-12
    forward = ((sign2 - sign1) % 12) + 1
    backward = ((sign1 - sign2) % 12) + 1
    pair = {forward, backward}
    if pair == {6, 8}:
        return "6-8 (Shadashtak) relationship - traditionally the most cautioned Bhakoot pattern"
    if pair == {2, 12}:
        return "2-12 (Dwirdwadash) relationship - traditionally considered a mild caution, often for finances/family"
    if pair == {5, 9}:
        return "5-9 (Nav-Pancham) relationship - traditionally considered a mild caution"
    return "no classical Bhakoot caution pattern between these Moon signs"


def compute_compatibility_notes(result1: dict, result2: dict) -> dict:
    """
    result1, result2: outputs of kundali_core.compute_kundali()
    Returns a dict of comparison data plus a ready-to-use text summary.
    """
    nak1, nak2 = result1["moon_nakshatra"], result2["moon_nakshatra"]
    gana1, gana2 = NAKSHATRA_TO_GANA[nak1], NAKSHATRA_TO_GANA[nak2]
    nadi1, nadi2 = _nadi(nak1), _nadi(nak2)
    sign1, sign2 = result1["planets"]["Moon"]["sign"], result2["planets"]["Moon"]["sign"]

    nadi_dosha = nadi1 == nadi2
    gana_note = _gana_note(gana1, gana2)
    bhakoot_note = _bhakoot_note(sign1, sign2)

    summary_lines = [
        f"{result1['name']}: Moon in {RASHIS[sign1]}, Nakshatra {nak1} (Gana: {gana1}, Nadi: {nadi1})",
        f"{result2['name']}: Moon in {RASHIS[sign2]}, Nakshatra {nak2} (Gana: {gana2}, Nadi: {nadi2})",
        f"Nadi: {'SAME (' + nadi1 + ') - traditionally the single most-cautioned factor (Nadi Dosha)' if nadi_dosha else nadi1 + ' vs ' + nadi2 + ' - different, traditionally favorable on this factor'}",
        f"Gana match: {gana_note}",
        f"Bhakoot (Moon-sign relationship): {bhakoot_note}",
        "Note: this covers Nadi, Gana and Bhakoot only - three of the eight classical "
        "Ashtakoot koots (chosen because they're unambiguous index lookups). It is not "
        "a full 36-point Guna Milan score; Varna, Vashya, Yoni and Graha Maitri are left "
        "for qualitative discussion since those tables vary between classical sources.",
    ]

    return {
        "nakshatra_1": nak1, "nakshatra_2": nak2,
        "gana_1": gana1, "gana_2": gana2,
        "nadi_1": nadi1, "nadi_2": nadi2,
        "nadi_dosha": nadi_dosha,
        "gana_note": gana_note,
        "bhakoot_note": bhakoot_note,
        "summary_text": "\n".join(summary_lines),
    }
