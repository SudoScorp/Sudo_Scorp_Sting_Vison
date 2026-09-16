"""Render each SLIDES entry from content.py to a 1920x1080 PNG.

Style: dark background with a soft radial gradient, glass-card panels with
drop shadows, and genuine 3D (mplot3d + LightSource shading) for the gravity
well diagrams, the title sphere, and the comparison bar charts.
"""
import os
import textwrap

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
from matplotlib.colors import LightSource, LinearSegmentedColormap
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

from content import SLIDES

W, H = 19.2, 10.8
DPI = 100

BG = "#070b14"
BG2 = "#121b2e"
PANEL = "#141f36"
PANEL2 = "#0e1626"
FG = "#eef2f8"
MUTED = "#93a2b8"
GOLD = "#d4af37"
GOLD_LT = "#f0d878"
TEAL = "#2dd4bf"
BLUE = "#5b8def"
RED = "#e05252"

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["mathtext.fontset"] = "cm"

OUT_DIR = os.path.join(os.path.dirname(__file__), "slides")
os.makedirs(OUT_DIR, exist_ok=True)


# ---------------------------------------------------------------- utilities

def radial_gradient(w_px, h_px, center, inner_hex, outer_hex, power=1.6):
    def to_rgb(hx):
        hx = hx.lstrip("#")
        return np.array([int(hx[i:i + 2], 16) for i in (0, 2, 4)]) / 255.0

    cin, cout = to_rgb(inner_hex), to_rgb(outer_hex)
    yy, xx = np.mgrid[0:h_px, 0:w_px]
    cx, cy = center[0] * w_px, center[1] * h_px
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    d = d / d.max()
    t = np.clip(d, 0, 1) ** power
    img = np.empty((h_px, w_px, 3))
    for k in range(3):
        img[:, :, k] = cin[k] * (1 - t) + cout[k] * t
    return img


def new_fig():
    fig = plt.figure(figsize=(W, H), dpi=DPI)
    fig.patch.set_facecolor(BG)
    bg_ax = fig.add_axes([0, 0, 1, 1])
    bg_ax.set_xlim(0, 1)
    bg_ax.set_ylim(0, 1)
    bg_ax.axis("off")
    grad = radial_gradient(960, 540, (0.62, 0.42), BG2, BG, power=1.7)
    bg_ax.imshow(grad, extent=[0, 1, 0, 1], aspect="auto", zorder=-10)

    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")
    ax.patch.set_alpha(0)
    return fig, ax


def add_title(ax, title, y=9.75, size=40, color=FG):
    ax.text(1.0, y, title, fontsize=size, color=color, weight="bold",
             ha="left", va="top", family="DejaVu Sans")
    ax.plot([1.0, W - 1.0], [y - 0.55, y - 0.55], color=GOLD, lw=2, alpha=0.85)


def add_plain_callout(ax, text, y=9.0):
    if not text:
        return y
    wrapped = wrap(text, 95)
    n = wrapped.count("\n") + 1
    box_h = 0.5 * n + 0.32
    card(ax, 1.0, y - box_h, W - 2.0, box_h, face="#1c2947", edge=GOLD, alpha=0.55)
    ax.text(1.35, y - box_h / 2, "→", fontsize=20, color=GOLD, ha="left", va="center")
    ax.text(1.85, y - box_h / 2, wrapped, fontsize=17.5, color=GOLD_LT, ha="left",
             va="center", style="italic", linespacing=1.35)
    return y - box_h - 0.35


def card(ax, x, y, w, h, face=PANEL, edge=None, alpha=1.0, shadow=True, r=0.09):
    if shadow:
        ax.add_patch(mpatches.FancyBboxPatch(
            (x + 0.09, y - 0.09), w, h,
            boxstyle=f"round,pad=0.0,rounding_size={r}",
            linewidth=0, facecolor="black", alpha=0.35, zorder=1))
    ax.add_patch(mpatches.FancyBboxPatch(
        (x, y), w, h, boxstyle=f"round,pad=0.0,rounding_size={r}",
        linewidth=1.1 if edge else 0, edgecolor=edge or "none",
        facecolor=face, alpha=alpha, zorder=2))


def wrap(text, width):
    return "\n".join(textwrap.wrap(text, width=width))


# -------------------------------------------------------------- slide kinds

