# Heka Hoods — Box Order Automation

Automates the "Dispatch Works Order" (DWO) box-packing step for Heka Hoods
(range hood manufacturer, Yandina QLD): given a job's hood dimensions, decide
which hoods share a box, compute box cut lengths, and fill a review copy of
the real DWO Excel template — the same file dispatch already prints and
feeds into the Dymo label printer, untouched downstream.

This consolidates two sources: the printed "Creating a Dispatch Works Order"
policy pages, and a working prototype (`box_grouping.py` / `write_to_template.py`
/ `run_known_jobs.py`) built in an earlier, now-lost conversation and
recovered from Google Drive on 2026-08-26. That prototype's rules were
validated against 6 real jobs and are more accurate than the printed policy
in places — see "Rules" below for where they disagree.

## What's here

- `box_order/box_grouping.py` — the grouping engine (`Piece`, `Box`,
  `group_into_boxes`). Pure logic, no file I/O.
- `box_order/known_jobs.py` — piece dimensions for 6 real jobs, read off the
  Final Drawings PDFs. Varying confidence — see file for which are confirmed.
- `box_order/verify_known_jobs.py` — runs the engine against those 6 jobs
  and checks results. Run with `python -m box_order.verify_known_jobs`.
- `box_order/write_to_template.py` — fills a copy of the real DWO template
  with a job's boxes. Every formula (box length, sorted print view, label
  sheets, DWO checklist) is left exactly as the template has it.
- `box_order/template/` — the real DWO template, as used by dispatch today.

Not built yet: any input method that isn't hand-written Python (the 6 known
jobs are hardcoded). No UI. No PDF parsing.

## Rules

**Box-per-hood counts, corner returns, custom hoods, reveal-hood depth** —
from the printed policy ("Creating a Dispatch Works Order", pages 2–5,
20.10.2023):
- Commercial Series: list 1 Return per hood with a Commercial Corner on one
  end, 2 if corners on both ends — this is what the DWO's `RETURNS` column
  (J) holds, and it feeds the box length formula below.
- Same depth only in a box (a HH450 and a HH600 never share a box).
- The longest hood in a box goes in `LENGTH H1`.
- Custom hoods: write `CUSTOM` in the notes column, speak to dispatch.
- Reveal hoods: use the O/D (outer dimension, including flange depth) for
  the `DEPTH` column, not the nominal hood size.

**Which hoods can share a box at all** — from the recovered prototype,
confirmed by Caio on 2026-08-12 against 6 real jobs (this supersedes the
printed policy's simpler "2 per box" / "1 per box" category list, which
doesn't handle angle, taper, or the returns/box-count interaction — see the
note below on where they disagree):
1. Max 2 hoods per box.
2. Only depth ≤600mm is even eligible to pair — deeper is always solo.
3. Solo-forced regardless of depth if: it has a welded return (any
   `RETURNS` > 0), it's tapered / non-standard shape, or it's angled
   (5–45° between flange and depth). Being mitred alone does *not* force
   solo — a mitred piece can still pair with a straight one.
4. **[Updated 2026-08-26]** Pairable pieces need only the same depth.
   Orientation no longer matters — standard (regular) and inverted hoods can
   now be paired together, same as any other 2-per-box combination. Before
   this date the prototype required matching orientation too; if you're
   comparing against anything generated before 2026-08-26, that's the
   difference.
5. The longer hood in a pair is listed first.
6. Among valid pairings, prefer the one that keeps box lengths across the
   job as close to equal as possible (confirmed as a general goal; applied
   by hand and inconsistently even by Caio today).

**Where the printed policy and the validated rules disagree:** the printed
policy lists Commercial Series Corner Hoods as a 2-per-box category, but
rule 3 above forces solo on *any* hood with a return, which includes
commercial corners. None of the 6 confirmed jobs exercise this exact case
(the ones with returns were also solo for other reasons — deep or angled),
so this hasn't actually been tested against a real commercial-corner job.
Trust rule 3 until proven otherwise, but flag it if a commercial-corner job
comes through and the box count looks wrong.

**Box cut length** — reverse-engineered directly from the real template's
`CALCULATIONS` and `BOX ORDER` tabs (not documented anywhere in writing
before now):
```
BASE (mm) = ROUNDUP(Length H1, -1) + (Returns × 100) + 350
LID  (mm) = BASE + 40
```
Depth does *not* factor into cut length in the current template, despite
the printed guide implying it should ("box cut length is auto calculated
based on the depth and length entered") — only length and returns actually
drive the formula.

**Known limitation:** when a same-depth pool has an odd number of pairable
pieces (3, 5, ...), the pairing algorithm always leaves the *middle* piece
solo. On job HH23104N this produces "2B & 1" solo "2A", where Caio's
confirmed answer was the opposite pairing ("2A & 1" solo "2B"). Box
dimensions come out identical either way (1548mm and 1549mm both round up
to 1550mm) — this has never caused a wrong-size box, only a possible wrong
hood ID on a box's paperwork. Not fixed, since guessing a general
tie-breaking rule from one example risks overfitting. See
`box_grouping.py` and `verify_known_jobs.py`.

**Still open / unconfirmed:**
- Whether the solo-forcing list (rule 3) is complete.
- Any box weight limit (none known).
- Whether the printed-policy/validated-rules disagreement above (commercial
  corners) is real or just an untested edge case.

**Resolved 2026-08-26:** job HH20143SA (Horizon)'s U-shaped hoods were
flagged uncertain - whether their vertical legs counted as "returns".
Checked against the real drawing: they're separate straight pieces joined
by a hardware L-shaped joiner, not a welded corner fold, so none of the
solo-forcing rules apply. Fixed in `known_jobs.py` (which also had a real
bug - hoods 3 and 4 are 5-piece runs, not 3-piece; the D piece was
missing). Box count for that job dropped from 16 to 13 as a result.

This is also the case for treating "read the job card, extract pieces" as
a visual task rather than a text-parsing one (see "Open design questions"
below) - this fix came from looking at the actual isometric drawing, not
from any label that said "not a return."

## Running it

```
python -m box_order.verify_known_jobs   # engine sanity check against 6 real jobs
```

```python
from box_order.box_grouping import Piece, group_into_boxes
from box_order.write_to_template import write_job

boxes = group_into_boxes([
    Piece("JOB123", "1", 450, 1200),
    Piece("JOB123", "2", 450, 1350),
])
write_job("JOB123", "Some Client", boxes,
          total_hoods=2, total_h_sections=0, total_joiners=0,
          out_name="JOB123 - BOX ORDER (auto-filled, review copy).xlsx")
```

## Open design questions (not yet decided)

- **Input**: hoods are hardcoded Python today. Real jobs should come from
  "Job Cards" — same hood drawings as the client-facing Final Drawings
  PDFs, minus client info — but no sample has been available to design a
  parser against yet.
- **Interface**: nothing built yet. Candidates discussed: a small local web
  UI (paste a hood list, see live box groupings, download the filled DWO),
  vs. staying script-only. Not settled.
