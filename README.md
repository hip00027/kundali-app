# Kundali Generator

A Vedic astrology (Jyotish) birth chart app. Enter a name, date/time, and
place of birth — it computes sidereal planetary positions (Lahiri ayanamsa)
using the Swiss Ephemeris and renders both a **North Indian (diamond)** and
**South Indian (box grid)** chart, plus a planetary position table. A **chat
box** underneath lets the person ask about their own chart — career, marriage,
wealth, health, whatever — grounded in their actual planetary positions, not
generic answers.

There's also an optional **"Compare with someone else's chart"** panel: add a
second person's birth details and the chat can then answer compatibility
questions ("how do our charts compare for marriage?", "are we a good business
match?"). Three deterministic compatibility indicators — Nadi, Gana, and
Bhakoot — are computed exactly from both Moon positions; the rest of the
compatibility picture is discussed qualitatively by the chat model itself
(see the note in `compatibility.py` on why it stops there — see below).

## Files
- `app.py` — Streamlit UI
- `kundali_core.py` — astronomical/astrological calculations (pyswisseph)
- `chart_draw.py` — matplotlib drawing for both chart styles
- `compatibility.py` — Nadi/Gana/Bhakoot compatibility indicators between two charts
- `chat_assistant.py` — builds chart context (incl. house significations for
  career/marriage/wealth, and comparison context when a second chart is added)
  + calls the Anthropic API for the chat box
- `requirements.txt` — dependencies

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

## The chat feature needs an API key
The chat box calls the Anthropic API directly, so each person using the app
needs to paste their own key into the sidebar ("Anthropic API key"). Get one
free to start at https://console.anthropic.com/settings/keys (new accounts
get a small free credit; after that it's pay-as-you-go, and a chat session
like this costs a fraction of a cent per message on Sonnet).

The key is only kept in that browser session's memory (`st.session_state`) —
it's never written to disk or logged. If you're deploying this for other
people to use (e.g. via Streamlit Cloud) and don't want each person to need
their own key, you can instead hardcode a key you control using
[Streamlit secrets](https://docs.streamlit.io/develop/concepts/connections/secrets-management)
and read it with `st.secrets["ANTHROPIC_API_KEY"]` in `app.py` — just be aware
that then you're paying for everyone's usage.

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
