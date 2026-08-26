"""
Turns a job's boxes into a pallet layout for the 3D view.

Box physical dimensions (2026-08-26, Caio's placeholder numbers - change
freely, everything downstream reads from these two constants):
  - length = the box's own base_length_mm (already computed - the cut
    length formula in box_grouping.py)
  - width = depth = (that box's hood depth) + BOX_XY_CLEARANCE_MM
  - height = BOX_HEIGHT_MM, flat regardless of hood size

Pallets are PALLET_SIZE_MM squares; boxes lie with their length running
along a row of however many pallets get joined end to end
(ceil(length / PALLET_SIZE_MM) - not capped at 2, some boxes run past
8000mm). Boxes are grouped by depth (since width depends on depth) onto
separate rows, sorted longest-first, and stacked up to MAX_STACK_HIGH
per footprint before starting a new row. This is a greedy heuristic, not
an optimal packer - good enough to see the shape of a load, not a promise
of the fewest possible pallets.
"""

from dataclasses import dataclass, field
from typing import List

from box_order.box_grouping import Box

PALLET_SIZE_MM = 1200
BOX_XY_CLEARANCE_MM = 200
BOX_HEIGHT_MM = 600
MAX_STACK_HIGH = 2  # boxes stacked per footprint - placeholder, no real limit known yet


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
        return BOX_HEIGHT_MM


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


def pack_pallets(boxes: List[Box]) -> List[PalletRow]:
    rows: List[PalletRow] = []

    by_depth = {}
    for box in boxes:
        by_depth.setdefault(box.depth_mm, []).append(box)

    for depth_mm, group in by_depth.items():
        group = sorted(group, key=lambda b: b.base_length_mm, reverse=True)
        row = None
        stack_used = 0
        for box in group:
            needed_pallets = -(-int(box.base_length_mm) // PALLET_SIZE_MM)  # ceil div
            if row is None or stack_used >= MAX_STACK_HIGH or needed_pallets > row.pallet_count:
                row = PalletRow(depth_mm=depth_mm, pallet_count=needed_pallets)
                rows.append(row)
                stack_used = 0
            placed = PlacedBox(box=box, x_mm=0, y_mm=0, z_mm=stack_used * BOX_HEIGHT_MM)
            row.boxes.append(placed)
            stack_used += 1

    return rows


def total_pallets(rows: List[PalletRow]) -> int:
    return sum(r.pallet_count for r in rows)