def slide_title(ax, s):
    # 3D lit sphere, upper right, representing the substrate field / a mass
    ax3d = plt.gcf().add_axes([0.56, 0.28, 0.42, 0.62], projection="3d")
    u = np.linspace(0, 2 * np.pi, 90)
    v = np.linspace(0, np.pi, 90)
    x = np.outer(np.cos(u), np.sin(v))
    y = np.outer(np.sin(u), np.sin(v))
    z = np.outer(np.ones_like(u), np.cos(v))
    ls = LightSource(azdeg=305, altdeg=45)
    base = np.array([0.83, 0.68, 0.21])
    rgb = ls.shade(z, cmap=LinearSegmentedColormap.from_list(
        "gold", [[0.03, 0.04, 0.08], base, [1, 0.98, 0.85]]),
        vert_exag=1, blend_mode="soft")
    ax3d.plot_surface(x, y, z, facecolors=rgb, rstride=1, cstride=1,
                       antialiased=True, shade=False, linewidth=0)
    ax3d.set_box_aspect((1, 1, 1))
    ax3d.set_axis_off()
    ax3d.view_init(elev=18, azim=35)
    ax3d.set_facecolor("none")
    ax3d.patch.set_alpha(0)

    for i, r in enumerate([5.4, 4.1, 3.0]):
        circle = plt.Circle((W - 3.6, H / 2 + 0.2), r, fill=False,
                             color=GOLD, alpha=0.08 + 0.015 * i, lw=1.6)
        ax.add_patch(circle)

    ax.text(1.0, H / 2 + 1.35, s["title"], fontsize=54, color=FG, weight="bold",
            ha="left", va="center")
    ax.text(1.0, H / 2 + 0.35, s["subtitle"], fontsize=25, color=TEAL,
            ha="left", va="center")
    ax.plot([1.05, 1.05 + 5.6], [H / 2 - 0.02, H / 2 - 0.02], color=GOLD, lw=2, alpha=0.8)
    ax.text(1.0, 1.1, s.get("footer", ""), fontsize=15, color=MUTED,
            ha="left", va="center")


def slide_bullets(ax, s):
    add_title(ax, s["title"])
    y = add_plain_callout(ax, s.get("plain"), y=9.05)
    y -= 0.15
    for b in s["bullets"]:
        wrapped = wrap(b, 88)
        n_lines = wrapped.count("\n") + 1
        row_h = 0.5 * n_lines + 0.28
        card(ax, 1.3, y - row_h, W - 2.6, row_h, face=PANEL, alpha=0.92, r=0.07)
        ax.text(1.6, y - row_h / 2, "●", fontsize=13, color=GOLD, ha="left", va="center")
        ax.text(2.0, y - row_h / 2, wrapped, fontsize=21, color=FG, ha="left", va="center",
                linespacing=1.35)
        y -= row_h + 0.2
    if s.get("footer"):
        ax.text(W / 2, max(y - 0.15, 0.55), s["footer"], fontsize=17, color=GOLD,
                ha="center", va="center", style="italic")


def slide_equation_block(ax, s):
    add_title(ax, s["title"])
    y = add_plain_callout(ax, s.get("plain"), y=9.05)
    y -= 0.2
    for eq, note in s["lines"]:
        card(ax, 1.3, y - 1.05, W - 2.6, 1.05, face=PANEL, alpha=0.92, r=0.08)
        ax.text(1.75, y - 0.42, eq, fontsize=29, color=GOLD_LT, ha="left", va="center")
        ax.text(W - 1.75, y - 0.42, note, fontsize=16, color=MUTED, ha="right", va="center")
        y -= 1.28
    if s.get("note"):
        ax.text(W / 2, max(y - 0.05, 0.5), s["note"], fontsize=19, color=TEAL,
                ha="center", va="top", style="italic")


