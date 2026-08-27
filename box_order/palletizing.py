"""
Turns a job's boxes into a pallet layout for the 3D view.

Box physical dimensions (2026-08-27, confirmed by Caio against the real
"Estimating Dispatch Rules" doc - change freely if that changes, everything
downstream reads from these constants):
  - length = the box's own base_length_mm (already computed - the cut
    length formula in box_grouping.py)
  - width = depth = (that box's hood depth) + BOX_XY_CLEARANCE_MM - still
    the 2026-08-26 placeholder; the source doc gives a different formula
    (depth bucketed to a standard size, +80mm, +flange depth for reveal
    hoods) but that's NOT confirmed to apply here yet - don't change this
    without checking, see README "Open design questions".
  - height = BOX_HEIGHT_RETURN_MM (260mm) if the box has a return
    (box.returns > 0), else BOX_HEIGHT_NO_RETURN_MM (170mm) - confirmed by
    Caio 2026-08-27, replaces an earlier (wrong) hood-count-based guess.

Pallets are PALLET_SIZE_MM squares; boxes lie with their length running
along a row of however many pallets get joined end to end. Capped at
MAX_PALLETS_PER_ROW (2) - confirmed by Caio 2026-08-27: "at the base of
the stack we use 2 pallets. Never 3 or more." A box longer than 2 pallets
will overhang in the model rather than get a 3rd - that's the confirmed
behavior, not a bug. Boxes are grouped by depth (since width depends on
depth) onto separate rows, sorted longest-first, and stacked per
footprint before starting a new row.

Stacking limit (confirmed by Caio 2026-08-27, from the "Estimating
Dispatch Rules" doc's pallet table): total stack height, pallet included,
can't exceed TOTAL_STACK_HEIGHT_CEILING_MM (1.2m) - checked in
pack_pallets() against each stack's actual cumulative height. Caio's own
examples ("17cm boxes stack 6 high, 26cm stack 4 high") are the same rule
applied to a stack of all-one-height boxes - 1.2m ceiling minus the
150mm pallet leaves 1050mm for boxes, and 1050 // 170 = 6, 1050 // 260 =
4. This implementation checks cumulative actual height rather than
hardcoding "6" or "4", so a mixed stack (a solo and a paired box, say) is
handled correctly too, not just those two example cases. Deep hoods get
an extra hard cap via max_boxes_by_depth() on top of the height math
regardless: HH900+ depth maxes at 4 high, HH1200+ maxes at 2, even if the
height ceiling alone would allow more.

Weight (2026-08-26): BOX_WEIGHT_KG is a flat 15kg/box placeholder, not a
real calculation - Caio's explicit instruction was to stub this until an
actual weight formula exists (likely from hood depth/length/gauge, the
same inputs CALCULATIONS!D:F in the real template already uses for its
own weight estimate - see box_order/README.md). Swap BOX_WEIGHT_KG for a
per-box function once that's worked out; everything downstream (row and
job totals) just sums whatever this returns.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from box_order.box_grouping import Box

PALLET_SIZE_MM = 1200
PALLET_THICKNESS_MM = 150  # pallet itself (the timber/plastic base), not a box - matches plotly_view's render
BOX_XY_CLEARANCE_MM = 200
BOX_HEIGHT_NO_RETURN_MM = 170  # confirmed by Caio 2026-08-27 (Estimating Dispatch Rules doc)
BOX_HEIGHT_RETURN_MM = 260  # a box containing a return needs the taller box
TOTAL_STACK_HEIGHT_CEILING_MM = 1200  # hard constraint: pallet + stacked boxes, confirmed by Caio 2026-08-27
# Extra hard caps on boxes-per-footprint for deep hoods, checked in addition to the
# height-ceiling math above - confirmed by Caio 2026-08-27. (min depth_mm, max boxes high),
# checked most-restrictive-first.
DEPTH_STACK_OVERRIDES = [(1200, 2), (900, 4)]
MAX_PALLETS_PER_ROW = 2  # confirmed by Caio 2026-08-27 - never 3+, a longer box just overhangs
BOX_WEIGHT_KG = 15  # flat placeholder per box until real weight calc exists (2026-08-26)


def box_height_mm(box: Box) -> float:
    return BOX_HEIGHT_RETURN_MM if box.returns > 0 else BOX_HEIGHT_NO_RETURN_MM


def max_boxes_by_depth(depth_mm: float) -> Optional[int]:
    """A depth-specific hard cap on boxes stacked per footprint, or None if
    this depth has no override (just use the height-ceiling math instead)."""
    for min_depth, cap in DEPTH_STACK_OVERRIDES:
        if depth_mm >= min_depth:
            return cap
    return None


@dataclass
class PlacedBox:
    box: Box
    x_mm: float  # position of the box's near corner, pallet-row coordinate frame
    y_mm: float
    z_mm: float

    @property
    def length_mm(self) -> float:
        return self.box.base_length_mm

    @property
    def width_mm(self) -> float:
        return self.box.depth_mm + BOX_XY_CLEARANCE_MM

    @property
    def height_mm(self) -> float:
        return box_height_mm(self.box)


@dataclass
class PalletRow:
    depth_mm: float
    pallet_count: int
    boxes: List[PlacedBox] = field(default_factory=list)

    @property
    def row_length_mm(self) -> float:
        return self.pallet_count * PALLET_SIZE_MM

    @property
    def row_width_mm(self) -> float:
        return PALLET_SIZE_MM

    @property
    def row_height_mm(self) -> float:
        if not self.boxes:
            return PALLET_THICKNESS_MM
        stacked_height = max(p.z_mm + p.height_mm for p in self.boxes)
        return PALLET_THICKNESS_MM + stacked_height

    @property
    def box_count(self) -> int:
        return len(self.boxes)

    @property
    def hood_count(self) -> int:
        return sum(len(p.box.pieces) for p in self.boxes)

    @property
    def weight_kg(self) -> float:
        return self.box_count * BOX_WEIGHT_KG


def pack_pallets(boxes: List[Box]) -> List[PalletRow]:
    rows: List[PalletRow] = []

    by_depth = {}
    for box in boxes:
        by_depth.setdefault(box.depth_mm, []).append(box)

    for depth_mm, group in by_depth.items():
        group = sorted(group, key=lambda b: b.base_length_mm, reverse=True)
        row = None
        stack_used = 0
        stack_height_mm = 0.0
        depth_cap = max_boxes_by_depth(depth_mm)  # same depth for the whole group, so this doesn't change per box
        for box in group:
            needed_pallets = min(-(-int(box.base_length_mm) // PALLET_SIZE_MM), MAX_PALLETS_PER_ROW)  # ceil div, capped
            box_h = box_height_mm(box)
            exceeds_height_ceiling = stack_height_mm + box_h > (TOTAL_STACK_HEIGHT_CEILING_MM - PALLET_THICKNESS_MM)
            exceeds_depth_cap = depth_cap is not None and stack_used >= depth_cap
            if row is None or exceeds_height_ceiling or exceeds_depth_cap or needed_pallets > row.pallet_count:
                row = PalletRow(depth_mm=depth_mm, pallet_count=needed_pallets)
                rows.append(row)
                stack_used = 0
                stack_height_mm = 0.0
            placed = PlacedBox(box=box, x_mm=0, y_mm=0, z_mm=stack_height_mm)
            row.boxes.append(placed)
            stack_height_mm += box_h  # box heights vary, so stack on actual cumulative height, not a flat multiple
            stack_used += 1

    return rows


def total_pallets(rows: List[PalletRow]) -> int:
    return sum(r.pallet_count for r in rows)


def total_boxes(rows: List[PalletRow]) -> int:
    return sum(r.box_count for r in rows)


def total_hoods(rows: List[PalletRow]) -> int:
    return sum(r.hood_count for r in rows)


def total_weight_kg(rows: List[PalletRow]) -> float:
    return sum(r.weight_kg for r in rows)


def row_utilization(row: PalletRow) -> float:
    """Volume utilization: boxes' combined volume / the row's available
    pallet-footprint x max-stack-height volume. 0-1. Penalizes both an
    under-stacked row and boxes shorter than their row's pallet length -
    a single number for "how much of this row is actually earning its
    keep," not a promise about real packing efficiency (this heuristic
    doesn't try to minimize pallets, just reports how the greedy result
    came out)."""
    if not row.boxes:
        return 0.0
    used = sum(p.length_mm * p.width_mm * p.height_mm for p in row.boxes)
    available = row.row_length_mm * row.row_width_mm * (TOTAL_STACK_HEIGHT_CEILING_MM - PALLET_THICKNESS_MM)
    return used / available if available else 0.0


def row_fits(row: PalletRow, max_width_mm: float, max_height_mm: float) -> bool:
    """Width and height are hard per-row constraints - a row wider or
    taller than the vehicle can't fit no matter how rows are arranged.
    Length isn't checked here since multiple rows can sit side-by-side
    across the vehicle's width instead of only end to end - see the
    "if lined up end to end" total in the app for an approximate,
    conservative length reference instead of a hard per-row check."""
    return row.row_width_mm <= max_width_mm and row.row_height_mm <= max_height_mm
