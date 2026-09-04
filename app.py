import datetime

import streamlit as st

from kundali_core import compute_kundali, search_places
from chart_draw import draw_north_indian, draw_south_indian
from compatibility import compute_compatibility_notes, compute_group_compatibility
from chat_assistant import build_system_prompt, ask_llm

st.set_page_config(page_title="Kundali Generator", page_icon="🔯", layout="centered")

st.title("🔯 Kundali Generator")
st.caption("Vedic (Jyotish) birth charts — sidereal positions, Lahiri ayanamsa")

# --- Sidebar: API key for the chat assistant ---
with st.sidebar:
    st.header("Chat assistant setup")
    provider_label = st.radio(
        "Chat provider",
        ["Google Gemini (free)", "Anthropic Claude (paid)"],
        key="provider_label",
    )

    if provider_label.startswith("Google"):
        st.session_state["provider"] = "gemini"
        st.markdown(
            "Get a free key (no credit card, no expiration) from "
            "[Google AI Studio](https://aistudio.google.com/apikey)."
        )
        st.session_state["api_key"] = st.text_input(
            "Google Gemini API key", type="password", key="gemini_api_key_input"
        )
        st.session_state["model_name"] = st.text_input(
            "Model", value="gemini-2.5-flash", key="gemini_model_input"
        )
    else:
        st.session_state["provider"] = "anthropic"
        st.markdown(
            "Requires a funded [Anthropic API key](https://console.anthropic.com/settings/keys)."
        )
        st.session_state["api_key"] = st.text_input(
            "Anthropic API key", type="password", key="anthropic_api_key_input"
        )
        st.session_state["model_name"] = st.text_input(
            "Model", value="claude-sonnet-5", key="anthropic_model_input"
        )

    st.caption("Your key is used only in this browser session and never stored.")


def render_add_person(prefix: str, container, add_label: str = "Add person"):
    """
    Renders an 'add a person' entry form (not a st.form, so a place search
    can populate a dropdown of candidate cities before the person confirms
    and adds). Appends a computed kundali result to
    st.session_state[prefix] (a list) when confirmed.
    """
    counter = st.session_state.get(f"{prefix}_counter", 0)
    ns = f"{prefix}_{counter}"  # unique key namespace, bumped after each add so fields reset

    name = container.text_input("Name", key=f"{ns}_name")
    c1, c2 = container.columns(2)
    dob = c1.date_input(
        "Date of birth", value=datetime.date(1995, 1, 1),
        min_value=datetime.date(1900, 1, 1), max_value=datetime.date(2100, 1, 1),
        key=f"{ns}_dob",
    )
    tob = c2.time_input("Time of birth", value=datetime.time(12, 0), key=f"{ns}_tob")

    place_mode = container.radio(
        "Place of birth",
        ["Search by place name", "Enter latitude / longitude / timezone manually"],
        horizontal=True, key=f"{ns}_mode",
    )

    lat = lon = tz_name = None

    if place_mode == "Search by place name":
        pc1, pc2 = container.columns([3, 1])
        query = pc1.text_input("City, Country (e.g. 'Jaipur, India')", key=f"{ns}_query")
        if pc2.button("Search", key=f"{ns}_search_btn", use_container_width=True):
            try:
                with container.spinner("Searching..."):
                    candidates = search_places(query, limit=6)
                st.session_state[f"{ns}_candidates"] = candidates
            except Exception as e:
                container.error(f"Search failed: {e}")
                st.session_state.pop(f"{ns}_candidates", None)

        candidates = st.session_state.get(f"{ns}_candidates")
        if candidates:
            options = [c["display_name"] for c in candidates]
            chosen_label = container.selectbox(
                "Confirm the correct place (please check this carefully - many places share a name)",
                options, key=f"{ns}_choice",
            )
            chosen = candidates[options.index(chosen_label)]
            lat, lon, tz_name = chosen["lat"], chosen["lon"], chosen["tz_name"]
            container.caption(f"✓ Using lat {lat:.4f}, lon {lon:.4f}, timezone {tz_name}")
    else:
        c1, c2, c3 = container.columns(3)
        lat = c1.number_input("Latitude", value=28.6139, format="%.4f", key=f"{ns}_lat")
        lon = c2.number_input("Longitude", value=77.2090, format="%.4f", key=f"{ns}_lon")
        tz_name = c3.text_input("Timezone (IANA)", value="Asia/Kolkata", key=f"{ns}_tz")

    if container.button(add_label, key=f"{ns}_add_btn", type="primary", use_container_width=True):
        if not name:
            container.error("Please enter a name.")
        elif lat is None or lon is None or not tz_name:
            container.error("Please search and confirm a place (or enter coordinates) first.")
        else:
            try:
                dt_local = datetime.datetime.combine(dob, tob)
                result = compute_kundali(name, dt_local, lat, lon, tz_name)
                st.session_state.setdefault(prefix, [])
                st.session_state[prefix].append(result)
                st.session_state[f"{prefix}_counter"] = counter + 1
                st.session_state.pop(f"{ns}_candidates", None)
                st.session_state["chat_history"] = []  # roster changed, reset chat
                st.rerun()
            except Exception as e:
                container.error(f"Could not compute chart: {e}")


