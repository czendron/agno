"""
Heka Hoods - Box Order web app.

Upload a job card (or paste pieces by hand), see them grouped into boxes
and packed onto pallets live, and download the filled-in Dispatch Works
Order. See box_order/README.md for the rules this applies.
"""

import io
import os

import pandas as pd
import streamlit as st

from box_order.box_grouping import Piece, group_into_boxes
from box_order.known_jobs import JOBS
from box_order.palletizing import pack_pallets, total_pallets
from box_order.plotly_view import pallet_load_figure
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


def _get_api_key() -> str:
    try:
        return st.secrets["ANTHROPIC_API_KEY"]
    except (KeyError, FileNotFoundError):
        return os.environ.get("ANTHROPIC_API_KEY", "")


def _job_to_df(pieces) -> pd.DataFrame:
    return pd.DataFrame([
        {"id": p.label, "depth_mm": p.depth_mm, "length_mm": p.length_mm,
         "orientation": p.orientation, "tapered": p.tapered,
         "angle_deg": p.angle_deg, "returns": p.returns,
         "uncertain": p.uncertain or ""}
        for p in pieces
    ], columns=PIECE_COLUMNS)


def _bump_pieces_data(df: pd.DataFrame) -> None:
    # st.data_editor owns its value once instantiated - it refuses a direct
    # st.session_state[key] overwrite after that (StreamlitValueAssignmentNotAllowedError).
    # Changing the widget's key forces a fresh instance instead, which does accept a new value.
    st.session_state["pieces_data"] = df
    st.session_state["pieces_version"] = st.session_state.get("pieces_version", 0) + 1


def _load_example():
    choice = st.session_state["example_choice"]
    if choice == "-":
        return
    st.session_state["job_id"] = choice
    st.session_state["client"] = EXAMPLE_CLIENTS.get(choice, "")
    _bump_pieces_data(_job_to_df(JOBS[choice]))


def _analyze_job_card():
    uploaded = st.session_state.get("job_card_upload")
    if uploaded is None:
        return
    api_key = _get_api_key()
    if not api_key:
        st.session_state["ai_error"] = (
            "No ANTHROPIC_API_KEY found (checked Streamlit secrets and the "
            "environment). Add one in the app's Settings -> Secrets to use this."
        )
        return
    from box_order.ai_reader import read_job_card  # deferred: keeps the app usable without the anthropic package configured
    try:
        with st.spinner("Reading job card..."):
            extracted = read_job_card(uploaded.read(), api_key)
        st.session_state["job_id"] = extracted.job_id
        _bump_pieces_data(pd.DataFrame([
            {"id": p.id, "depth_mm": p.depth_mm, "length_mm": p.length_mm,
             "orientation": p.orientation, "tapered": p.tapered,
             "angle_deg": p.angle_deg, "returns": p.returns,
             "uncertain": p.uncertain or ""}
            for p in extracted.pieces
        ], columns=PIECE_COLUMNS))
        st.session_state["ai_error"] = None
    except Exception as e:  # noqa: BLE001 - surface any failure in the UI, this is a best-effort draft step
        st.session_state["ai_error"] = f"Couldn't read that job card: {e}"


st.title("Heka Hoods - Box Order")
st.caption("Group a job's hoods into boxes, pack them onto pallets, and generate the Dispatch Works Order.")

with st.sidebar:
    st.header("Job card")
    st.file_uploader("Upload a job card (PDF)", type=["pdf"], key="job_card_upload")
    st.button("Analyze with AI", on_click=_analyze_job_card,
              disabled=st.session_state.get("job_card_upload") is None)
    if st.session_state.get("ai_error"):
        st.error(st.session_state["ai_error"])
    st.caption(
        "Drafts the table below from the PDF - always reviewed by a human before "
        "anything is computed, same as any other uncertain piece."
    )

    st.divider()
    st.header("Job details")
    job_id = st.text_input("Job #", key="job_id")
    client = st.text_input("Client / Company", key="client")
    h_sections = st.number_input("H Sections", min_value=0, value=0, step=1, key="h_sections")
    joiners = st.number_input("Joiners", min_value=0, value=0, step=1, key="joiners")

    st.divider()
    st.selectbox("Or load an example job", ["-"] + list(JOBS.keys()),
                 key="example_choice", on_change=_load_example)

left, right = st.columns([3, 2])

with left:
    st.subheader("Pieces")
    st.caption(
        "One row per piece. Leave `uncertain` blank when you're confident about a "
        "piece's shape/return/angle; fill it in if you're not sure - that piece "
        "goes solo and gets flagged, instead of being silently grouped."
    )

    if "pieces_data" not in st.session_state:
        st.session_state["pieces_data"] = pd.DataFrame([EMPTY_ROW], columns=PIECE_COLUMNS)
        st.session_state["pieces_version"] = 0

    pieces_df = st.data_editor(
        st.session_state["pieces_data"],
        key=f"pieces_editor_{st.session_state['pieces_version']}",
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
        st.info("Add at least one piece above (or upload a job card) to see box groupings.")
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
            "Length H2": box.length_h2 or None,  # None, not "" - keeps the column numeric (mixed float/str breaks Arrow serialization)
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

with right:
    st.subheader("Pallet load")
    rows_ = pack_pallets(boxes)
    st.caption(f"{total_pallets(rows_)} pallets (1200mm squares, joined end to end for long boxes)")
    st.plotly_chart(pallet_load_figure(rows_), use_container_width=True)
    st.caption(
        "Box size = that box's hood depth + 200mm (width/depth), 600mm height. "
        "Max 2 boxes stacked per footprint. Placeholder numbers - tell me and I'll change them."
    )
