"""
FastAPI wrapper around the box_order engine - exists so the Next.js
frontend (web/) can call the exact same tested Python logic the Streamlit
app uses, instead of a second reimplementation in JS. Every endpoint here
is a thin adapter: parse request -> call the existing engine function ->
serialize the result. No business logic lives in this file.

Run locally: uvicorn box_order.api:app --reload --port 8000
"""

import json
from typing import List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from box_order.box_grouping import Piece, group_into_boxes
from box_order.known_jobs import JOBS
from box_order.labels import box_labels_html
from box_order.palletizing import (
    pack_pallets,
    row_fits,
    row_utilization,
    total_boxes,
    total_hoods,
    total_pallets,
    total_weight_kg,
)
from box_order.plotly_view import pallet_load_figure
from box_order.write_to_template import write_job

app = FastAPI(title="Heka Hoods Box Order API")

# Local-dev CORS - the Next.js dev server runs on a different port.
# Tighten this to the real deployed frontend origin before going to production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

EXAMPLE_CLIENTS = {
    "XP0096": "Express by Heka Hoods",
    "HH23173N": "Provision Projects",
    "HH23341N": "Renovation Solutions",
    "HH23104N": "Architects Ink",
    "HH22496N": "DLG Aluminium & Glazing",
    "HH20143SA": "Horizon Construction Services",
    "HH19634N": "Westbury Constructions",
    "HH22246": "Renovare",
    "HH19239N": "J.R. Prime",
}


class PieceIn(BaseModel):
    id: str
    depth_mm: float
    length_mm: float
    orientation: str = "regular"
    tapered: bool = False
    angle_deg: float = 0
    returns: int = 0
    is_express: bool = False
    uncertain: Optional[str] = None


class GroupRequest(BaseModel):
    pieces: List[PieceIn]


class PalletsRequest(BaseModel):
    pieces: List[PieceIn]
    freight_rate: float = 50.0
    truck_length_mm: float = 13600
    truck_width_mm: float = 2450
    truck_height_mm: float = 2700


class GenerateRequest(BaseModel):
    job_id: str
    client: str
    pieces: List[PieceIn]
    h_sections: int = 0
    joiners: int = 0


def _to_pieces(pieces_in: List[PieceIn], job_id: str = "JOB") -> List[Piece]:
    return [
        Piece(
            job_id=job_id, label=p.id, depth_mm=p.depth_mm, length_mm=p.length_mm,
            orientation=p.orientation, tapered=p.tapered, angle_deg=p.angle_deg,
            returns=p.returns, is_express=p.is_express, uncertain=p.uncertain,
        )
        for p in pieces_in
    ]


def _box_out(box, index: int) -> dict:
    sp = box.sorted_pieces
    return {
        "box_number": index,
        "label": box.label,
        "depth_mm": box.depth_mm,
        "length_h1": box.length_h1,
        "length_h2": box.length_h2,
        "returns": box.returns,
        "base_mm": box.base_length_mm,
        "lid_mm": box.lid_length_mm,
        "reasons": box.reasons,
        "flagged": box.flagged,
    }


@app.get("/api/jobs")
def list_jobs():
    return [{"job_id": jid, "client": EXAMPLE_CLIENTS.get(jid, "")} for jid in JOBS]


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(404, "unknown example job")
    pieces = JOBS[job_id]
    return {
        "job_id": job_id,
        "client": EXAMPLE_CLIENTS.get(job_id, ""),
        "pieces": [
            {"id": p.label, "depth_mm": p.depth_mm, "length_mm": p.length_mm,
             "orientation": p.orientation, "tapered": p.tapered,
             "angle_deg": p.angle_deg, "returns": p.returns, "is_express": p.is_express,
             "uncertain": p.uncertain}
            for p in pieces
        ],
    }


@app.post("/api/group")
def group(req: GroupRequest):
    boxes = group_into_boxes(_to_pieces(req.pieces))
    return {
        "boxes": [_box_out(b, i) for i, b in enumerate(boxes, start=1)],
        "flagged_count": sum(1 for b in boxes if b.flagged),
    }


@app.post("/api/pallets")
def pallets(req: PalletsRequest):
    boxes = group_into_boxes(_to_pieces(req.pieces))
    rows = pack_pallets(boxes)
    freight_cost = total_pallets(rows) * req.freight_rate
    row_out = []
    for i, r in enumerate(rows, start=1):
        row_out.append({
            "row": i,
            "pallets": r.pallet_count,
            "boxes": r.box_count,
            "hoods": r.hood_count,
            "length_mm": r.row_length_mm,
            "width_mm": r.row_width_mm,
            "height_mm": r.row_height_mm,
            "weight_kg": r.weight_kg,
            "utilization": row_utilization(r),
            "fits_truck": row_fits(r, req.truck_width_mm, req.truck_height_mm),
        })
    lined_up_length = sum(r.row_length_mm for r in rows)
    figure = pallet_load_figure(rows)
    return {
        "rows": row_out,
        "totals": {
            "pallets": total_pallets(rows),
            "boxes": total_boxes(rows),
            "hoods": total_hoods(rows),
            "weight_kg": total_weight_kg(rows),
            "freight_cost": freight_cost,
        },
        "lined_up_length_mm": lined_up_length,
        "truck_length_mm": req.truck_length_mm,
        "plotly_figure": json.loads(figure.to_json()),
    }


@app.post("/api/generate-dwo")
def generate_dwo(req: GenerateRequest):
    boxes = group_into_boxes(_to_pieces(req.pieces, req.job_id))
    try:
        out_path = write_job(
            job_id=req.job_id, client=req.client, boxes=boxes,
            total_hoods=len(req.pieces), total_h_sections=req.h_sections,
            total_joiners=req.joiners, out_name=f"{req.job_id} - BOX ORDER.xlsx",
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return FileResponse(
        out_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=out_path.name,
    )


@app.post("/api/labels")
def labels(req: GenerateRequest):
    boxes = group_into_boxes(_to_pieces(req.pieces, req.job_id))
    html = box_labels_html(req.job_id, boxes)
    return JSONResponse({"html": html, "filename": f"{req.job_id} - box labels.html"})


@app.post("/api/analyze-job-card")
async def analyze_job_card(file: UploadFile = File(...)):
    from box_order.ai_reader import read_job_card
    import os

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(400, "ANTHROPIC_API_KEY not configured on the API server")
    pdf_bytes = await file.read()
    try:
        result = read_job_card(pdf_bytes, api_key)
    except Exception as e:  # noqa: BLE001 - surface any failure to the frontend as a normal error
        raise HTTPException(500, f"Couldn't read that job card: {e}")
    return {
        "job_id": result.job_id,
        "pieces": [p.model_dump() for p in result.pieces],
    }
