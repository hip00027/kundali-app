import datetime

import streamlit as st

from kundali_core import compute_kundali, geocode_place
from chart_draw import draw_north_indian, draw_south_indian
from compatibility import compute_compatibility_notes
from chat_assistant import build_system_prompt, ask_claude

st.set_page_config(page_title="Kundali Generator", page_icon="🔯", layout="centered")

st.title("🔯 Kundali Generator")
st.caption("Vedic (Jyotish) birth chart — sidereal positions, Lahiri ayanamsa")

# --- Sidebar: API key for the chat assistant ---
with st.sidebar:
    st.header("Chat assistant setup")
    st.markdown(
        "To ask questions about your chart in the chat box below, enter an "
        "[Anthropic API key](https://console.anthropic.com/settings/keys). "
        "It's used only in your browser session and never stored."
    )
    api_key = st.text_input("Anthropic API key", type="password", key="api_key")
    model_name = st.text_input("Model", value="claude-sonnet-5", key="model_name")


def _birth_details_form(form_key, defaults=None):
    """Renders a birth-details form and returns (submitted, name, dt_local, lat, lon, tz_name) or None."""
    defaults = defaults or {}
    with st.form(form_key):
        name = st.text_input("Name", value=defaults.get("name", ""), key=f"{form_key}_name")

        col1, col2 = st.columns(2)
        with col1:
            birth_date = st.date_input(
                "Date of birth", value=defaults.get("date", datetime.date(1995, 1, 1)),
                min_value=datetime.date(1900, 1, 1), max_value=datetime.date(2100, 1, 1),
                key=f"{form_key}_date",
            )
        with col2:
            birth_time = st.time_input(
                "Time of birth", value=defaults.get("time", datetime.time(12, 0)),
                key=f"{form_key}_time",
            )

        st.markdown("**Place of birth**")
        place_mode = st.radio(
            "How do you want to enter the location?",
            ["Search by place name", "Enter latitude / longitude / timezone manually"],
            horizontal=True, label_visibility="collapsed", key=f"{form_key}_place_mode",
        )

        place_name, lat_in, lon_in, tz_in = None, None, None, None
        if place_mode == "Search by place name":
            place_name = st.text_input("City, Country (e.g. 'Jaipur, India')", key=f"{form_key}_place_name")
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                lat_in = st.number_input("Latitude", value=28.6139, format="%.4f", key=f"{form_key}_lat")
            with c2:
                lon_in = st.number_input("Longitude", value=77.2090, format="%.4f", key=f"{form_key}_lon")
            with c3:
                tz_in = st.text_input("Timezone (IANA)", value="Asia/Kolkata", key=f"{form_key}_tz")

        submit_label = defaults.get("submit_label", "Generate Kundali")
        submitted = st.form_submit_button(submit_label, use_container_width=True)

    if not submitted:
        return None

    try:
        if place_mode == "Search by place name":
            if not place_name:
                st.error("Please enter a place name.")
                return None
            with st.spinner("Looking up location..."):
                lat, lon, tz_name = geocode_place(place_name)
        else:
            if not tz_in:
                st.error("Please enter a timezone.")
                return None
            lat, lon, tz_name = lat_in, lon_in, tz_in

        dt_local = datetime.datetime.combine(birth_date, birth_time)
        result = compute_kundali(name or "Native", dt_local, lat, lon, tz_name)
        return result, lat, lon, tz_name
    except Exception as e:
        st.error(f"Could not compute chart: {e}")
        return None


# --- Primary birth details form ---
primary = _birth_details_form("primary")
if primary is not None:
    result, lat, lon, tz_name = primary
    st.session_state["result"] = result
    st.session_state["location_note"] = f"lat {lat:.4f}, lon {lon:.4f}, timezone {tz_name}"
    st.session_state["chat_history"] = []  # reset chat when a new chart is generated
    st.session_state.pop("result2", None)  # a fresh primary chart clears any prior comparison

