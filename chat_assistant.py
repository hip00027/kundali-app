"""
chat_assistant.py
Builds a text summary of one or two computed kundalis (for grounding the
chat) and sends chat messages to the Anthropic API.
"""

SYSTEM_PROMPT_HEADER = """You are a knowledgeable, level-headed Vedic astrology (Jyotish) assistant \
embedded in a kundali-generator app. You answer questions about the specific birth chart(s) \
given below - use them to ground every answer rather than speaking generically.

"""

HOUSE_SIGNIFICATIONS = """REFERENCE: HOUSE SIGNIFICATIONS (whole-sign houses, counted from the Ascendant)
For topical questions, check the relevant house(s), their sign, and any planets placed there \
or aspecting them:
- Career / profession: mainly the 10th house (karma, public standing, profession) and its \
sign/lord; also the 6th (job, service, competition) and 2nd (income from work). Saturn and \
the Sun are natural career significators (karakas); the Sun in/ruling the 10th, or Saturn \
well placed, often correlates with career discipline and public role.
- Marriage / relationships: mainly the 7th house (partnership, spouse) and its sign/lord; \
Venus is the natural significator of marriage/love for a male chart, Jupiter for a female \
chart in classical texts (modern practice often looks at both regardless of gender). Also \
check for planets placed in the 7th house or aspecting it, and the Moon's condition for \
emotional temperament in relationships.
- Wealth / finances: mainly the 2nd house (accumulated wealth, family resources, savings) \
and the 11th house (income, gains, fulfillment of desires); Jupiter is the natural \
significator of wealth/abundance, Venus of luxury and material comfort.
- Health: mainly the 6th house (disease, daily struggle) and the 1st house (the body/vitality) \
and its lord's condition.
- Family/home: 4th house (mother, home, emotional foundation, property).
- Children: 5th house.
- Siblings: 3rd house.
- Foreign travel/spirituality/luck: 9th (fortune, higher learning, father) and 12th (loss, \
foreign lands, spirituality, expenditure).

When a question touches one of these topics, name the relevant house(s), what sign occupies \
it (from the ascendant given below), and any planets placed there for this specific chart, \
then interpret using standard Jyotish principles (own sign/exalted/debilitated, benefic vs \
malefic occupancy, retrograde, etc.) rather than giving a generic answer.

"""

COMPATIBILITY_GUIDANCE = """REFERENCE: COMPARING CHARTS ACROSS GROUPS / COMPATIBILITY QUESTIONS
One or more additional people's charts are included below (Group B), alongside a few \
deterministic compatibility indicators (Nadi, Gana, Bhakoot) computed for every person-in-A \
x person-in-B pair from their Moon nakshatras/signs. Use these as a starting point, and add \
qualitative discussion of the other classical dimensions (Varna, Vashya, Yoni, Graha Maitri \
- i.e. spiritual temperament, mutual attraction, instinctive/physical compatibility, and \
mental rapport based on the Moon-sign lords' relationship) using your own Jyotish knowledge \
applied to the actual Moon signs given. When asked to compare two specific named individuals \
(e.g. one person from each group), also compare their Ascendants and 7th houses for \
romantic/marital questions, or their 10th houses for professional/business questions - adapt \
which houses matter to the kind of relationship being asked about. When asked about two \
whole groups (e.g. "family vs family"), summarize the overall pattern across all the pairs \
rather than only picking one pair, and note which specific pairings look strongest or most \
cautioned.

Do NOT present a fabricated precise 36-point Guna Milan total - the app only computes three \
of the eight classical koots exactly (noted below); say so plainly if asked for a full \
score, and offer the qualitative read instead. Keep the framing as traditional symbolic \
compatibility patterns worth reflecting on, not a deterministic verdict on whether specific \
people should or shouldn't be together, or whether two families are "good" or "bad" matches \
- that judgment belongs to the people involved, not to a chart reading.

"""

