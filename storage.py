"""
storage.py
Lightweight local persistence for saved birth details, so the same person's
information can be reused later (added to Group A or B again) without
retyping it.

CAVEAT: this writes to a JSON file on the app's own disk. On Streamlit
Community Cloud's free tier, that disk is only guaranteed to last while the
app stays "awake" - if it goes to sleep from inactivity and later wakes back
up, the file may be reset to empty. Use the Export/Import buttons in the app
to keep a permanent backup on your own device if you want saved people to
survive that.
"""

import json
import os

STORAGE_PATH = os.path.join(os.path.dirname(__file__), "saved_people.json")


def load_saved_people():
    if not os.path.exists(STORAGE_PATH):
        return []
    try:
        with open(STORAGE_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return []


def write_saved_people(people):
    try:
        with open(STORAGE_PATH, "w") as f:
            json.dump(people, f, indent=2)
    except Exception:
        pass  # best-effort - e.g. a read-only filesystem shouldn't crash the app


def _dedup_key(entry):
    return (
        entry.get("name"), entry.get("dob"), entry.get("tob"),
        round(entry.get("lat", 0), 4), round(entry.get("lon", 0), 4),
    )


def add_saved_person(entry: dict):
    """entry: dict with name, dob (YYYY-MM-DD str), tob (HH:MM str), lat, lon, tz_name, gender."""
    people = load_saved_people()
    key = _dedup_key(entry)
    if any(_dedup_key(p) == key for p in people):
        return people  # already saved, nothing to do
    people.append(entry)
    write_saved_people(people)
    return people


def merge_saved_people(new_people: list):
    """Used by Import: adds any entries not already present."""
    people = load_saved_people()
    existing_keys = {_dedup_key(p) for p in people}
    for entry in new_people:
        if _dedup_key(entry) not in existing_keys:
            people.append(entry)
            existing_keys.add(_dedup_key(entry))
    write_saved_people(people)
    return people


def delete_saved_person(index: int):
    people = load_saved_people()
    if 0 <= index < len(people):
        people.pop(index)
        write_saved_people(people)
    return people
