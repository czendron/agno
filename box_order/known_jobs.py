"""
Piece dimensions for 10 real jobs, read off the Final Drawings / job card
PDFs.

Confidence varies by job - see verify_known_jobs.py, which checks the
confirmed jobs strictly and only prints (doesn't assert) the rest:

  - XP0096, HH23173N, HH23341N, HH23104N, HH19634N, HH22246, HH19239N,
    HH17435: confirmed by Caio against what dispatch actually did (or, for
    HH17435, unambiguous from the depth-alone solo rule - no pairing/tie
    -break logic even comes into play). Should match exactly.
  - HH22496N (DLG), HH20143SA (Horizon): included, but partly flagged
    UNCERTAIN per the open questions in box_grouping.py. Review, don't
    trust blindly.

Job cards are extracted from the Final Drawings and often only include
some of the pages the drawing set's own title block claims (e.g. "page 2
of 3") - that's expected, not a sign of missing data, unless a piece
actually needed for the box order turns out to be undimensioned anywhere
in what's provided (see HH19239N below for how that's handled).
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

# --- HH19634N - Westbury Constructions (confirmed by Caio 2026-08-26) ---
# 4 hoods, each a 3-piece U-shape (2 vertical legs + 1 horizontal top,
# joined by plain JN hardware at each corner) - same shape family as
# Horizon's 3-piece hoods above, but a DIFFERENT returns pattern: here each
# leg carries its own return (1, from a formed tab at its end) and the top
# piece carries none, even though it touches a JN corner at both ends.
# Don't generalize either job's rule onto the other - Horizon's LJN joints
# give a 3-piece hood's top piece returns=2; this job's plain JN joints
# give it returns=0. Different hardware, independently confirmed results.
# Piece lengths read off the drawing's own dimension chains (e.g. hoods
# 1/2: 100+3+814+3+100 = 1020 I/D; hoods 3/4: 100+3+764+3+100 = 970 I/D),
# cross-checked against Caio's confirmed box order - exact match.
JOBS["HH19634N"] = [
    Piece("HH19634N", "1A", 450, 1820, returns=1),
    Piece("HH19634N", "1B", 450, 814, returns=0),
    Piece("HH19634N", "1C", 450, 1820, returns=1),
    Piece("HH19634N", "2A", 450, 1820, returns=1),
    Piece("HH19634N", "2B", 450, 814, returns=0),
    Piece("HH19634N", "2C", 450, 1820, returns=1),
    Piece("HH19634N", "3A", 300, 1690, returns=1),
    Piece("HH19634N", "3B", 300, 764, returns=0),
    Piece("HH19634N", "3C", 300, 1690, returns=1),
    Piece("HH19634N", "4A", 300, 1690, returns=1),
    Piece("HH19634N", "4B", 300, 764, returns=0),
    Piece("HH19634N", "4C", 300, 1690, returns=1),
]

# --- HH22246 - Renovare (confirmed by Caio 2026-08-26) ---
# 3 single-piece hoods, no joiners/returns/taper/angle at all - the
# simplest job read so far. All three share depth 450mm, so all three are
# pairing-eligible, which makes this an odd (3-piece) same-depth pool -
# the exact case that pinned down the odd-pool tie-break rule in
# box_grouping.py (rule 6): the longest piece (3) goes solo, the other two
# (1, 2) pair. Box sizes come out the same as the OLD "leave the middle
# piece solo" behavior either way - Caio's reasoning was purely about
# balancing material weight per box, not box size.
JOBS["HH22246"] = [
    Piece("HH22246", "1", 450, 800),
    Piece("HH22246", "2", 450, 1400),
    Piece("HH22246", "3", 450, 1850),
]

# --- HH19239N - J.R. Prime (confirmed by Caio 2026-08-26) ---
# Two hoods, both JN-jointed, both on the same job card - the one that
# pinned down the general shape of the returns rule (see box_grouping.py):
# a vertical piece gets 1 return per real corner it touches, a horizontal
# piece always gets 0, no matter how many corners it touches.
#
# Hood 1 (depth 600mm - HH500 nominal, 600mm O/D, both shown on the
# drawing so O/D wins per the reveal-hood rule): an open 3-piece U, same
# shape and rule as Westbury - legs 1A/1C touch 1 corner each (returns=1),
# top 1B touches 2 corners but is horizontal (returns=0).
#
# Hood 2 (depth 300mm - HH200 nominal, 300mm O/D): a closed rectangular
# loop around a ~13m-wide opening, not a 3-piece U - four straight runs of
# HH300 profile joined by JN at 4 real corners, long enough that each run
# is itself split into several straight (no-corner) pieces. The two
# vertical end pieces (2A, 2G) each touch 2 corners (top run + bottom
# run), so returns=2 each - the case that generalized the rule above.
#
# Only the TOP run (2A-2G) is dimensioned on the job card; the BOTTOM run
# (2G-2A the other way, i.e. 2H-2L) isn't dimensioned anywhere in the
# pages provided. Caio confirmed the general technique for this: when a
# symmetric shape's other half isn't dimensioned, mirror the dimensioned
# half - "same work to vertical position as well", i.e. the piece next to
# 2G on the bottom (2H) mirrors the piece next to 2G on the top (2F), and
# so on down to the piece next to 2A (2L, mirroring 2B). This is a
# confirmed technique, not a one-off guess - reuse it on future jobs with
# the same shape.
#
# Orientation (Caio, 2026-08-26): the top run (2B-2F) is a "fixing
# flange" - the flange stays straight, doesn't fold 90deg - so regular
# (the default). The bottom run (2H-2L) is an inverted hood - the lip
# folds to the same size as the flange. Doesn't change this job's box
# count (regular and inverted can share a box since the 2026-08-26 rule
# update, and the dimensions already matched), but it's the correct data.
JOBS["HH19239N"] = [
    Piece("HH19239N", "1A", 600, 2265, returns=1),
    Piece("HH19239N", "1B", 600, 963, returns=0),
    Piece("HH19239N", "1C", 600, 2265, returns=1),
    Piece("HH19239N", "2A", 300, 1360, returns=2),
    Piece("HH19239N", "2B", 300, 2547, returns=0),
    Piece("HH19239N", "2C", 300, 2547, returns=0),
    Piece("HH19239N", "2D", 300, 2547, returns=0),
    Piece("HH19239N", "2E", 300, 2547, returns=0),
    Piece("HH19239N", "2F", 300, 2548, returns=0),
    Piece("HH19239N", "2G", 300, 1360, returns=2),
    Piece("HH19239N", "2H", 300, 2548, returns=0, orientation="inverted"),  # mirrors 2F
    Piece("HH19239N", "2I", 300, 2547, returns=0, orientation="inverted"),  # mirrors 2E
    Piece("HH19239N", "2J", 300, 2547, returns=0, orientation="inverted"),  # mirrors 2D
    Piece("HH19239N", "2K", 300, 2547, returns=0, orientation="inverted"),  # mirrors 2C
    Piece("HH19239N", "2L", 300, 2547, returns=0, orientation="inverted"),  # mirrors 2B
]

# --- HH17435 (confirmed - unambiguous, depth alone forces every piece
# solo) ---
# One straight run (Hood 1), HH900 depth, gauge 6mm, cut into 5 segments
# by plain JN joiners. Lengths read directly off the drawing's own
# dimension chain (2583+2583+2584+2584+2584 + 4x10mm gaps = 12958mm,
# matching the drawing's own "12958 O/A" label exactly). No corners in
# this run, so returns=0 throughout. Page details table (4 Joiners + 4
# H-Sections + 5 hood segments = 13 Parts, 12.958 Lineal Metres) is
# self-consistent with just this one page/hood - despite the drawing
# saying "Page 1 of 4", nothing needed for THIS hood is missing (see the
# module docstring's general note on missing pages).
#
# Depth 900mm > 600mm forces every piece solo (Rule 3) regardless of the
# other rules, so this job never touches pairing or the odd-pool tie
# -break at all - about as unambiguous a case as they come.
#
# Two annotation types not seen on any earlier job ("CUT-OUT + ADDITIONAL
# FLANGE" on 1A, "ANGLE CUT-OUT + ADDITIONAL FLANGE" at the 1C/1D joint)
# and the explicit "6MM" gauge callout aren't modeled by any Piece field
# yet - flagged, not acted on, since neither changes this job's outcome.
# Revisit if a future job's annotations or gauge actually affect grouping
# or pallet weight.
JOBS["HH17435"] = [
    Piece("HH17435", "1A", 900, 2583),
    Piece("HH17435", "1B", 900, 2583),
    Piece("HH17435", "1C", 900, 2584),
    Piece("HH17435", "1D", 900, 2584),
    Piece("HH17435", "1E", 900, 2584),
]