GUIDELINES = """GUIDELINES
- Answer using standard Vedic astrology concepts (rashis, houses, nakshatras, dashas, \
yogas, retrograde/combust effects, etc.) as they apply to the chart(s) above.
- Be specific to the data given rather than generic.
- If asked about something this data doesn't cover (e.g. divisional charts, dasha \
periods/timing, transits, exact Mangal Dosha assessment), say plainly that it isn't in \
the current chart data, and answer at the level of general principles instead of \
inventing chart-specific claims.
- Keep the tone grounded and reflective rather than fatalistic - frame chart readings as \
traditional symbolic interpretations and possible tendencies, not guaranteed predictions, \
and not medical/financial/legal advice.
- Keep answers focused and conversational - a few short paragraphs unless the person asks \
for more detail.
"""


def _chart_block(result: dict, label: str = "") -> str:
    planet_lines = "\n".join(
        f"- {pname}: {pdata['rashi']}, house {pdata['house']}"
        + (" (retrograde)" if pdata["retrograde"] else "")
        for pname, pdata in result["planets"].items()
    )
    title = f"BIRTH CHART{' - ' + label if label else ''}"
    return (
        f"{title}\n{'-' * len(title)}\n"
        f"Name: {result['name']}\n"
        f"Birth date/time (local): {result['birth_datetime_local'].strftime('%Y-%m-%d %H:%M')}\n"
        f"Birth place: lat {result['lat']:.4f}, lon {result['lon']:.4f}, timezone {result['tz_name']}\n"
        f"Ayanamsa used: Lahiri ({result['ayanamsa']:.4f}°)\n"
        f"House system: whole-sign houses\n\n"
        f"Ascendant (Lagna): {result['ascendant']['rashi']}\n"
        f"Moon sign (Rashi): {result['moon_sign']}\n"
        f"Moon Nakshatra: {result['moon_nakshatra']} (pada {result['moon_pada']})\n\n"
        f"Planetary placements (sign / house / retrograde):\n{planet_lines}\n"
    )


def build_system_prompt(group_a: list, group_b: list = None, group_compat_text: str = "") -> str:
    """
    group_a: list of compute_kundali() results (e.g. one person, or a family)
    group_b: optional second list, for comparison questions
    group_compat_text: optional precomputed text from
        compatibility.compute_group_compatibility(group_a, group_b)
    """
    group_b = group_b or []
    parts = [SYSTEM_PROMPT_HEADER]

    label_a = "Group A" if len(group_a) > 1 else None
    for i, result in enumerate(group_a, start=1):
        label = f"Group A - {result['name']}" if label_a else ""
        parts.append(_chart_block(result, label=label))
        parts.append("\n")

    if group_b:
        label_b = "Group B" if len(group_b) > 1 else None
        for i, result in enumerate(group_b, start=1):
            label = f"Group B - {result['name']}" if label_b else ""
            parts.append(_chart_block(result, label=label))
            parts.append("\n")

        if group_compat_text:
            parts.append("\n" + group_compat_text + "\n")

        parts.append("\n" + HOUSE_SIGNIFICATIONS + COMPATIBILITY_GUIDANCE + GUIDELINES)
    else:
        parts.append("\n" + HOUSE_SIGNIFICATIONS + GUIDELINES)

    return "\n".join(parts)


def ask_claude(api_key: str, system_prompt: str, chat_history: list, model: str = "claude-sonnet-5") -> str:
    """
    chat_history: list of {"role": "user"|"assistant", "content": str}
    Returns the assistant's reply text.
    """
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system=system_prompt,
        messages=chat_history,
    )
    parts = [block.text for block in response.content if block.type == "text"]
    return "\n".join(parts).strip()


def ask_gemini(api_key: str, system_prompt: str, chat_history: list, model: str = "gemini-2.5-flash") -> str:
    """
    Same shape as ask_claude, but calls Google's Gemini API (which has a
    genuinely free, non-expiring tier - see README). Gemini expects the
    assistant role to be called "model" rather than "assistant".
    """
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    contents = [
        types.Content(
            role="model" if msg["role"] == "assistant" else "user",
            parts=[types.Part(text=msg["content"])],
        )
        for msg in chat_history
    ]
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=1024,
        ),
    )
    return (response.text or "").strip()


def ask_llm(provider: str, api_key: str, system_prompt: str, chat_history: list, model: str) -> str:
    """Routes to the chosen provider. provider is 'gemini' or 'anthropic'."""
    if provider == "gemini":
        return ask_gemini(api_key, system_prompt, chat_history, model=model)
    return ask_claude(api_key, system_prompt, chat_history, model=model)
