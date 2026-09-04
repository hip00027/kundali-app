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

## Files
- `app.py` — Streamlit UI (add-person flow, city-confirmation dropdown, Group A/B, chat)
- `kundali_core.py` — astronomical/astrological calculations (pyswisseph) + place search
- `chart_draw.py` — matplotlib drawing for both chart styles
- `compatibility.py` — Nadi/Gana/Bhakoot compatibility indicators, single-pair and group-vs-group
- `chat_assistant.py` — builds chart context (house significations, multi-person/group
  comparison context) + calls the chat API
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