def _gravity_well(ax3d, direction, color_hex):
    n = 70
    x = np.linspace(-3, 3, n)
    y = np.linspace(-3, 3, n)
    X, Y = np.meshgrid(x, y)
    R = np.sqrt(X ** 2 + Y ** 2) + 0.35
    if direction == "outward":
        Z = 1.6 / R          # a hill / peak -> unstable, rolls away (repulsive)
    else:
        Z = -1.6 / R         # a well -> ball settles at bottom (attractive)

    def to_rgb(hx):
        hx = hx.lstrip("#")
        return tuple(int(hx[i:i + 2], 16) / 255 for i in (0, 2, 4))

    accent = to_rgb(color_hex)
    cmap = LinearSegmentedColormap.from_list("well", [[0.04, 0.05, 0.09], accent, [1, 1, 1]])
    ls = LightSource(azdeg=300, altdeg=55)
    znorm = (Z - Z.min()) / (Z.max() - Z.min() + 1e-9)
    rgb = ls.shade(znorm, cmap=cmap, vert_exag=0.3, blend_mode="soft")
    ax3d.plot_surface(X, Y, Z, facecolors=rgb, rstride=1, cstride=1,
                       linewidth=0, antialiased=True, shade=False)

    # a small ball resting on the visible slope: perched near the peak, about to
    # roll off (outward) or partway down the wall, settling toward the bottom (inward)
    r_ball = 1.15
    bx, by = r_ball, 0.0
    if direction == "outward":
        bz = 1.6 / (r_ball + 0.35) + 0.22
        ball_color = "#f7d7d7"
    else:
        bz = -1.6 / (r_ball + 0.35) + 0.22
        ball_color = "#eafff9"
    ax3d.scatter([bx], [by], [bz], color=ball_color, s=520, edgecolor="#1a1e28",
                 linewidth=1.8, depthshade=False, zorder=10)

    ax3d.set_box_aspect((1, 1, 0.6))
    ax3d.set_zlim(Z.min() * 1.05, Z.max() * 1.05)
    ax3d.set_axis_off()
    ax3d.set_facecolor("none")
    ax3d.patch.set_alpha(0)
    ax3d.view_init(elev=24, azim=-50)


def slide_diagram_force(ax, s):
    add_title(ax, s["title"])
    y = add_plain_callout(ax, s.get("plain"), y=9.05)

    ax3d = plt.gcf().add_axes([0.20, 0.10, 0.60, 0.62], projection="3d")
    _gravity_well(ax3d, s["direction"], s["color"])

    label = "REPULSIVE — rolls away" if s["direction"] == "outward" else "ATTRACTIVE — settles in (correct)"
    ax.text(W / 2, 1.55, label, fontsize=21, color=s["color"], ha="center", va="center",
            weight="bold")
    ax.text(W / 2, y - 0.15, s["eq"], fontsize=27, color=FG, ha="center", va="center")
    ax.text(W / 2, 0.75, wrap(s["caption"], 88), fontsize=16.5, color=MUTED,
            ha="center", va="center", linespacing=1.3)


def slide_table(ax, s):
    add_title(ax, s["title"])
    y0 = add_plain_callout(ax, s.get("plain"), y=9.05)
    headers = s["headers"]
    rows = s["rows"]
    ncols = len(headers)
    col_w = (W - 2.4) / ncols
    x0 = 1.2
    top = y0 - 0.1
    row_h = 0.98
    card(ax, x0 - 0.05, top - 0.85 - row_h * len(rows) - 0.1, W - 2.3,
         0.85 + row_h * len(rows) + 0.2, face=PANEL2, alpha=0.85, r=0.1)
    for c, htext in enumerate(headers):
        x = x0 + c * col_w
        ax.add_patch(mpatches.FancyBboxPatch((x, top - 0.85), col_w - 0.1, 0.85,
                                              boxstyle="round,pad=0.0,rounding_size=0.06",
                                              linewidth=0, facecolor=GOLD, alpha=0.92, zorder=3))
        ax.text(x + col_w / 2, top - 0.425, htext, fontsize=18, color=BG, ha="center",
                va="center", weight="bold", zorder=4)
    for r, row in enumerate(rows):
        y = top - 0.85 - (r + 1) * row_h
        for c, cell in enumerate(row):
            x = x0 + c * col_w
            color = FG if c != 2 else TEAL
            ax.text(x + col_w / 2, y + row_h / 2, cell, fontsize=20,
                    color=color, ha="center", va="center", zorder=4)
        if r < len(rows) - 1:
            ax.plot([x0, x0 + ncols * col_w - 0.1], [y, y], color=MUTED, lw=0.6,
                     alpha=0.3, zorder=3)


def _bar3d(ax3d, xpos, ypos, dx, dy, dz, color):
    for x, y, h, c in zip(xpos, ypos, dz, color):
        top_h = max(abs(h), 1e-6)
        z0 = min(0, h)
        ax3d.bar3d(x, y, z0, dx, dy, top_h, color=c, shade=True, edgecolor="#0a0e18",
                   linewidth=0.6, alpha=0.96)