# --- Render chart + chat if we have a computed result (persists across chat reruns) ---
if "result" in st.session_state:
    result = st.session_state["result"]

    st.success(f"Location resolved to {st.session_state['location_note']}")

    # --- Summary ---
    s1, s2, s3 = st.columns(3)
    s1.metric("Ascendant (Lagna)", result["ascendant"]["rashi"])
    s2.metric("Moon Sign (Rashi)", result["moon_sign"])
    s3.metric("Nakshatra", f"{result['moon_nakshatra']} (pada {result['moon_pada']})")

    # --- Charts ---
    tab1, tab2 = st.tabs(["North Indian Chart", "South Indian Chart"])
    with tab1:
        fig_n = draw_north_indian(result, title=f"{result['name']} — North Indian")
        st.pyplot(fig_n, use_container_width=True)
    with tab2:
        fig_s = draw_south_indian(result, title=f"{result['name']} — South Indian")
        st.pyplot(fig_s, use_container_width=True)

    # --- Planet table ---
    st.subheader("Planetary Positions")
    rows = []
    for pname in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
        pdata = result["planets"][pname]
        deg_in_sign = pdata["longitude"] % 30
        rows.append({
            "Planet": pname,
            "Sign": pdata["rashi"],
            "Degree": f"{deg_in_sign:.2f}°",
            "House": pdata["house"],
            "Retrograde": "Yes" if pdata["retrograde"] else "No",
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)

    st.caption(
        f"Ayanamsa (Lahiri): {result['ayanamsa']:.4f}°  |  "
        f"Birth (UTC): {result['birth_datetime_utc'].strftime('%Y-%m-%d %H:%M:%S')}"
    )

    # --- Optional: add a second chart to compare / check compatibility ---
    st.divider()
    with st.expander("💞 Compare with someone else's chart (partner, family, business, etc.)"):
        st.caption(
            "Add a second person's birth details to unlock compatibility questions in the "
            "chat below — the assistant will compare both charts, and a few deterministic "
            "indicators (Nadi, Gana, Bhakoot) are computed automatically."
        )
        secondary = _birth_details_form("secondary", defaults={"submit_label": "Add this person"})
        if secondary is not None:
            result2, lat2, lon2, tz2 = secondary
            st.session_state["result2"] = result2
            st.session_state["chat_history"] = []  # reset chat so it picks up the new context
            st.rerun()

        if "result2" in st.session_state:
            result2 = st.session_state["result2"]
            notes = compute_compatibility_notes(result, result2)
            st.session_state["compat_notes"] = notes

            st.success(f"Comparing with **{result2['name']}**")
            c1, c2, c3 = st.columns(3)
            c1.metric(f"{result2['name']}'s Ascendant", result2["ascendant"]["rashi"])
            c2.metric(f"{result2['name']}'s Moon Sign", result2["moon_sign"])
            c3.metric(f"{result2['name']}'s Nakshatra", result2["moon_nakshatra"])
            st.text(notes["summary_text"])

            if st.button("Remove comparison"):
                st.session_state.pop("result2", None)
                st.session_state.pop("compat_notes", None)
                st.session_state["chat_history"] = []
                st.rerun()

    # --- Chat ---
    st.divider()
    st.subheader("💬 Ask about this chart")
    st.caption(
        "Ask about career, marriage, wealth, health, or anything else in the chart — "
        "or, if you've added a second person above, ask how the two charts compare."
    )

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    question = st.chat_input("e.g. 'How do our charts compare for marriage?'")
    if question:
        if not st.session_state.get("api_key"):
            st.error("Add your Anthropic API key in the sidebar first.")
        else:
            st.session_state["chat_history"].append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        system_prompt = build_system_prompt(
                            result,
                            result2=st.session_state.get("result2"),
                            compatibility_notes=st.session_state.get("compat_notes"),
                        )
                        reply = ask_claude(
                            api_key=st.session_state["api_key"],
                            system_prompt=system_prompt,
                            chat_history=st.session_state["chat_history"],
                            model=st.session_state.get("model_name") or "claude-sonnet-5",
                        )
                    except Exception as e:
                        reply = f"Sorry, something went wrong calling the API: {e}"
                st.markdown(reply)

            st.session_state["chat_history"].append({"role": "assistant", "content": reply})

else:
    st.info("Fill in the birth details above and click **Generate Kundali**.")
