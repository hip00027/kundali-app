# Kundali Generator

A Vedic astrology (Jyotish) birth chart app. Add a person's name, date/time,
and place of birth — it computes sidereal planetary positions (Lahiri
ayanamsa) using the Swiss Ephemeris and renders both a **North Indian
(diamond)** and **South Indian (box grid)** chart, plus a planetary position
table. A **chat box** underneath lets you ask about career, marriage,
wealth, health, or anything else, grounded in the actual chart(s) — not
generic answers.

**Multiple people, both sides.** "Group A" can hold one person or a whole
family (add as many as you like — a "family of 3" is just adding 3 people).
An optional "Group B" lets you add a second person or family to compare
against — e.g. comparing one family of 3 with another family of 3. Nadi,
Gana, and Bhakoot (three deterministic classical compatibility factors) are
computed automatically for every Group A × Group B pair, and the chat can
answer questions about any specific pairing or the overall pattern across
both groups.

**Confirming the right city.** When you search a place by name, the app
shows a dropdown of every matching location it found (many place names are
shared by multiple cities/towns worldwide) so you can pick the correct one
before it computes anything — instead of silently guessing the first result.

**Gender.** Each person has an optional Gender field. Classical Jyotish uses
different planets as the spouse significator depending on gender (Venus for
a male chart, Jupiter for a female chart), so this lets the chat apply the
correct one instead of guessing or ignoring it. It's optional — leave it as
"Prefer not to say" and the chat will just mention both possibilities.

**Reusing people.** Every person you add is automatically saved. A "📇 Saved
people" panel lets you add anyone you've entered before straight into Group
A or B with one click — no retyping birth details for someone you've already
added once. See the note on where this is stored below.