def slide_bar_compare(ax, s):
    add_title(ax, s["title"])
    add_plain_callout(ax, s.get("plain"), y=9.05)

    ax3d = plt.gcf().add_axes([0.22, 0.10, 0.56, 0.62], projection="3d")
    vals = [s["left_value"], s["right_value"]]
    colors = [RED, TEAL]
    _bar3d(ax3d, [0, 1.3], [0, 0], 0.7, 0.7, vals, colors)
    ax3d.set_xlim(-0.5, 2.5)
    ax3d.set_ylim(-1, 1)
    zr = max(abs(v) for v in vals) * 1.4
    ax3d.set_zlim(-zr, zr)
    ax3d.set_xticks([0.35, 1.65])
    ax3d.set_xticklabels([s["left_label"], s["right_label"]], fontsize=13, color=FG)
    ax3d.set_yticks([])
    ax3d.set_zticks([])
    ax3d.set_axis_off()
    ax3d.view_init(elev=18, azim=-60)
    ax3d.set_facecolor("none")

    for xv, v, lab in [(3.1, vals[0], s["left_label"]), (11.9, vals[1], s["right_label"])]:
        pass
    ax.text(4.9, 6.0, f"{vals[0]:+.3f} {s['unit']}", fontsize=22, color=RED, ha="center",
            va="center", weight="bold")
    ax.text(4.9, 5.5, s["left_label"], fontsize=15, color=MUTED, ha="center", va="center")
    ax.text(14.2, 6.0, f"{vals[1]:+.3f} {s['unit']}", fontsize=22, color=TEAL, ha="center",
            va="center", weight="bold")
    ax.text(14.2, 5.5, s["right_label"], fontsize=15, color=MUTED, ha="center", va="center")
    ax.text(W / 2, 1.05, wrap(s["caption"], 82), fontsize=17.5, color=MUTED,
            ha="center", va="center")


def slide_grouped_bar(ax, s):
    add_title(ax, s["title"])
    add_plain_callout(ax, s.get("plain"), y=9.05)

    ax3d = plt.gcf().add_axes([0.14, 0.08, 0.74, 0.64], projection="3d")
    cats = s["categories"]
    a, b = s["series_a"], s["series_b"]
    n = len(cats)
    xs_a = np.arange(n) * 2.0
    xs_b = xs_a + 0.9
    _bar3d(ax3d, xs_a, [0] * n, 0.75, 0.75, a["values"], [a["color"]] * n)
    _bar3d(ax3d, xs_b, [0] * n, 0.75, 0.75, b["values"], [b["color"]] * n)
    ax3d.set_xticks(xs_a + 0.45)
    ax3d.set_xticklabels(cats, fontsize=13, color=FG)
    ax3d.set_yticks([])
    ax3d.set_zlim(0, max(max(a["values"]), max(b["values"])) * 1.25)
    ax3d.set_zlabel(s["ylabel"], color=MUTED, fontsize=12, labelpad=2)
    ax3d.tick_params(colors=MUTED, labelsize=11)
    for axis in (ax3d.xaxis, ax3d.yaxis, ax3d.zaxis):
        axis.pane.set_visible(False)
        axis.pane.set_edgecolor("none")
        axis._axinfo["grid"]["linewidth"] = 0
    ax3d.xaxis.line.set_color("none")
    ax3d.yaxis.line.set_color("none")
    ax3d.zaxis.line.set_color(MUTED)
    ax3d.view_init(elev=18, azim=-60)
    ax3d.set_facecolor("none")
    ax3d.patch.set_alpha(0)

    swatch_y = 2.35
    ax.add_patch(mpatches.Rectangle((15.3, swatch_y), 0.4, 0.3, color=a["color"]))
    ax.text(15.85, swatch_y + 0.15, a["label"], fontsize=16, color=FG, va="center")
    ax.add_patch(mpatches.Rectangle((15.3, swatch_y - 0.55), 0.4, 0.3, color=b["color"]))
    ax.text(15.85, swatch_y - 0.4, b["label"], fontsize=16, color=FG, va="center")

    ax.text(W / 2, 1.05, wrap(s["caption"], 92), fontsize=16.5, color=MUTED,
            ha="center", va="center")


RENDERERS = {
    "title": slide_title,
    "bullets": slide_bullets,
    "equation_block": slide_equation_block,
    "diagram_force": slide_diagram_force,
    "table": slide_table,
    "bar_compare": slide_bar_compare,
    "grouped_bar": slide_grouped_bar,
}


def main():
    for i, s in enumerate(SLIDES):
        fig, ax = new_fig()
        RENDERERS[s["kind"]](ax, s)
        out = os.path.join(OUT_DIR, f"{s['id']}.png")
        fig.savefig(out, facecolor=BG)
        plt.close(fig)
        print("rendered", out)


if __name__ == "__main__":
    main()
