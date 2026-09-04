"""
chart_draw.py
Draws North Indian (diamond) and South Indian (box-grid) Kundali charts
as matplotlib figures, given the output of kundali_core.compute_kundali().
"""

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
from kundali_core import RASHIS, RASHI_SHORT

PLANET_ABBR = {
    "Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me",
    "Jupiter": "Ju", "Venus": "Ve", "Saturn": "Sa", "Rahu": "Ra", "Ketu": "Ke",
}

BG = "#fdfaf3"
LINE = "#3b2f2f"
TEXT = "#1f1f1f"
ASC_COLOR = "#b5482b"


def _planets_by_house(result):
    by_house = {h: [] for h in range(1, 13)}
    for pname, pdata in result["planets"].items():
        by_house[pdata["house"]].append(pname)
    return by_house


def _planets_by_sign(result):
    by_sign = {s: [] for s in range(12)}
    for pname, pdata in result["planets"].items():
        by_sign[pdata["sign"]].append(pname)
    return by_sign


# ---------------------------------------------------------------------------
# NORTH INDIAN CHART (fixed diamond layout; sign shown per house via ascendant)
# ---------------------------------------------------------------------------

def draw_north_indian(result, title="North Indian Chart"):
    asc_sign = result["ascendant"]["sign"]
    by_house = _planets_by_house(result)

    O = (2, 2)
    T, R, Bm, L = (2, 4), (4, 2), (2, 0), (0, 2)
    A, B, C, D = (0, 4), (4, 4), (4, 0), (0, 0)
    P1, P2, P4, P3 = (1, 3), (3, 3), (3, 1), (1, 1)  # midpoints of OA, OB, OC, OD

    # house_number -> (polygon points, label anchor)
    houses = {
        1: ([O, P1, T, P2], (2.0, 2.85)),
        2: ([T, B, P2], (2.75, 3.55)),
        3: ([B, R, P2], (3.55, 2.75)),
        4: ([O, P2, R, P4], (2.85, 2.0)),
        5: ([R, C, P4], (3.55, 1.25)),
        6: ([C, Bm, P4], (2.75, 0.45)),
        7: ([O, P4, Bm, P3], (2.0, 1.15)),
        8: ([Bm, D, P3], (1.25, 0.45)),
        9: ([D, L, P3], (0.45, 1.25)),
        10: ([O, P3, L, P1], (1.15, 2.0)),
        11: ([L, A, P1], (0.45, 2.75)),
        12: ([A, T, P1], (1.25, 3.55)),
    }

    # small offsets for the sign-number tag inside each house (near a corner)
    sign_tag_pos = {
        1: (2.0, 3.6), 2: (2.35, 3.85), 3: (3.75, 2.5), 4: (3.5, 2.0),
        5: (3.75, 1.5), 6: (2.35, 0.15), 7: (2.0, 0.4), 8: (1.65, 0.15),
        9: (0.25, 1.5), 10: (0.5, 2.0), 11: (0.25, 2.5), 12: (1.65, 3.85),
    }

    fig, ax = plt.subplots(figsize=(5.2, 5.2))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    # outer square + diagonals + inner diamond (the classic construction lines)
    ax.plot(*zip(A, B, C, D, A), color=LINE, linewidth=1.8)
    ax.plot(*zip(A, C), color=LINE, linewidth=1.2)
    ax.plot(*zip(B, D), color=LINE, linewidth=1.2)
    ax.plot(*zip(T, R, Bm, L, T), color=LINE, linewidth=1.2)

    for hnum, (pts, label_anchor) in houses.items():
        sign = (asc_sign + hnum - 1) % 12
        is_asc_house = hnum == 1

        if is_asc_house:
            poly = Polygon(pts, closed=True, facecolor="#f3e3d3", edgecolor=LINE, linewidth=1.2, zorder=1)
            ax.add_patch(poly)

        tagx, tagy = sign_tag_pos[hnum]
        ax.text(tagx, tagy, RASHI_SHORT[sign], fontsize=8, color="#8a7660",
                ha="center", va="center", style="italic", zorder=3)

        planet_list = by_house[hnum]
        label = "\n".join(PLANET_ABBR[p] + ("(R)" if result["planets"][p]["retrograde"] else "")
                           for p in planet_list)
        if is_asc_house:
            label = ("Asc\n" + label) if label else "Asc"

        lx, ly = label_anchor
        ax.text(lx, ly, label, fontsize=10, color=TEXT, ha="center", va="center",
                fontweight="bold", zorder=3, linespacing=1.4)

    ax.set_xlim(-0.3, 4.3)
    ax.set_ylim(-0.3, 4.5)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, fontsize=13, color=TEXT, pad=10)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# SOUTH INDIAN CHART (fixed sign positions in a 4x4 grid; ascendant marked)
# ---------------------------------------------------------------------------

SIGN_GRID_POS = {
    0: (0, 1), 1: (0, 2), 2: (0, 3), 3: (1, 3), 4: (2, 3), 5: (3, 3),
    6: (3, 2), 7: (3, 1), 8: (3, 0), 9: (2, 0), 10: (1, 0), 11: (0, 0),
}


def draw_south_indian(result, title="South Indian Chart"):
    asc_sign = result["ascendant"]["sign"]
    by_sign = _planets_by_sign(result)

    fig, ax = plt.subplots(figsize=(5.2, 5.2))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    cell = 1.0
    for sign in range(12):
        row, col = SIGN_GRID_POS[sign]
        x0, y0 = col * cell, (3 - row) * cell  # flip row so row0 is at top
        is_asc = sign == asc_sign

        rect = Rectangle((x0, y0), cell, cell,
                          facecolor="#f3e3d3" if is_asc else BG,
                          edgecolor=LINE, linewidth=1.4, zorder=1)
        ax.add_patch(rect)

        ax.text(x0 + 0.07, y0 + cell - 0.12, RASHI_SHORT[sign], fontsize=7.5,
                color="#8a7660", ha="left", va="top", style="italic", zorder=3)

        planet_list = by_sign[sign]
        label = "\n".join(PLANET_ABBR[p] + ("(R)" if result["planets"][p]["retrograde"] else "")
                           for p in planet_list)
        if is_asc:
            label = ("Asc\n" + label) if label else "Asc"

        ax.text(x0 + cell / 2, y0 + cell / 2 - 0.08, label, fontsize=9.5, color=TEXT,
                ha="center", va="center", fontweight="bold", zorder=3, linespacing=1.4)

    # frame + center label
    ax.plot([0, 4, 4, 0, 0], [0, 0, 4, 4, 0], color=LINE, linewidth=1.8, zorder=2)
    ax.text(2, 2, result["name"], fontsize=10, color="#8a7660", ha="center", va="center", style="italic")

    ax.set_xlim(-0.2, 4.2)
    ax.set_ylim(-0.2, 4.2)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, fontsize=13, color=TEXT, pad=10)
    fig.tight_layout()
    return fig
