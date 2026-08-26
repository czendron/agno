"""
Runs the box-grouping engine against the 8 known jobs and checks results.

XP0096 / HH23173N / HH23341N / HH23104N / HH19634N / HH22246 are confirmed
- these are asserted strictly. HH22496N / HH20143SA are not fully confirmed
- these are printed for a human to review, not asserted, so this script
doesn't manufacture false confidence about them.

Run with: python -m box_order.verify_known_jobs
"""

from box_order.box_grouping import group_into_boxes, report
from box_order.known_jobs import JOBS

CONFIRMED = {
    "XP0096": ["1 & 2"],
    "HH23173N": ["1 & 2"],
    "HH23341N": ["2 & 1"],
    # Odd 3-piece pool at depth=600 (1, 2A, 2B): the longest (2B) goes
    # solo, the other two pair - see the odd-pool tie-break rule in
    # box_grouping.py (confirmed on HH22246, and it reproduces this result
    # exactly - this used to need a separate workaround check, see git log).
    "HH23104N": ["3", "2A & 1", "2B"],
    # Odd 3-piece pool, all depth=450: longest (3) goes solo, the other
    # two (1, 2) pair - the job that pinned down the odd-pool tie-break
    # rule above (Caio, 2026-08-26): "keep 3 alone and 2 and 1 together...
    # it won't change the sizes, but at least we balance the weight."
    "HH22246": ["2 & 1", "3"],
}
REVIEW_ONLY = {"HH22496N", "HH20143SA"}

FAILURES = []


def check_confirmed(job_id: str) -> None:
    boxes = group_into_boxes(JOBS[job_id])
    expected_labels = CONFIRMED[job_id]
    actual_labels = [b.label for b in boxes]
    if actual_labels == expected_labels:
        print(f"PASS  {job_id}: {actual_labels}")
    else:
        FAILURES.append(job_id)
        print(f"FAIL  {job_id}: expected {expected_labels}, got {actual_labels}")
    print(report(job_id, boxes))
    print()


def check_hh19634n() -> None:
    """Fully confirmed by Caio (2026-08-26): 10 boxes, exact labels, and
    base lengths that pin down the per-piece returns (legs=1, tops=0) -
    the part of this entry most likely to regress silently."""
    job_id = "HH19634N"
    boxes = group_into_boxes(JOBS[job_id])
    expected = [
        ("1A", 2270), ("1C", 2270), ("2A", 2270), ("2C", 2270),
        ("3A", 2140), ("3C", 2140), ("4A", 2140), ("4C", 2140),
        ("1B & 2B", 1170), ("3B & 4B", 1120),
    ]
    actual = [(b.label, b.base_length_mm) for b in boxes]
    if actual == expected:
        print(f"PASS  {job_id}: {[a[0] for a in actual]}")
    else:
        FAILURES.append(job_id)
        print(f"FAIL  {job_id}: expected {expected}, got {actual}")
    print(report(job_id, boxes))
    print()


def review_only(job_id: str) -> None:
    boxes = group_into_boxes(JOBS[job_id])
    flagged = [b for b in boxes if b.flagged]
    print(f"REVIEW  {job_id}: {len(boxes)} boxes, {len(flagged)} flagged for confirmation")
    print(report(job_id, boxes))
    print()


if __name__ == "__main__":
    for job_id in ["XP0096", "HH23173N", "HH23341N", "HH23104N", "HH22246"]:
        check_confirmed(job_id)
    check_hh19634n()
    for job_id in REVIEW_ONLY:
        review_only(job_id)

    if FAILURES:
        print(f"{len(FAILURES)} job(s) did not match confirmed results: {FAILURES}")
        raise SystemExit(1)
    print("All confirmed jobs match.")
