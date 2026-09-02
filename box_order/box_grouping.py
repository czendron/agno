"""
Heka Hoods box-grouping engine.

Encodes the rules Caio confirmed on 2026-08-12 (against 6 real jobs pulled
from the Final Drawings folder), plus one rule change confirmed 2026-08-26:

  1. Max 2 hoods (pieces) per box.
  2. Only pieces with depth <= 600mm are eligible to pair (HH300/450/600, or
     any custom depth in between, e.g. 330mm) - anything deeper is always solo.
  3. A piece is always solo if: depth > 600mm, OR it has a welded return
     (Returns column > 0), OR it's tapered / a non-standard shape, OR it's
     angled (any angle between flange and depth - 5/10/15/30/45deg).
     A mitred piece is NOT automatically solo by itself - it can still pair
     with a straight piece if the other conditions are met.
  4. Two pairable pieces can share a box if they have the SAME depth.
     [2026-08-26 UPDATE] Orientation no longer needs to match - standard
     (regular) and inverted hoods can now be paired together, same as any
     other 2-per-box combination. Before this date, regular/inverted could
     not mix; if you're comparing against output from before 2026-08-26,
     that's the difference you're seeing.
  5. When two hoods share a box, the longer one is listed first.
  6. When more than one valid pairing exists, prefer whichever pairing keeps
     box lengths across the job as close to equal as possible (Caio confirmed
     this is a general goal, applied manually and inconsistently today).
     [2026-08-26 UPDATE] For an odd-sized same-depth pool specifically, where
     more than one pairing ties on box-length equality: leave the longest
     piece solo (not the leftover middle piece from naive longest+shortest
     pairing) and pair the rest longest-with-shortest. This never changes
     which box sizes result (the longest piece always sets its box's size,
     paired or not) - it only changes which piece carries that size alone
     vs. picks up a partner, so it balances total material per box instead.
     Confirmed by Caio on job HH22246 (Renovare, 3 same-depth solo-eligible
     pieces) and it also resolves the HH23104N labelling discrepancy noted
     below - both were the same underlying tie-break question.

STILL UNCONFIRMED (carried over from 2026-08-12):
  - Whether this solo-forcing list is complete.
  - Any box weight limit (none known yet).

RESOLVED 2026-08-26: Horizon HH20143SA Hoods 2-6's vertical legs ARE
returns - confirmed by Caio - just small ones (a 100mm tab at each angled
corner, joined by hardware rather than welded). Each piece gets 1 return
per LJN (L-shaped/angled) corner it touches - 0, 1, or 2 depending on
where it sits in the run; the plain in-line JN joints between straight
horizontal segments don't count, since there's no angle there. See the
per-piece breakdown in known_jobs.py.

RESOLVED 2026-08-26 (the general shape of the returns rule): confirmed
across three jobs (Horizon, Westbury HH19634N, and HH19239N) that this
comes down to one consistent mechanism - a VERTICAL piece gets 1 return
per real corner (direction change) it touches, while a HORIZONTAL piece
gets 0 returns regardless of how many corners it touches. Westbury's
"legs=1, top=0" was this rule applied to an open 3-piece U (each leg
touches exactly 1 corner). HH19239N's Hood 2 is a closed rectangular loop
- its two vertical end pieces each touch 2 corners (one where the top run
meets them, one where the bottom run does), so they get returns=2 each;
every horizontal run segment, even the ones directly touching a corner,
still gets 0. Caio's framing: "when we have a full surround (a closed
square or rectangle) or L-shapes, the vertical hood will always have a
return (one or two)." Plain in-line JN joints between two horizontal
segments (no direction change) still don't count, per the Horizon note
above. See the per-piece breakdown in known_jobs.py.

RESOLVED 2026-08-26 (odd-pool tie-break): earlier versions of this file
paired same-depth odd pools via naive repeated "pop longest + pop shortest",
which always left the *middle* piece solo. On HH23104N (Architects Ink) this
produced "2B & 1" solo "2A", where Caio's confirmed answer was "2A & 1" solo
"2B" - the box dimensions came out identical either way (2A=1548mm and
2B=1549mm both round up to 1550mm), so it never caused a wrong-size box, but
it could put the wrong literal hood ID on a box's paperwork. Rather than
guess a tie-breaking rule from that one example, it was left unfixed and
flagged as a labelling detail worth a human glance. Caio then gave the
actual rule on a second, unrelated odd-pool job (HH22246, Renovare): leave
the *longest* piece solo, not the middle one - see rule 6 above. That rule
also happens to exactly reproduce Caio's original HH23104N answer, so both
jobs are now asserted normally in verify_known_jobs.py, no more workaround.

Angle length-padding (5/10/15deg=+0, 30deg=+50mm, 45deg=+100mm) is applied
by hand to the length before it's typed into the sheet, per Caio - so it's
not re-applied here; length_mm is assumed to already include it if relevant.

RESOLVED 2026-09-02 (Express range): confirmed by Caio - Express orders
(Heka Hoods' standard/stock range, as opposed to a custom job) always get
1 hood per box, full stop, regardless of depth/returns/shape/anything
else that would otherwise allow pairing. The Express range is a
constrained catalog: depth is always one of 300/450/600mm, length is
always 1200 or 2400mm, and colour is always Surfmist Matt, Monument Matt,
or Black Matt (colour isn't modeled here - it doesn't affect box/pallet
dimensions - but is noted in case a future rule needs it). A piece marked
is_express with a depth or length outside that catalog gets flagged
UNCERTAIN rather than trusted silently, same as any other reading that
looks off.

This retroactively changes XP0096 (job_id literally means "eXPress",
EXAMPLE_CLIENTS labels it "Express by Heka Hoods", both its pieces are
450mm/1200mm - squarely in the Express catalog): it was previously
confirmed and asserted as one paired box ("1 & 2"), from before this
rule was known. Marked is_express=True and re-confirmed as two solo
boxes ("1", "2") in known_jobs.py/verify_known_jobs.py to match - see
the comment there. Flagged for Caio to double check against what
actually shipped, since this reverses a previously-confirmed result
rather than just adding a new one.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import math

EXPRESS_DEPTHS_MM = {300, 450, 600}
EXPRESS_LENGTHS_MM = {1200, 2400}
EXPRESS_COLOURS = {"Surfmist Matt", "Monument Matt", "Black Matt"}  # not modeled on Piece - see module docstring


def round_up_10(x: float) -> float:
    """Matches the sheet's ROUNDUP(x, -1) - round up to the nearest 10mm."""
    return math.ceil(x / 10) * 10


