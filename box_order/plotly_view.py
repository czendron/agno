"""
3D pallet-load view, built with Plotly (renders fine inside Streamlit via
st.plotly_chart - no extra JS needed). Purely visual: shows the pack_pallets()
result as solid boxes on flat pallets so you can eyeball whether a layout
looks sane, not a CAD-accurate drawing.
"""

from typing import List

import plotly.graph_objects as go

from box_order.palletizing import PALLET_SIZE_MM, PalletRow

PALLET_THICKNESS_MM = 150
ROW_GAP_MM = 300

# Muted, architectural palette (concrete/steel/stone tones) to match the
# Heka Hoods brand identity (black/grey/white) instead of a bright default set.
BOX_COLORS = ["#2B2B2E", "#838287", "#B8B4AC", "#6E6A5E", "#4A4A4D", "#A89F91"]


def _cuboid_trace(x0, y0, z0, dx, dy, dz, color, name, opacity=1.0):
    x = [x0, x0, x0 + dx, x0 + dx, x0, x0, x0 + dx, x0 + dx]
    y = [y0, y0 + dy, y0 + dy, y0, y0, y0 + dy, y0 + dy, y0]
    z = [z0, z0, z0, z0, z0 + dz, z0 + dz, z0 + dz, z0 + dz]
    i = [0, 0, 4, 4, 0, 0, 1, 1, 0, 0, 3, 3]
    j = [1, 2, 5, 6, 3, 7, 2, 6, 1, 5, 2, 6]
    k = [2, 3, 6, 7, 7, 4, 6, 5, 5, 4, 6, 7]
    return go.Mesh3d(
        x=x, y=y, z=z, i=i, j=j, k=k,
        color=color, opacity=opacity, name=name,
        hovertext=name, hoverinfo="text",
        flatshading=True,
        lighting=dict(ambient=0.6, diffuse=0.6, specular=0.2),
    )


def pallet_load_figure(rows: List[PalletRow]) -> go.Figure:
    traces = []
    y_cursor = 0.0

    for row in rows:
        row_length = row.pallet_count * PALLET_SIZE_MM
        traces.append(_cuboid_trace(
            0, y_cursor, -PALLET_THICKNESS_MM,
            row_length, PALLET_SIZE_MM, PALLET_THICKNESS_MM,
            color="#B0A08A", name=f"{row.pallet_count} pallet(s), depth {row.depth_mm:.0f}mm", opacity=0.9,
        ))
        for n in range(1, row.pallet_count):
            traces.append(_cuboid_trace(
                n * PALLET_SIZE_MM - 4, y_cursor, -PALLET_THICKNESS_MM,
                8, PALLET_SIZE_MM, PALLET_THICKNESS_MM,
                color="#4a4a4a", name="pallet join", opacity=0.9,
            ))

        for idx, placed in enumerate(row.boxes):
            color = BOX_COLORS[idx % len(BOX_COLORS)]
            y0 = y_cursor + (PALLET_SIZE_MM - placed.width_mm) / 2
            traces.append(_cuboid_trace(
                0, y0, placed.z_mm,
                placed.length_mm, placed.width_mm, placed.height_mm,
                color=color,
                name=f"Box: {placed.box.label} ({placed.length_mm:.0f}x{placed.width_mm:.0f}x{placed.height_mm:.0f}mm)",
                opacity=0.95,
            ))

        y_cursor += PALLET_SIZE_MM + ROW_GAP_MM

    fig = go.Figure(data=traces)
    fig.update_layout(
        scene=dict(
            xaxis_title="length (mm)",
            yaxis_title="width (mm)",
            zaxis_title="height (mm)",
            aspectmode="data",
        ),
        margin=dict(l=0, r=0, t=30, b=0),
        showlegend=False,
        height=600,
    )
    return fig
