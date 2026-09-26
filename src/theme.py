"""Chart palette and Plotly template.

The palette is the validated default set (light surface #fcfcfb). Rules that
matter when you add charts later:

  * Categorical hues are assigned in SLOT ORDER and never cycled. A 9th series
    folds into "Other" (see ``fold_to_other``) — it never gets a generated hue.
  * Color follows the entity, not its rank: a bar chart ranked by count is
    MAGNITUDE, so it gets one hue (``SEQUENTIAL``), not eight.
  * Never a second y-axis. Two measures of different scale = two charts.
  * A legend is present for >= 2 series and absent for one (the title names it).
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

# --- Categorical slots, fixed order ---------------------------------------
CATEGORICAL = [
    "#2a78d6",  # 1 blue
    "#eb6834",  # 2 orange
    "#1baf7a",  # 3 aqua
    "#eda100",  # 4 yellow
    "#e87ba4",  # 5 magenta
    "#008300",  # 6 green
    "#4a3aa7",  # 7 violet
    "#e34948",  # 8 red
]
# Scatter / bubble / choropleth compare ALL pairs, not just adjacent ones —
# only the first three slots clear the floors there.
CATEGORICAL_ALL_PAIRS = CATEGORICAL[:3]

# --- Single-hue sequential ramp (blue, light -> dark) ----------------------
SEQUENTIAL = [
    "#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec",
    "#5598e7", "#3987e5", "#2a78d6", "#256abf", "#1c5cab",
    "#184f95", "#104281", "#0d366b",
]
SEQUENTIAL_MAIN = "#2a78d6"

# --- Diverging: blue <-> gray <-> red -------------------------------------
DIVERGING = ["#0d366b", "#3987e5", "#cde2fb", "#f0efec", "#f5c0c0", "#e34948", "#a32424"]

# --- Status (reserved — never reused as a series color) -------------------
STATUS = {
    "good": "#0ca30c",
    "warning": "#fab219",
    "serious": "#ec835a",
    "critical": "#d03b3b",
}

# --- Chrome ----------------------------------------------------------------
SURFACE = "#fcfcfb"
PAGE = "#f9f9f7"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"

FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'

TEMPLATE = "cdc"


def register_template() -> None:
    """Install the shared Plotly template. Call once, at app start."""
    pio.templates[TEMPLATE] = go.layout.Template(
        layout=go.Layout(
            colorway=CATEGORICAL,
            paper_bgcolor=SURFACE,
            plot_bgcolor=SURFACE,
            font=dict(family=FONT, size=13, color=INK_SECONDARY),
            title=dict(font=dict(size=16, color=INK), x=0, xanchor="left", pad=dict(b=12)),
            margin=dict(l=8, r=8, t=48, b=8),
            xaxis=dict(
                showgrid=False,
                linecolor=AXIS,
                zeroline=False,
                ticks="outside",
                ticklen=4,
                tickcolor=AXIS,
                tickfont=dict(color=INK_MUTED, size=12),
                automargin=True,
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor=GRID,
                gridwidth=1,
                linecolor="rgba(0,0,0,0)",
                zeroline=False,
                ticks="",
                tickfont=dict(color=INK_MUTED, size=12),
                automargin=True,
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.0,
                xanchor="left",
                x=0,
                title=None,
                font=dict(color=INK_SECONDARY, size=12),
                bgcolor="rgba(0,0,0,0)",
            ),
            hoverlabel=dict(
                bgcolor=SURFACE,
                bordercolor=AXIS,
                font=dict(family=FONT, size=12, color=INK),
            ),
            barcornerradius=4,
            bargap=0.28,
            colorscale=dict(sequential=[[i / 12, c] for i, c in enumerate(SEQUENTIAL)]),
        )
    )
    pio.templates.default = TEMPLATE


def fold_to_other(
    df: pd.DataFrame, key: str, value: str, top: int = 8, other: str = "Other"
) -> pd.DataFrame:
    """Keep the ``top`` largest categories by ``value``; sum the rest into one
    "Other" row. This is how a 9th series is handled — never a 9th hue."""
    if df[key].nunique() <= top:
        return df
    keep = df.groupby(key)[value].sum().nlargest(top).index
    folded = df.copy()
    folded[key] = folded[key].where(folded[key].isin(keep), other)
    return folded.groupby([c for c in folded.columns if c != value], as_index=False)[
        value
    ].sum()


def truncate(text: object, width: int = 42) -> str:
    """Shorten a long category label for an axis tick."""
    s = str(text)
    return s if len(s) <= width else s[: width - 1] + "…"
