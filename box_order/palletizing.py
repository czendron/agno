"""
Turns a job's boxes into a pallet layout for the 3D view.

Box physical dimensions (2026-08-26, Caio's placeholder numbers - change
freely, everything downstream reads from these constants):
  - length = the box's own base_length_mm (already computed - the cut
    length formula in box_grouping.py)
  - width = depth = (that box's hood depth) + BOX_XY_CLEARANCE_MM
  - height = BOX_HEIGHT_BY_HOOD_COUNT[hoods in the box] - 150mm for a
    solo box, 200mm for a paired box (2026-08-26, Caio) - taller boxes
    hold more hoods, so height now depends on the box's own hood count,
    not a single flat number.

Pallets are PALLET_SIZE_MM squares; boxes lie with their length running
along a row of however many pallets get joined end to end
(ceil(length / PALLET_SIZE_MM) - not capped at 2, some boxes run past
8000mm). Boxes are grouped by depth (since width depends on depth) onto
separate rows, sorted longest-first, and stacked up to MAX_STACK_HIGH
per footprint before starting a new row - a stacked footprint can mix a
solo and a paired box, so stacking tracks each box's own actual height
rather than assuming a uniform one. This is a greedy heuristic, not an
optimal packer - good enough to see the shape of a load, not a promise of
the fewest possible pallets.

Weight (2026-08-26): BOX_WEIGHT_KG is a flat 15kg/box placeholder, not a
real calculation - Caio's explicit instruction was to stub this until an
actual weight formula exists (likely from hood depth/length/gauge, the
same inputs CALCULATIONS!D:F in the real template already uses for its
own weight estimate - see box_order/README.md). Swap BOX_WEIGHT_KG for a
per-box function once that's worked out; everything downstream (row and
job totals) just sums whatever this returns.
"""

from dataclasses import dataclass, field
from typing import List

from box_order.box_grouping import Box

PALLET_SIZE_MM = 1200
PALLET_THICKNESS_MM = 150  # pallet itself (the timber/plastic base), not a box - matches plotly_view's render
BOX_XY_CLEARANCE_MM = 200
BOX_HEIGHT_BY_HOOD_COUNT = {1: 150, 2: 200}  # keyed by hoods per box (rule 1 caps this at 2)
MAX_BOX_HEIGHT_MM = max(BOX_HEIGHT_BY_HOOD_COUNT.values())  # tallest a box can be - used as the utilization ceiling
MAX_STACK_HIGH = 2  # boxes stacked per footprint - placeholder, no real limit known yet
BOX_WEIGHT_KG = 15  # flat placeholder per box until real weight calc exists (2026-08-26)


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
        return BOX_HEIGHT_BY_HOOD_COUNT[len(self.box.pieces)]


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
        for box in group:
            needed_pallets = -(-int(box.base_length_mm) // PALLET_SIZE_MM)  # ceil div
            if row is None or stack_used >= MAX_STACK_HIGH or needed_pallets > row.pallet_count:
                row = PalletRow(depth_mm=depth_mm, pallet_count=needed_pallets)
                rows.append(row)
                stack_used = 0
                stack_height_mm = 0.0
            placed = PlacedBox(box=box, x_mm=0, y_mm=0, z_mm=stack_height_mm)
            row.boxes.append(placed)
            stack_height_mm += placed.height_mm  # box heights vary now, so stack on actual height, not a flat multiple
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
    available = row.row_length_mm * row.row_width_mm * (MAX_STACK_HIGH * MAX_BOX_HEIGHT_MM)
    return used / available if available else 0.0


def row_fits(row: PalletRow, max_width_mm: float, max_height_mm: float) -> bool:
    """Width and height are hard per-row constraints - a row wider or
    taller than the vehicle can't fit no matter how rows are arranged.
    Length isn't checked here since multiple rows can sit side-by-side
    across the vehicle's width instead of only end to end - see the
    "if lined up end to end" total in the app for an approximate,
    conservative length reference instead of a hard per-row check."""
    return row.row_width_mm <= max_width_mm and row.row_height_mm <= max_height_mm
