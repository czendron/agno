# Heka Hoods — Box Order (Next.js front end)

The Next.js version of the Box Order app — same job data, same box-grouping
and pallet-loading rules as the Streamlit version at the repo root, served
through `box_order/api.py` instead of running Python directly. See
`../README.md` ("Two front ends") for how the two compare and how to run
them side by side.

This UI holds no business logic of its own: every computed value (box
groupings, pallet counts, DWO file, printable labels) comes from the
FastAPI backend in `../box_order/api.py`, which just calls the same
`box_order/*.py` code the Streamlit app imports directly.

## Running locally

Needs the API running first:

```bash
# from the repo root
uvicorn box_order.api:app --reload --port 8000
```

Then, in `web/`:

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). `NEXT_PUBLIC_API_URL`
in `.env.local` points the UI at the API (defaults to
`http://localhost:8000`).

For the "Analyze with AI" job-card upload, the API process needs
`ANTHROPIC_API_KEY` set in its environment.

## Structure

- `src/app/page.tsx` — the whole app: form state, debounced calls to
  `/api/group` and `/api/pallets` as pieces change, and the two-column
  layout.
- `src/components/` — one component per section (pieces table, sidebar,
  results table, pallet stats, 3D view, actions).
- `src/lib/api.ts` — typed fetch wrapper for every API endpoint.
- `src/lib/types.ts` — TypeScript types mirroring the API's Pydantic
  models.

## Deploying

Not yet deployed. Vercel is the natural target for this frontend, but
pairing it with the FastAPI backend needs a real hosting decision first —
see "Two front ends" in the root README.