**Timing — Mahadasha, Antardasha, and current transits.** Beyond the static
birth chart, the app now computes each person's full Vimshottari Mahadasha
timeline (the classical planetary-period system - one full 120-year cycle
from birth), their current Antardasha breakdown, their real current
planetary transits mapped onto their natal houses, and their Sade Sati
status (with the actual date Saturn entered the relevant sign and when it's
expected to leave, found by scanning the ephemeris directly). This means the
chat can now answer genuine timing questions ("what period am I in", "is
this a hard year") with real computed dates, not just static personality-style
readings. See `dasha.py` and `transits.py` for exactly what is and isn't
covered.

## Files
- `app.py` — Streamlit UI (add-person flow, city-confirmation dropdown, Group A/B, chat)
- `kundali_core.py` — astronomical/astrological calculations (pyswisseph) + place search
- `chart_draw.py` — matplotlib drawing for both chart styles
- `compatibility.py` — Nadi/Gana/Bhakoot compatibility indicators, single-pair and group-vs-group
- `dasha.py` — Vimshottari Mahadasha/Antardasha timeline (deterministic, from the Moon's birth position)
- `transits.py` — current planetary transits mapped onto natal houses, and Sade Sati (computed
  directly from the ephemeris, not a lookup table)
- `chat_assistant.py` — builds chart context (house significations, gender-aware
  significators, timing guidance, multi-person/group comparison context) + calls the chat API
- `storage.py` — saves/loads people's birth details for reuse (see caveat below)
- `requirements.txt` — dependencies

## Note on timing accuracy
Two different confidence levels are worth knowing about:
- **Mahadasha/Antardasha dates** use a single, universally-agreed classical formula (unlike
  the compatibility koots), so the *sequence and proportions* are exactly right. The
  *calendar dates* carry a small, unavoidable approximation (±1-2 days per decade) from
  converting "years" to days using 365.25 days/year, which is the same convention nearly
  all Jyotish software uses.
- **Transits and Sade Sati boundary dates** are found by directly scanning the same Swiss
  Ephemeris engine used for the birth chart, so they're accurate to the day - except that
  the scan doesn't account for a planet briefly retrograding back across a sign boundary
  before finally moving on, which can shift a real-world "final" ingress date by weeks to
  months from what a single continuous scan reports. The app notes this caveat in its Sade
  Sati output.

Neither replaces a professional's exact calculation for a decision that hinges on a specific
day - but both are solid enough to answer "what period am I in" and "is this a heavier year"
questions with real dates instead of vague generalities.

## Note on saved people persisting
`storage.py` writes to a JSON file on the app's own server disk. That's
reliable while the app stays running (repeat visits, other people using the
same deployed link), but Streamlit Community Cloud's free tier can put an
inactive app to sleep and wipe its disk when it wakes back up — so a saved
list can occasionally reset. Use the "Export saved people" / "Import saved
people" buttons in the sidebar to keep a permanent backup file on your own
device; that one is unaffected by anything happening on the server.

## Note on the compatibility score
Classical Vedic matchmaking (Ashtakoot Guna Milan) scores 8 factors out of 36
points. This app computes 3 of them exactly (Nadi, Gana, Bhakoot) because
they're pure index arithmetic on the Moon's nakshatra/sign — no ambiguity.
The other 5 (Varna, Vashya, Yoni, Graha Maitri) depend on detailed
friendship/animal-compatibility tables that read slightly differently across
classical sources; rather than hard-code a table that might be subtly wrong
and present it as an authoritative number for a decision as significant as
marriage, the app leaves those to the chat model's own reasoning over the
real chart data, clearly framed as traditional interpretation rather than a
verdict. If you want a certified full 36-point score, a professional
astrologer or a dedicated matching tool is the more reliable source.

## The chat feature needs an API key — pick free or paid
The sidebar has a "Chat provider" switch:

- **Google Gemini (free)** — recommended if you just want this working at no
  cost. Get a key at [Google AI Studio](https://aistudio.google.com/apikey):
  no credit card, no expiration, roughly 1,500 requests/day on the free
  Flash models. Plenty for personal use.
- **Anthropic Claude (paid)** — get a key at
  [console.anthropic.com](https://console.anthropic.com/settings/keys).
  New accounts sometimes get a small starting credit, but there's no
  permanent free tier — after that it's pay-as-you-go (a chat message
  costs a fraction of a cent on Sonnet, so it's cheap, just not free).

Either way, the key is only kept in that browser session's memory
(`st.session_state`) — never written to disk or logged. If you're deploying
this for other people to use (e.g. via Streamlit Cloud) and don't want each
person to need their own key, you can instead hardcode a key you control
using [Streamlit secrets](https://docs.streamlit.io/develop/concepts/connections/secrets-management)
and read it with `st.secrets[...]` in `app.py` — just be aware that then
you're the one paying for / rate-limited by everyone's usage.

## Option A — Streamlit Community Cloud (free, permanent shareable link, recommended)
1. Create a free GitHub account if you don't have one, and a new repo.
2. Upload these 4 files (`app.py`, `kundali_core.py`, `chart_draw.py`, `requirements.txt`) to the repo.
3. Go to https://share.streamlit.io → "New app" → sign in with GitHub.
4. Pick your repo, branch, and `app.py` as the main file → Deploy.
5. You'll get a permanent public URL like `https://your-app.streamlit.app`.

This is free, has no time limit, and doesn't require you to keep a notebook open.

## Option B — Google Colab (free, but link only works while the notebook is running)
Paste this into a Colab cell (upload the 3 `.py` files to the Colab file panel first,
or paste their contents into cells that write the files):

```python
!pip install -q streamlit pyswisseph geopy timezonefinder pytz matplotlib pyngrok

# Upload app.py, kundali_core.py, chart_draw.py into the Colab session first
# (drag them into the Files panel on the left, or use files.upload())

from pyngrok import ngrok
ngrok.set_auth_token("YOUR_NGROK_AUTHTOKEN")  # free at https://dashboard.ngrok.com

import subprocess, time
subprocess.Popen(["streamlit", "run", "app.py", "--server.port", "8501", "--server.headless", "true"])
time.sleep(5)
public_url = ngrok.connect(8501)
print(public_url)
```

Click the printed URL. Note: it stops working the moment the Colab runtime
disconnects — good for testing, not for a permanent link (use Option A for that).

## Option C — Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Notes
- Uses the Moshier analytical ephemeris built into `pyswisseph` (no separate
  ephemeris data files needed) — accurate to about 1 arc-second, which is
  more than enough for chart generation.
- House system used: **whole-sign houses** (standard in Vedic astrology).
- Ayanamsa: **Lahiri**, the most widely used in Vedic astrology. To switch to
  another ayanamsa, change `swe.SIDM_LAHIRI` in `kundali_core.py` (e.g.
  `swe.SIDM_RAMAN`, `swe.SIDM_KRISHNAMURTI`).
- Nodes: uses the **Mean Node** for Rahu/Ketu (change to `swe.TRUE_NODE` in
  `kundali_core.py` if you prefer the true node).
- "Search by place name" needs internet access at runtime (it calls
  OpenStreetMap's free geocoder) — this works fine on Streamlit Cloud/Colab/locally,
  just not in a fully offline environment.