def render_person_summary(prefix: str, container):
    """Lists added people with a remove button and an expander with their charts."""
    people = st.session_state.get(prefix, [])
    for i, r in enumerate(people):
        row = container.container(border=True)
        rc1, rc2 = row.columns([5, 1])
        rc1.markdown(
            f"**{r['name']}** — Asc {r['ascendant']['rashi']}, "
            f"Moon {r['moon_sign']} ({r['moon_nakshatra']})"
        )
        if rc2.button("Remove", key=f"{prefix}_remove_{i}"):
            people.pop(i)
            st.session_state["chat_history"] = []
            st.rerun()

        with row.expander("View charts & planetary positions"):
            tab1, tab2 = st.tabs(["North Indian", "South Indian"])
            with tab1:
                st.pyplot(draw_north_indian(r, title=f"{r['name']} — North Indian"), use_container_width=True)
            with tab2:
                st.pyplot(draw_south_indian(r, title=f"{r['name']} — South Indian"), use_container_width=True)

            rows = []
            for pname in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
                pdata = r["planets"][pname]
                rows.append({
                    "Planet": pname, "Sign": pdata["rashi"],
                    "Degree": f"{pdata['longitude'] % 30:.2f}°",
                    "House": pdata["house"],
                    "Retrograde": "Yes" if pdata["retrograde"] else "No",
                })
            st.dataframe(rows, use_container_width=True, hide_index=True)
            st.caption(
                f"Ayanamsa (Lahiri): {r['ayanamsa']:.4f}°  |  "
                f"Birth (UTC): {r['birth_datetime_utc'].strftime('%Y-%m-%d %H:%M:%S')}"
            )


# --- Group A ---
st.subheader("👤 Group A")
st.caption("Add one person, or a whole family — each birth chart is computed and shown below.")
render_add_person("group_a", st, add_label="Add person to Group A")
render_person_summary("group_a", st)

# --- Group B (optional) ---
st.divider()
with st.expander("💞 Compare with another person or family (Group B, optional)"):
    st.caption(
        "Add people here to unlock comparison questions in the chat — e.g. comparing a "
        "family of 3 with another family of 3. Nadi/Gana/Bhakoot are computed for every "
        "Group A × Group B pair automatically."
    )
    render_add_person("group_b", st, add_label="Add person to Group B")
    render_person_summary("group_b", st)

group_a = st.session_state.get("group_a", [])
group_b = st.session_state.get("group_b", [])

if not group_a:
    st.info("Add at least one person to Group A above to get started.")
else:
    # --- Compatibility snapshot, if Group B has members ---
    group_compat_text = ""
    if group_b:
        group_compat_text = compute_group_compatibility(group_a, group_b)
        st.divider()
        st.subheader("🔍 Compatibility snapshot")
        st.text(group_compat_text)

    # --- Chat ---
    st.divider()
    st.subheader("💬 Ask about these charts")
    st.caption(
        "Ask about career, marriage, wealth, health, or anything else — or, with Group B "
        "added, ask how specific people or the two groups compare."
    )

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    question = st.chat_input("e.g. 'How does our family compare with theirs for marriage?'")
    if question:
        if not st.session_state.get("api_key"):
            st.error("Add your API key in the sidebar first.")
        else:
            st.session_state["chat_history"].append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        system_prompt = build_system_prompt(
                            group_a, group_b=group_b, group_compat_text=group_compat_text,
                        )
                        reply = ask_llm(
                            provider=st.session_state.get("provider", "gemini"),
                            api_key=st.session_state["api_key"],
                            system_prompt=system_prompt,
                            chat_history=st.session_state["chat_history"],
                            model=st.session_state.get("model_name") or "gemini-2.5-flash",
                        )
                    except Exception as e:
                        reply = f"Sorry, something went wrong calling the API: {e}"
                st.markdown(reply)

            st.session_state["chat_history"].append({"role": "assistant", "content": reply})
