"""Reusable chart builders.

Every chart in the app should come from here so the mark specs (2px lines,
4px rounded bar ends, recessive grid, hover layer, legend rules) stay
consistent. Add new forms here rather than calling Plotly from a page.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from . import theme
from .config import label


def timeseries(
    df: pd.DataFrame,
    x: str = "month",
    y: str = "n",
    color: str | None = None,
    title: str = "",
) -> go.Figure:
    """Change over time. One series = no legend; many = fold past 8 to Other."""
    data = df
    if color is not None:
        data = theme.fold_to_other(df, color, y, top=8)

    fig = px.line(
        data,
        x=x,
        y=y,
        color=color,
        title=title,
        labels={x: label(x), y: label(y), **({color: label(color)} if color else {})},
    )
    fig.update_traces(line=dict(width=2), hovertemplate="%{y:,} complaints<extra>%{fullData.name}</extra>")
    fig.update_layout(
        hovermode="x unified",
        showlegend=color is not None,
        xaxis=dict(showspikes=True, spikemode="across", spikethickness=1,
                   spikecolor=theme.AXIS, spikedash="solid"),
    )
    if color is None:
        fig.update_traces(line_color=theme.SEQUENTIAL_MAIN, hovertemplate="%{y:,} complaints<extra></extra>")
    return fig


def ranked_bar(
    df: pd.DataFrame,
    category: str,
    value: str = "n",
    title: str = "",
    top: int = 10,
) -> go.Figure:
    """Magnitude ranked by size — ONE hue, because color here would encode rank,
    not identity. Values are direct-labelled at the end of each bar."""
    data = df.nlargest(top, value).sort_values(value)
    data = data.assign(_label=data[category].map(theme.truncate))

    fig = go.Figure(
        go.Bar(
            x=data[value],
            y=data["_label"],
            orientation="h",
            marker_color=theme.SEQUENTIAL_MAIN,
            marker_line=dict(width=2, color=theme.SURFACE),
            text=data[value].map("{:,}".format),
            textposition="outside",
            textfont=dict(color=theme.INK_SECONDARY, size=12),
            customdata=data[[category]],
            hovertemplate="%{customdata[0]}<br>%{x:,} complaints<extra></extra>",
        )
    )
    fig.update_layout(
        title=title,
        showlegend=False,
        xaxis=dict(showgrid=True, gridcolor=theme.GRID, title=None, showticklabels=False),
        yaxis=dict(showgrid=False, title=None, ticksuffix="  "),
        margin=dict(l=8, r=64, t=48, b=8),
        height=max(260, 34 * len(data) + 90),
    )
    return fig


def share_bar(
    df: pd.DataFrame,
    category: str,
    series: str,
    value: str = "n",
    title: str = "",
) -> go.Figure:
    """Composition within each category — stacked, normalized to 100%.
    Series get categorical hues (identity), folded to 8 + Other."""
    data = theme.fold_to_other(df, series, value, top=8)
    data = data.assign(_label=data[category].map(theme.truncate))

    fig = px.bar(
        data,
        x=value,
        y="_label",
        color=series,
        orientation="h",
        title=title,
        labels={value: label(value), series: label(series), "_label": label(category)},
    )
    fig.update_traces(marker_line=dict(width=2, color=theme.SURFACE))
    fig.update_layout(
        barmode="stack",
        barnorm="percent",
        xaxis=dict(showgrid=True, gridcolor=theme.GRID, title=None, ticksuffix="%"),
        yaxis=dict(showgrid=False, title=None, ticksuffix="  "),
        height=max(280, 34 * data["_label"].nunique() + 120),
    )
    return fig


def state_map(df: pd.DataFrame, state: str = "state", value: str = "n", title: str = "") -> go.Figure:
    """Choropleth — continuous magnitude, so one hue light->dark."""
    fig = px.choropleth(
        df,
        locations=state,
        locationmode="USA-states",
        color=value,
        scope="usa",
        color_continuous_scale=theme.SEQUENTIAL,
        title=title,
        labels={value: label(value)},
    )
    fig.update_traces(
        marker_line=dict(width=0.6, color=theme.SURFACE),
        hovertemplate="%{location}<br>%{z:,} complaints<extra></extra>",
    )
    fig.update_layout(
        geo=dict(bgcolor=theme.SURFACE, lakecolor=theme.SURFACE, landcolor="#f0efec",
                 subunitcolor=theme.SURFACE),
        coloraxis_colorbar=dict(title=None, thickness=10, len=0.6, outlinewidth=0,
                                tickfont=dict(color=theme.INK_MUTED, size=11)),
        margin=dict(l=0, r=0, t=48, b=0),
        height=420,
    )
    return fig
