"""
Calls Claude to read a job card PDF and draft a piece list, in the same
shape the rest of the app uses. This is a DRAFT ONLY - the app shows it in
the editable table for a human to check before anything gets computed,
same "flag, don't guess" principle as the rest of the engine.

Needs an Anthropic API key (ANTHROPIC_API_KEY env var, or Streamlit secrets
key "ANTHROPIC_API_KEY"). Verified against two real job cards (Architects
Ink, Horizon) on 2026-08-26 with accurate results - still a draft shown for
human review before anything computes, same as any other uncertain piece,
not a reason to skip the review step.
"""

import base64
from typing import List, Optional

import anthropic
from pydantic import BaseModel

MODEL = "claude-opus-5"

SYSTEM_PROMPT = """You read Heka Hoods fabrication drawings (job cards / final drawings) for a
range-hood manufacturer and extract each physical piece as structured data.

Layout you'll see: each "Hood N" isometric drawing shows one or more
lettered pieces (e.g. "1", "2A", "2B") joined by joiners. A summary table
at the bottom lists Joiners/H-Sections/Struts/Hoods/Parts counts and the
Job #.

How to read the key fields:
- id: the piece's label as drawn (e.g. "1", "2A", "3C").
- depth_mm: from the "HH ###" callout on that piece (e.g. "HH 600" -> 600).
  For a reveal hood, use the O/D (outer) figure if both are shown.
- length_mm: use the dimension line drawn closest to and along that
  specific piece, NOT a larger "O/A" (overall) or combined multi-piece
  figure - those overstate a single piece's own length. When a run is
  split into several pieces by joiners, each piece has its own shorter
  dimension line; use that one.
- orientation: "regular" unless the drawing explicitly says inverted /
  reverse flange - if you can't tell, use "regular" and set `uncertain`.
- tapered: true if the piece's cross-section changes along its length
  (drawing shows "TAPER" labels/arrows, or two different depth values for
  one piece).
- angle_deg: the angle between flange and depth if the piece is drawn at
  an angle (e.g. "15 FALL" in the hood title, or an angle dimension on
  the piece itself). 0 if flat/standard.
- returns: how many small hardware-joined corner tabs ("returns") this
  piece touches - distinct from a plain in-line joiner. Check the joiner
  at each end of the piece: an L-shaped/angled joiner (often labelled
  LJN) where the piece bends into another piece counts as a return (+1
  per such corner, so 0, 1, or 2 total). A plain straight in-line joiner
  (JN) connecting two collinear pieces is NOT a return (+0). A fully
  welded integral folded corner on the SAME piece (see the drawing's
  legend note about welded returns) also counts as a return. This is
  genuinely easy to misread - when the joiner/corner type at an end
  isn't clearly labelled, don't guess: set `uncertain` explaining what's
  unclear, and give your best-guess value for the field anyway.
- uncertain: null when you're confident in every field above for this
  piece. Otherwise a short note on what's unclear. An uncertain piece
  gets shown to a human for confirmation rather than trusted blindly, so
  flag anything you're not sure about instead of guessing silently.

Ignore any client/company name or site address if present - extract only
the Job # (a code like "HH23104N" or "XP0096"), never client-identifying
text.

Extract every piece from every hood shown in the document. Skip pages
that are generic fixing/installation specification sheets with no hood
drawing.
"""


class ExtractedPiece(BaseModel):
    id: str
    depth_mm: float
    length_mm: float
    orientation: str
    tapered: bool
    angle_deg: float
    returns: int
    uncertain: Optional[str] = None


class ExtractedJob(BaseModel):
    job_id: str
    pieces: List[ExtractedPiece]


def read_job_card(pdf_bytes: bytes, api_key: str) -> ExtractedJob:
    client = anthropic.Anthropic(api_key=api_key)
    encoded = base64.standard_b64encode(pdf_bytes).decode("utf-8")

    response = client.messages.parse(
        model=MODEL,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": encoded,
                    },
                },
                {"type": "text", "text": "Extract every piece from this job card."},
            ],
        }],
        output_format=ExtractedJob,
    )
    return response.parsed_output
