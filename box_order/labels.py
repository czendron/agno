"""
Generates a print-ready HTML file of box labels - one per box, in box-number
order (matching the numbers already shown in the app's results table).
Open the downloaded file in a browser and print it with the Dymo selected
as the printer - @page is sized to the label, so each one lands on its own
physical label in a single print job, replacing the current copy-from-
Excel-paste-into-Dymo-Connect-per-box-then-delete-and-repeat workflow.

Label size (2026-08-26, placeholder): 101mm x 54mm, a common DYMO "large"
label size. Change LABEL_WIDTH_MM/LABEL_HEIGHT_MM if that's wrong for the
actual label stock in use - everything else follows from those two numbers.

Content and layout matches the real template's BOXING ORDER LABELS /
NUMERICAL LABELS sheets (job # / "BOX #" + number / "HOODS" + hood ID(s)),
just rendered as one label per printed page instead of one row per sheet.
"""

from typing import List

from box_order.box_grouping import Box

LABEL_WIDTH_MM = 101
LABEL_HEIGHT_MM = 54

_LABEL_TEMPLATE = """<div class="label">
  <div class="job">{job_id}</div>
  <div class="hdr">BOX #</div>
  <div class="box-num">{box_number}</div>
  <div class="hdr">HOODS</div>
  <div class="hoods">{hood_label}</div>
</div>"""

_PAGE_TEMPLATE = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{job_id} - Box Labels</title>
<style>
  @page {{ size: {width}mm {height}mm; margin: 0; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; }}
  .label {{
    width: {width}mm;
    height: {height}mm;
    padding: 4mm;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    page-break-after: always;
    text-align: center;
  }}
  .label:last-child {{ page-break-after: auto; }}
  .job {{ font-size: 15pt; font-weight: 700; }}
  .hdr {{ font-size: 8pt; letter-spacing: 0.15em; color: #666; margin-top: 3mm; }}
  .box-num {{ font-size: 22pt; font-weight: 700; }}
  .hoods {{ font-size: 15pt; font-weight: 700; }}
</style>
</head>
<body>
{labels}
</body>
</html>
"""


def box_labels_html(job_id: str, boxes: List[Box]) -> str:
    labels = "\n".join(
        _LABEL_TEMPLATE.format(job_id=job_id, box_number=i, hood_label=box.label)
        for i, box in enumerate(boxes, start=1)
    )
    return _PAGE_TEMPLATE.format(job_id=job_id, width=LABEL_WIDTH_MM, height=LABEL_HEIGHT_MM, labels=labels)