@dataclass
class Piece:
    job_id: str
    label: str                     # e.g. "1A", "2", "3"
    depth_mm: float
    length_mm: float
    orientation: str = "regular"   # "regular" or "inverted" - kept as metadata;
                                    # no longer a pairing constraint, see rule 4
    tapered: bool = False          # non-constant depth / non-standard shape
    angle_deg: float = 0           # 0 = flat; otherwise 5/10/15/30/45
    returns: int = 0               # 0, 1, or 2 (full surround)
    is_express: bool = False       # Express range (stock, not custom) - always 1/box, see module docstring
    uncertain: Optional[str] = None  # set if a flag above is a guess, not a fact

    def solo_reasons(self) -> List[str]:
        reasons = []
        if self.depth_mm > 600:
            reasons.append(f"depth {self.depth_mm:.0f}mm > 600mm")
        if self.returns > 0:
            reasons.append(f"has return (x{self.returns})")
        if self.tapered:
            reasons.append("tapered / non-standard shape")
        if self.angle_deg > 0:
            reasons.append(f"angled ({self.angle_deg:.0f}°)")
        if self.is_express:
            reasons.append("Express order - always 1 hood per box")
            if self.depth_mm not in EXPRESS_DEPTHS_MM:
                reasons.append(f"UNCERTAIN: Express depth {self.depth_mm:.0f}mm isn't one of the standard 300/450/600mm sizes")
            if self.length_mm not in EXPRESS_LENGTHS_MM:
                reasons.append(f"UNCERTAIN: Express length {self.length_mm:.0f}mm isn't one of the standard 1200/2400mm sizes")
        if self.uncertain:
            reasons.append(f"UNCERTAIN: {self.uncertain}")
        return reasons

    def must_go_alone(self) -> bool:
        return len(self.solo_reasons()) > 0


