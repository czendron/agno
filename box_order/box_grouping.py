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

KNOWN LIMITATION (found 2026-08-26 while porting/verifying this file): when
a same-depth pool has an odd number of pieces (3, 5, ...), the "pop longest
+ pop shortest, repeat" pairing below always leaves the *middle* piece as
the solo one. On HH23104N (Architects Ink) this produces "2B & 1" solo "2A",
where Caio's confirmed answer was "2A & 1" solo "2B" - the opposite pairing.
The box dimensions come out identical either way (2A=1548mm and 2B=1549mm
both round up to 1550mm), so this has never caused a wrong-size box, but it
can put the wrong literal hood ID on a box's paperwork. Rather than guess a
tie-breaking rule from one example, odd-sized pools are left as-is and
should be treated as a labelling detail worth a human glance, not a fact to
trust blindly - see verify_known_jobs.py.

Angle length-padding (5/10/15deg=+0, 30deg=+50mm, 45deg=+100mm) is applied
by hand to the length before it's typed into the sheet, per Caio - so it's
not re-applied here; length_mm is assumed to already include it if relevant.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import math


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
        while len(pool) > 1:
            longest = pool.pop(0)
            shortest = pool.pop(-1)
            boxes.append(Box(pieces=[longest, shortest]))
        if pool:
            boxes.append(Box(pieces=[pool[0]], reasons=["odd one out in its size/shape pool"]))

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
