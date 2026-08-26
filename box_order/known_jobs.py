"""
Piece dimensions for 6 real jobs, read off the Final Drawings PDFs.

Confidence varies by job - see verify_known_jobs.py, which checks the
confirmed jobs strictly and only prints (doesn't assert) the rest:

  - XP0096, HH23173N, HH23341N, HH23104N: confirmed by Caio against what
    dispatch actually did. Should match exactly (see the known odd-pool
    caveat on HH23104N in box_grouping.py).
  - HH22496N (DLG), HH20143SA (Horizon): included, but partly flagged
    UNCERTAIN per the open questions in box_grouping.py. Review, don't
    trust blindly.
"""

from box_order.box_grouping import Piece

JOBS = {}

# --- XP0096 - Express by Heka Hoods (confirmed via the live spreadsheet) ---
JOBS["XP0096"] = [
    Piece("XP0096", "1", 450, 1200),
    Piece("XP0096", "2", 450, 1200),
]

# --- HH23173N - Provision Projects (confirmed by Caio) ---
JOBS["HH23173N"] = [
    Piece("HH23173N", "1", 300, 2700),
    Piece("HH23173N", "2", 300, 2700),
]

# --- HH23341N - Renovation Solutions (confirmed by Caio: "2 & 1") ---
JOBS["HH23341N"] = [
    Piece("HH23341N", "1", 600, 1950),
    Piece("HH23341N", "2", 600, 2720),
]

# --- HH23104N - Architects Ink (confirmed by Caio: box1 "2A & 1", box2 "2B", box3 "3") ---
JOBS["HH23104N"] = [
    Piece("HH23104N", "1", 600, 1020),
    Piece("HH23104N", "2A", 600, 1548),
    Piece("HH23104N", "2B", 600, 1549),
    Piece("HH23104N", "3", 1020, 1020),  # corner/mitred - solo on depth alone, mitre not the reason
]

# --- HH22496N - DLG Aluminium & Glazing (36 identical hoods) ---
# Each hood = 2 angled top pieces (A, B - 15deg, HH500, ~1622mm) + 1 vertical
# return (C - HH483, ~2090mm, returns=1). Angled hoods are ALWAYS solo per
# Caio's latest rule, so A and B are solo too, not paired with each other -
# this UPDATES an earlier (wrong) assumption that A+B could pair.
_dlg_pieces = []
for n in range(1, 37):
    _dlg_pieces.append(Piece("HH22496N", f"{n}A", 500, 1622, angle_deg=15))
    _dlg_pieces.append(Piece("HH22496N", f"{n}B", 500, 1622, angle_deg=15))
    _dlg_pieces.append(Piece("HH22496N", f"{n}C", 483, 2090, returns=1))
JOBS["HH22496N"] = _dlg_pieces

# --- HH20143SA - Horizon Construction Services ---
# Hood 1 (taper, confirmed by Caio): 1A alone (depth 900->600), 1B/1C alone
# (tapered / non-standard shape).
_horizon_pieces = [
    Piece("HH20143SA", "1A", 900, 1340, tapered=True),
    Piece("HH20143SA", "1B", 573.7, 1645, tapered=True),
    Piece("HH20143SA", "1C", 200, 1645, tapered=True),
]
# Hoods 2, 3, 4, 5, 6: U-shaped wraps (A=left leg, B=top, C=right leg), all
# constant HH450, joined by L-shaped joiners - Caio said he's NOT SURE
# whether the vertical legs (A/C) count as "returns". Flagging rather than
# guessing.
_u_shape_hoods = {
    "2": {"A": 1200, "B": 2150, "C": 1200},
    "3": {"A": 1200, "B": 7760, "C": 1200},
    "4": {"A": 1200, "B": 7730, "C": 1200},
    "5": {"A": 1200, "B": 1790, "C": 1200},
    "6": {"A": 1200, "B": 1790, "C": 1200},
}
for hood, segs in _u_shape_hoods.items():
    _horizon_pieces.append(Piece("HH20143SA", f"{hood}A", 450, segs["A"],
                                  uncertain="is this vertical leg a 'return'? not confirmed"))
    _horizon_pieces.append(Piece("HH20143SA", f"{hood}B", 450, segs["B"]))
    _horizon_pieces.append(Piece("HH20143SA", f"{hood}C", 450, segs["C"],
                                  uncertain="is this vertical leg a 'return'? not confirmed"))
JOBS["HH20143SA"] = _horizon_pieces
