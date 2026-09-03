# Dispatch Desk

A single self-contained HTML file that turns pasted Smartsheet rows into ready-to-send
powder-coating dispatch emails. No build step, no server, no account, no internet
connection required — it's one file with inline CSS/JS, system fonts only, and zero
outbound network calls. Safe to run on a locked-down or air-gapped machine; every
row you paste stays on your computer, in your browser, for the life of the tab (plus
whatever `localStorage` remembers between visits, which also never leaves the machine).

## Use

1. Save/copy `index.html` to your computer and double-click it to open in any browser
   (Chrome, Edge, Firefox, Safari) — no install, no server, no login.
2. Copy one or more rows out of Smartsheet (as columns, tab-separated) and paste them
   into the text box. Multiple rows can be pasted at once — one email is generated per row.
3. Click **Generate emails**.
4. Review each generated email (they're editable — fix anything the parser guessed
   wrong, and always fill in the `[transit days]` placeholder, which is intentionally
   left blank since it isn't in the sheet).
5. Click **Copy email** to copy the body, or **Copy address** for the recipient.

Expected column order (matches the Smartsheet export):

```
primary, colour, total linear metres, square metres, PC drop date, PC completion date,
PC return date, PC notes, PC QA complete, site address, site contact, email address,
estimated dispatch date – week of, state
```

## Placeholder logic

- **First name** — first word of the first name on the site contact cell.
- **Site address** — the site address cell, stripped of any `Site Address:` label and
  of non-address lines (e.g. a project name with no street number/suburb/postcode).
- **Date & month** — the "estimated dispatch date – week of" cell, expanded to the
  Monday–Friday of that week (e.g. `21/09/26` → `September 21st – 25th`).
- **Transit days** — left as `[transit days]` on purpose; it isn't in the sheet, so fill
  it in by hand per order.
- **Suburb, state & postcode** — the full delivery address (not just the suburb/state/
  postcode, despite the placeholder's name) if the address cell has a separate
  `Delivery Address:` section, otherwise the same as the site address.
- **Site contact paragraph** — if a contact name is present, fills in the "we currently
  have X on Y" sentence; if the cell is empty, falls back to the "we're missing the
  contact's details" sentence.

Cards are flagged **Needs review** when something couldn't be parsed confidently (no
address found, unreadable date, missing contact/phone, etc.) so you know to double-check
before sending. The "Parsed data" disclosure on each card shows exactly what was
extracted.

Sender details (office phone, sender email, sender name) are editable under **Sender
details** and saved in your browser for next time. All parsing happens locally in the
browser — nothing is uploaded anywhere.
