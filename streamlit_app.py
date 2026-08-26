"""
Heka Hoods - Box Order web app.

Paste in a job's hood pieces (once you've read them off a job card - Claude
can do that part in a chat), see them grouped into boxes live, and download
the filled-in Dispatch Works Order. See box_order/README.md for the rules
this applies and box_order/box_grouping.py for the engine itself.
"""

import io

import pandas as pd
import streamlit as st

from box_order.box_grouping import Piece, group_into_boxes
from box_order.known_jobs import JOBS
from box_order.write_to_template import write_job

st.set_page_config(page_title="Heka Hoods - Box Order", page_icon="📦", layout="wide")

PIECE_COLUMNS = ["id", "depth_mm", "length_mm", "orientation", "tapered", "angle_deg", "returns", "uncertain"]

EXAMPLE_CLIENTS = {
    "XP0096": "Express by Heka Hoods",
    "HH23173N": "Provision Projects",
    "HH23341N": "Renovation Solutions",
    "HH23104N": "Architects Ink",
    "HH22496N": "DLG Aluminium & Glazing",
    "HH20143SA": "Horizon Construction Services",
}

EMPTY_ROW = {"id": "", "depth_mm": 450, "length_mm": 1200, "orientation": "regular",
             "tapered": False, "angle_deg": 0, "returns": 0, "uncertain": ""}


def _job_to_df(pieces) -> pd.DataFrame:
    return pd.DataFrame([
        {"id": p.label, "depth_mm": p.depth_mm, "length_mm": p.length_mm,
         "orientation": p.orientation, "tapered": p.tapered,
         "angle_deg": p.angle_deg, "returns": p.returns,
         "uncertain": p.uncertain or ""}
        for p in pieces
    ], columns=PIECE_COLUMNS)


def _load_example():
    choice = st.session_state["example_choice"]
    if choice == "-":
        return
    st.session_state["job_id"] = choice
    st.session_state["client"] = EXAMPLE_CLIENTS.get(choice, "")
    st.session_state["pieces_editor"] = _job_to_df(JOBS[choice])


st.title("Heka Hoods - Box Order")
st.caption("Group a job's hoods into boxes and generate the Dispatch Works Order.")

with st.sidebar:
    st.header("Job details")
    job_id = st.text_input("Job #", key="job_id")
    client = st.text_input("Client / Company", key="client")
    h_sections = st.number_input("H Sections", min_value=0, value=0, step=1, key="h_sections")
    joiners = st.number_input("Joiners", min_value=0, value=0, step=1, key="joiners")

    st.divider()
    st.selectbox("Load an example job", ["-"] + list(JOBS.keys()),
                 key="example_choice", on_change=_load_example)

st.subheader("Pieces")
st.caption(
    "One row per piece. Leave `uncertain` blank when you're confident about a "
    "piece's shape/return/angle; fill it in if you're not sure - that piece "
    "goes solo and gets flagged, instead of being silently grouped."
)

if "pieces_editor" not in st.session_state:
    st.session_state["pieces_editor"] = pd.DataFrame([EMPTY_ROW], columns=PIECE_COLUMNS)

pieces_df = st.data_editor(
    st.session_state["pieces_editor"],
    key="pieces_editor",
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "id": st.column_config.TextColumn("Hood ID", required=True),
        "depth_mm": st.column_config.NumberColumn("Depth (mm)", min_value=0),
        "length_mm": st.column_config.NumberColumn("Length (mm)", min_value=0),
        "orientation": st.column_config.SelectboxColumn("Orientation", options=["regular", "inverted"]),
        "tapered": st.column_config.CheckboxColumn("Tapered"),
        "angle_deg": st.column_config.NumberColumn("Angle (°)", min_value=0, max_value=45),
        "returns": st.column_config.NumberColumn("Returns", min_value=0, max_value=2),
        "uncertain": st.column_config.TextColumn("Uncertain? (why, or blank)"),
    },
)

rows = pieces_df.dropna(subset=["id"]).to_dict("records")
rows = [r for r in rows if str(r["id"]).strip()]

if not rows:
    st.info("Add at least one piece above to see box groupings.")
    st.stop()

pieces = [
    Piece(
        job_id=st.session_state["job_id"] or "JOB",
        label=str(r["id"]),
        depth_mm=float(r["depth_mm"] or 0),
        length_mm=float(r["length_mm"] or 0),
        orientation=r["orientation"] or "regular",
        tapered=bool(r["tapered"]),
        angle_deg=float(r["angle_deg"] or 0),
        returns=int(r["returns"] or 0),
        uncertain=(str(r["uncertain"]).strip() or None) if r["uncertain"] else None,
    )
    for r in rows
]

boxes = group_into_boxes(pieces)

st.subheader(f"Result: {len(boxes)} box{'es' if len(boxes) != 1 else ''}")

flagged_count = sum(1 for b in boxes if b.flagged)
if flagged_count:
    st.warning(f"{flagged_count} box{'es need' if flagged_count != 1 else ' needs'} a human check before dispatch.")

result_rows = []
for i, box in enumerate(boxes, start=1):
    result_rows.append({
        "Box": i,
        "Hoods": box.label,
        "Depth (mm)": box.depth_mm,
        "Length H1": box.length_h1,
        "Length H2": box.length_h2 or "",
        "Returns": box.returns,
        "Base (mm)": box.base_length_mm,
        "Lid (mm)": box.lid_length_mm,
        "Notes": "; ".join(box.reasons) if box.reasons else "",
        "⚠": "⚠️ CONFIRM" if box.flagged else "",
    })

st.dataframe(pd.DataFrame(result_rows), use_container_width=True, hide_index=True)

st.divider()

can_generate = bool(st.session_state["job_id"]) and bool(st.session_state["client"])
if not can_generate:
    st.info("Fill in Job # and Client in the sidebar to generate the Dispatch Works Order file.")
else:
    if st.button("Generate Dispatch Works Order", type="primary"):
        try:
            out_path = write_job(
                job_id=st.session_state["job_id"],
                client=st.session_state["client"],
                boxes=boxes,
                total_hoods=len(pieces),
                total_h_sections=int(st.session_state["h_sections"]),
                total_joiners=int(st.session_state["joiners"]),
                out_name=f"{st.session_state['job_id']} - BOX ORDER.xlsx",
            )
            with open(out_path, "rb") as f:
                data = f.read()
            st.download_button(
                "Download filled DWO",
                data=io.BytesIO(data),
                file_name=out_path.name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            st.success(f"Generated {out_path.name} - every formula in the template is untouched, only data cells were filled.")
        except ValueError as e:
            st.error(str(e))
