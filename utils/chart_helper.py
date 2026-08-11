from __future__ import annotations
import plotly.graph_objects as go

def _ensure_pct(scores):
    """Accept scores either already in 0-100 or in 0-1 fraction units."""
    s = list(scores) if scores is not None else []
    if not s:
        return s
    # Heuristic: if the largest score <= 1.0, treat the input as a fraction.
    if max(s) <= 1.0001:
        return [v * 100 for v in s]
    return s


def build_top3_chart(jobs, scores):
    if not jobs or not scores:
        return go.Figure().update_layout(
            template="plotly_dark",
            annotations=[dict(
                text="No predictions available yet.",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=14, color="#cfd8d2"),
            )],
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=300,
        )

    pct = _ensure_pct(scores)
    # Clip to [0, 100] so a runaway scorer can't push labels off-canvas.
    pct = [max(0.0, min(100.0, v)) for v in pct]

    palette = ["#e3a86c", "#d4b890", "#a4c2b0", "#7a8e87"]
    bar_colors = [palette[i % len(palette)] for i in range(len(jobs))]

    fig = go.Figure(
        data=[
            go.Bar(
                x=pct,
                y=[f"#{i+1}  {job}" for i, job in enumerate(jobs)],
                orientation="h",
                text=[f"{v:.0f}% match" for v in pct],
                textposition="outside",
                textfont=dict(size=12, color="#e8efe9"),
                cliponaxis=False,
                marker=dict(
                    color=bar_colors,
                    line=dict(color="rgba(255,255,255,.25)", width=1),
                ),
                hovertemplate=(
                    "<b>%{y}</b>"
                    "<br>Match score: %{x:.1f}%"
                    "<extra></extra>"
                ),
            )
        ]
    )

    fig.update_layout(
        height=360,
        margin=dict(l=200, r=140, t=40, b=70),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="-apple-system, Inter, Segoe UI, Roboto", color="#cfd8d2"),
        bargap=0.45,
        showlegend=False,
    )

    fig.update_xaxes(
        title=dict(
            text="Match Score (%)",
            font=dict(size=12, color="#cfd8d2"),
            standoff=18,
        ),
        range=[0, 105],
        showgrid=True,
        gridcolor="rgba(255,255,255,.08)",
        tickvals=[0, 25, 50, 75, 100],
        ticksuffix="%",
        zeroline=False,
    )

    fig.update_yaxes(
        title=None,
        autorange="reversed",
        automargin=True,
        showgrid=False,
        ticks="",
    )

    return fig
