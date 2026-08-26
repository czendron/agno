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
# Read directly off the real drawing. One correction from the earlier
# version stands: hoods 3 and 4 actually have 5 pieces each (A/B/C/D/E),
# not 3 - the page details table confirms it (4 Joiners + 4 H-Sections = 4
# joints, which needs 5 pieces). The earlier version was missing the D
# piece on both and had the remaining run as one piece instead of two.
#
# On the "are the legs returns" question (2026-08-26): yes - Caio confirmed
# it is a return, just a small one (a 100mm tab at the angle, joined by
# hardware - an LJN - rather than welded). +100mm (1 return) per LJN corner
# a piece touches; the plain in-line JN joints between horizontal segments
# don't add anything, since there's no angle there. Worked out per piece
# from the joint topology in the drawing:
#   - leg (A or the last letter): touches exactly 1 LJN -> returns=1
#   - a horizontal piece next to a leg (e.g. B, or D on the 5-piece hoods):
#     touches 1 LJN -> returns=1
#   - a horizontal piece between two other horizontal pieces (only C on
#     the 5-piece hoods 3/4 - both its neighbours are plain JN, no angle):
#     touches 0 LJN -> returns=0
#   - the single top piece on the 3-piece hoods (2B/5B/6B) touches an LJN
#     on BOTH ends -> returns=2
#
# Hood 1 (taper, confirmed by Caio): 1A/1B/1C all solo (tapered shape).
_horizon_pieces = [
    Piece("HH20143SA", "1A", 900, 1340, tapered=True),
    Piece("HH20143SA", "1B", 573.7, 1645, tapered=True),
    Piece("HH20143SA", "1C", 200, 1645, tapered=True),
]
# Hoods 2, 5, 6: 3-piece U-shapes (leg, top, leg), all HH450.
# Hoods 3, 4: 5-piece runs (leg, 3 horizontal segments, leg), all HH450.
# The middle segment lengths on 3/4 are read off the drawing's dimension
# lines, not cross-checked against a second source the way the confirmed
# jobs were - worth a quick glance if this job ever needs re-verifying.
_horizon_runs = {
    "2": [(1198.5, 1), (2147, 2), (1198.5, 1)],
    "3": [(1198.5, 1), (2583, 1), (2584, 0), (2584, 1), (1198.5, 1)],
    "4": [(1198.5, 1), (2573, 1), (2574, 0), (2574, 1), (1198.5, 1)],
    "5": [(1198.5, 1), (1787, 2), (1198.5, 1)],
    "6": [(1198.5, 1), (1787, 2), (1198.5, 1)],
}
_letters = "ABCDE"
for hood, segs in _horizon_runs.items():
    for letter, (length, returns) in zip(_letters, segs):
        _horizon_pieces.append(Piece("HH20143SA", f"{hood}{letter}", 450, length, returns=returns))
JOBS["HH20143SA"] = _horizon_pieces
