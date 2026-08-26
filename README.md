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
- `box_order/known_jobs.py` — piece dimensions for 7 real jobs, read off the
  Final Drawings / job card PDFs. Varying confidence — see file for which
  are confirmed.
- `box_order/verify_known_jobs.py` — runs the engine against those 7 jobs
  and checks results. Run with `python -m box_order.verify_known_jobs`.
- `box_order/write_to_template.py` — fills a copy of the real DWO template
  with a job's boxes. Every formula (box length, sorted print view, label
  sheets, DWO checklist) is left exactly as the template has it.
- `box_order/template/` — the real DWO template, as used by dispatch today.
- `box_order/palletizing.py` — greedy pallet-loading heuristic (see "Pallet
  layout" below).
- `box_order/plotly_view.py` — renders a pallet layout as a 3D Plotly figure.
- `box_order/ai_reader.py` — calls Claude to read a job card PDF and draft
  a piece list. Verified against two real job cards on 2026-08-26 — see
  the module docstring.
- `box_order/api.py` — FastAPI wrapper exposing the engine above as a REST
  API (`/api/group`, `/api/pallets`, `/api/generate-dwo`, `/api/labels`,
  `/api/analyze-job-card`, `/api/jobs`). Exists so the Next.js app can call
  the exact same tested Python logic instead of a second reimplementation
  in JS — every endpoint is a thin adapter, no business logic lives here.
- `streamlit_app.py` — one of two parallel front ends (see "Two front
  ends" below): upload a job card (or paste pieces by hand), see box
  groupings and a 3D pallet view live, download the finished DWO. Deploy
  via share.streamlit.io pointed at this repo, main file `streamlit_app.py`;
  needs `ANTHROPIC_API_KEY` in the app's secrets for the AI-read feature
  (everything else works without it).
- `web/` — the other front end: the same app rebuilt in Next.js
  (TypeScript, Tailwind, React), calling `box_order/api.py` instead of
  running Python directly. See "Two front ends" below.

## Two front ends

Same engine, same rules, same real data — two different UIs, built to
compare side by side rather than one replacing the other:

|                | Streamlit                          | Next.js                                  |
|----------------|-------------------------------------|-------------------------------------------|
| Where          | `streamlit_app.py`                  | `web/` (calls `box_order/api.py`)         |
| Runs on        | Python only                         | Python (API) + Node (UI)                  |
| Deploy target  | share.streamlit.io                  | Vercel (frontend) — API hosting TBD, see below |
| Business logic | Imports `box_order/` directly       | Same `box_order/` code, via HTTP          |

Both read and write the exact same job data, box-grouping engine, pallet
heuristic, DWO template, and label HTML — there is exactly one
implementation of the actual business rules (`box_order/*.py`); neither
front end re-derives box sizes or pallet counts on its own.

Run both locally, side by side:

```
# Terminal 1 - API (also powers the Next.js app)
uvicorn box_order.api:app --reload --port 8000

# Terminal 2 - Streamlit (talks to box_order/ directly, no API needed)
streamlit run streamlit_app.py

# Terminal 3 - Next.js (talks to the API on :8000)
cd web && npm install && npm run dev
```

Streamlit: http://localhost:8501 · Next.js: http://localhost:3000

**Deployment status:** neither is live yet. Streamlit's target
(share.streamlit.io) is the same one-click flow used for other internal
tools here; Next.js's natural target is Vercel for the frontend, same as
other projects, but pairing it with the FastAPI backend needs a real
hosting decision (Vercel's own Python functions, or a small separate host
for `box_order/api.py`) that hasn't been checked against Vercel's current
setup yet — don't assume either way until that's actually verified.

## Pallet layout

Box physical dimensions (2026-08-26, Caio's placeholder numbers, easy to
change — see `box_order/palletizing.py`):
- length = the box's own cut length (`base_length_mm`, from the formula
  above)
- width = depth = that box's hood depth + 200mm clearance
- height = 600mm flat, regardless of hood size

Pallets are 1200mm squares; a box's length determines how many pallets get
joined end to end in a row (`ceil(length / 1200)`, not capped at 2 — some
boxes already run past 8000mm). Boxes are grouped by depth (since width
depends on depth) onto separate rows and stacked up to 2 high per footprint.
This is a greedy heuristic, not an optimal packer — good enough to see the
shape of a load, not a promise of the fewest possible pallets. Known gap:
a box wider than 1200mm (any hood depth ≥ 1000mm) will overhang its pallet
in the view rather than span two pallets side-by-side — not handled yet.

Still no real answer on: max stack weight, or whether 2-high is actually
the right stacking limit — both are placeholders pending real numbers.

## Input methods

- **Web app** (`streamlit_app.py` or `web/` — see "Two front ends"): paste
  pieces into the table, or upload a job card PDF and have Claude draft the
  table (reviewed before anything computes).
- **Direct Python**: hardcoded `Piece()` lists, as in `known_jobs.py`.

No non-AI, non-Python input method exists (no CSV import, no manual Excel
input sheet) — not needed yet, add if it turns out to matter.

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
Caio confirmed: yes, it is a return, just a small one - a 100mm tab at
each angled corner (joined by hardware, an LJN, rather than welded).
Each piece gets 1 return per LJN corner it touches (0, 1, or 2, depending
on where it sits in the run - the plain in-line JN joints between straight
horizontal segments don't count, since there's no angle there). Since any
return forces solo (rule 3), this job is mostly solo boxes - 21, up from
an earlier miscount of 16 (which was also missing the 5th piece on hoods
3 and 4 - a separate bug this surfaced, now fixed in `known_jobs.py`).
Confirmed, not flagged - 0 pieces need review on this job now.

This is also a good example for "read the job card, extract pieces" being
a visual task rather than a text-parsing one (see "Open design questions"
below) - both the missing-piece bug and the returns question came from
reading the actual isometric drawing, not from any label that spelled it
out in words.

**Resolved 2026-08-26:** job HH19634N (Westbury Constructions) raised the
same "does this corner count as a return" question as Horizon, on a
different job card, and the answer came out *different* - a good sign the
two are genuinely separate cases, not one rule mis-applied twice. Its
hoods are the same 3-piece U-shape (2 legs + 1 top) as Horizon's simplest
hoods, but joined by plain JN hardware instead of Horizon's LJN. Caio
confirmed: here, each **leg** carries its own return (1, from a formed tab
at its end) and the **top piece carries none**, even though it touches a
JN corner at both ends - unlike Horizon, where a 3-piece hood's top piece
gets returns=2. Don't apply one job's rule to the other; both are recorded
as their own confirmed data point in `known_jobs.py`. All 10 boxes matched
Caio's box order exactly once this was applied - see
`verify_known_jobs.py`.

## Running it

```
python -m box_order.verify_known_jobs   # engine sanity check against 7 real jobs
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

- **AI job-card reading accuracy**: untested against a real job card end to
  end (see `ai_reader.py`). Every job card read by hand this session needed
  at least one correction after a closer look — expect the same from the
  AI draft, which is exactly why it's a draft shown for review, not
  auto-trusted.
- **Pallet numbers**: box clearance (200mm), height (600mm), and stack
  limit (2 high) are all placeholders — see "Pallet layout" above.
