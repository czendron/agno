"use client";

import { useEffect, useState } from "react";
import { analyzeJobCard, getJob, listJobs } from "@/lib/api";
import { EMPTY_PIECE, type JobFormState, type JobSummary, type Piece } from "@/lib/types";

const inputClass =
  "w-full rounded border border-brand-border bg-white px-2 py-1.5 text-sm text-foreground " +
  "focus:border-brand-black focus:outline-none focus:ring-1 focus:ring-brand-black";
const labelClass = "mb-1 block text-xs font-medium text-brand-gray";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className={labelClass}>{label}</span>
      {children}
    </label>
  );
}

interface SavedJobFile {
  job_id?: string;
  client?: string;
  h_sections?: number;
  joiners?: number;
  pieces?: Piece[];
}

interface SidebarProps {
  form: JobFormState;
  patch: (partial: Partial<JobFormState>) => void;
}

export function Sidebar({ form, patch }: SidebarProps) {
  const [examples, setExamples] = useState<JobSummary[]>([]);
  const [exampleChoice, setExampleChoice] = useState("-");
  const [exampleError, setExampleError] = useState<string | null>(null);

  const [jobCardFile, setJobCardFile] = useState<File | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);

  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    listJobs()
      .then(setExamples)
      .catch(() => setExampleError("Couldn't reach the API to load example jobs."));
  }, []);

  async function handleAnalyze() {
    if (!jobCardFile) return;
    setAnalyzing(true);
    setAiError(null);
    try {
      const result = await analyzeJobCard(jobCardFile);
      patch({ jobId: result.job_id, pieces: result.pieces });
    } catch (e) {
      setAiError(e instanceof Error ? e.message : "Couldn't read that job card.");
    } finally {
      setAnalyzing(false);
    }
  }

  async function handleExampleChange(value: string) {
    setExampleChoice(value);
    if (value === "-") return;
    setExampleError(null);
    try {
      const job = await getJob(value);
      patch({ jobId: job.job_id, client: job.client, pieces: job.pieces });
    } catch {
      setExampleError("Couldn't load that example job.");
    }
  }

  function handleSavedJobFile(file: File) {
    setLoadError(null);
    file
      .text()
      .then((text) => {
        const data = JSON.parse(text) as SavedJobFile;
        const pieces =
          data.pieces && data.pieces.length > 0
            ? data.pieces.map((p) => ({ ...EMPTY_PIECE, ...p }))
            : [{ ...EMPTY_PIECE }];
        patch({
          jobId: data.job_id ?? "",
          client: data.client ?? "",
          hSections: Number(data.h_sections ?? 0) || 0,
          joiners: Number(data.joiners ?? 0) || 0,
          pieces,
        });
      })
      .catch((e) => setLoadError(`Couldn't load that file: ${e instanceof Error ? e.message : e}`));
  }

  return (
    <aside className="w-full shrink-0 space-y-5 border-brand-border pr-0 text-sm md:w-72 md:border-r md:pr-6">
      <div>
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-brand-black">
          Job card
        </h2>
        <input
          type="file"
          accept="application/pdf"
          onChange={(e) => setJobCardFile(e.target.files?.[0] ?? null)}
          className="block w-full text-xs text-brand-gray file:mr-2 file:rounded file:border file:border-brand-border file:bg-white file:px-2 file:py-1 file:text-xs file:text-brand-black hover:file:bg-brand-surface"
        />
        <button
          type="button"
          onClick={handleAnalyze}
          disabled={!jobCardFile || analyzing}
          className="mt-2 w-full rounded bg-brand-black px-3 py-1.5 text-xs font-medium uppercase tracking-wide text-white disabled:cursor-not-allowed disabled:opacity-40"
        >
          {analyzing ? "Reading job card..." : "Analyze with AI"}
        </button>
        {aiError && <p className="mt-2 text-xs text-red-700">{aiError}</p>}
        <p className="mt-2 text-xs text-brand-gray">
          Drafts the table below from the PDF - always reviewed by a human before anything is
          computed, same as any other uncertain piece.
        </p>
      </div>

      <hr className="border-brand-border" />

      <div className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-brand-black">
          Job details
        </h2>
        <Field label="Job #">
          <input
            className={inputClass}
            value={form.jobId}
            onChange={(e) => patch({ jobId: e.target.value })}
          />
        </Field>
        <Field label="Client / Company">
          <input
            className={inputClass}
            value={form.client}
            onChange={(e) => patch({ client: e.target.value })}
          />
        </Field>
        <Field label="H Sections">
          <input
            type="number"
            min={0}
            step={1}
            className={inputClass}
            value={form.hSections}
            onChange={(e) => patch({ hSections: Number(e.target.value) || 0 })}
          />
        </Field>
        <Field label="Joiners">
          <input
            type="number"
            min={0}
            step={1}
            className={inputClass}
            value={form.joiners}
            onChange={(e) => patch({ joiners: Number(e.target.value) || 0 })}
          />
        </Field>
      </div>

      <hr className="border-brand-border" />

      <details className="group">
        <summary className="cursor-pointer text-sm font-semibold uppercase tracking-wide text-brand-black">
          Logistics assumptions (placeholders)
        </summary>
        <div className="mt-3 space-y-3">
          <Field label="Freight rate ($/pallet)">
            <input
              type="number"
              min={0}
              step={5}
              className={inputClass}
              value={form.freightRate}
              onChange={(e) => patch({ freightRate: Number(e.target.value) || 0 })}
            />
          </Field>
          <Field label="Truck max length (mm)">
            <input
              type="number"
              min={0}
              step={100}
              className={inputClass}
              value={form.truckLengthMm}
              onChange={(e) => patch({ truckLengthMm: Number(e.target.value) || 0 })}
            />
          </Field>
          <Field label="Truck max width (mm)">
            <input
              type="number"
              min={0}
              step={50}
              className={inputClass}
              value={form.truckWidthMm}
              onChange={(e) => patch({ truckWidthMm: Number(e.target.value) || 0 })}
            />
          </Field>
          <Field label="Truck max height (mm)">
            <input
              type="number"
              min={0}
              step={50}
              className={inputClass}
              value={form.truckHeightMm}
              onChange={(e) => patch({ truckHeightMm: Number(e.target.value) || 0 })}
            />
          </Field>
          <p className="text-xs text-brand-gray">
            All placeholder numbers (a generic semi-trailer) - set your real rate and vehicle
            dimensions.
          </p>
        </div>
      </details>

      <hr className="border-brand-border" />

      <div>
        <Field label="Or load an example job">
          <select
            className={inputClass}
            value={exampleChoice}
            onChange={(e) => handleExampleChange(e.target.value)}
          >
            <option value="-">-</option>
            {examples.map((job) => (
              <option key={job.job_id} value={job.job_id}>
                {job.job_id}
              </option>
            ))}
          </select>
        </Field>
        {exampleError && <p className="mt-2 text-xs text-red-700">{exampleError}</p>}
      </div>

      <hr className="border-brand-border" />

      <div>
        <Field label="Or load a saved job (.json)">
          <input
            type="file"
            accept="application/json"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleSavedJobFile(file);
              e.target.value = "";
            }}
            className="block w-full text-xs text-brand-gray file:mr-2 file:rounded file:border file:border-brand-border file:bg-white file:px-2 file:py-1 file:text-xs file:text-brand-black hover:file:bg-brand-surface"
          />
        </Field>
        {loadError && <p className="mt-2 text-xs text-red-700">{loadError}</p>}
      </div>
    </aside>
  );
}