@dataclass
class Box:
    pieces: List[Piece]
    reasons: List[str] = field(default_factory=list)  # why solo, if solo

    @property
    def sorted_pieces(self) -> List[Piece]:
        return sorted(self.pieces, key=lambda p: p.length_mm, reverse=True)

    @property
    def label(self) -> str:
        return " & ".join(p.label for p in self.sorted_pieces)

    @property
    def depth_mm(self) -> float:
        return self.pieces[0].depth_mm

    @property
    def length_h1(self) -> float:
        return self.sorted_pieces[0].length_mm

    @property
    def length_h2(self) -> float:
        return self.sorted_pieces[1].length_mm if len(self.pieces) > 1 else 0

    @property
    def returns(self) -> int:
        return max((p.returns for p in self.pieces), default=0)

    @property
    def base_length_mm(self) -> float:
        longest = max(p.length_mm for p in self.pieces)
        return round_up_10(longest) + self.returns * 100 + 350

    @property
    def lid_length_mm(self) -> float:
        return self.base_length_mm + 40

    @property
    def flagged(self) -> bool:
        return any("UNCERTAIN" in r for r in self.reasons)


def can_pair(a: Piece, b: Piece) -> bool:
    if a.must_go_alone() or b.must_go_alone():
        return False
    if a.depth_mm != b.depth_mm:
        return False
    return True


def group_into_boxes(pieces: List[Piece]) -> List[Box]:
    """
    Splits one job's pieces into boxes per the rules above. Pieces that must
    go alone are boxed immediately. The rest are pooled by depth alone (as of
    2026-08-26 - orientation is no longer part of the pool key, see rule 4)
    and paired longest-with-shortest, repeatedly - this balances resulting
    box lengths across the job (rule 6), matching the Architects Ink example
    Caio worked through by hand, modulo the odd-pool caveat documented above.
    """
    boxes: List[Box] = []
    pairable: List[Piece] = []

    for p in pieces:
        reasons = p.solo_reasons()
        if reasons:
            boxes.append(Box(pieces=[p], reasons=reasons))
        else:
            pairable.append(p)

    pools = {}
    for p in pairable:
        key = p.depth_mm
        pools.setdefault(key, []).append(p)

    for pool in pools.values():
        pool = sorted(pool, key=lambda p: p.length_mm, reverse=True)
        solo = None
        if len(pool) % 2 == 1:
            # Odd pool: the longest piece goes alone rather than the
            # leftover middle piece - see rule 6 note above. This never
            # changes which box sizes come out (the longest piece always
            # sets its box's size, paired or not), it just decides which
            # piece carries that size alone vs. picks up a partner.
            solo = pool.pop(0)
        while len(pool) > 1:
            longest = pool.pop(0)
            shortest = pool.pop(-1)
            boxes.append(Box(pieces=[longest, shortest]))
        if solo is not None:
            boxes.append(Box(pieces=[solo], reasons=["odd one out in its size/shape pool"]))

    return boxes


def report(job_id: str, boxes: List[Box]) -> str:
    lines = [f"=== {job_id} ({len(boxes)} boxes) ==="]
    for i, box in enumerate(boxes, start=1):
        flag = "  [FLAG: NEEDS CONFIRMATION]" if box.flagged else ""
        why = f"  <- solo: {', '.join(box.reasons)}" if len(box.pieces) == 1 and box.reasons else ""
        lines.append(
            f"Box {i:>3}: {box.label:<12} depth={box.depth_mm:.0f}mm  "
            f"H1={box.length_h1:.0f} H2={box.length_h2:.0f} returns={box.returns}  "
            f"base={box.base_length_mm:.0f}mm lid={box.lid_length_mm:.0f}mm{why}{flag}"
        )
    return "\n".join(lines)
