"use client";

import { useState } from "react";
import { generateDwo, getLabelsHtml } from "@/lib/api";
import { downloadBlob, downloadText } from "@/lib/download";
import type { JobFormState, Piece } from "@/lib/types";

interface JobActionsProps {
  form: JobFormState;
  validPieces: Piece[];
}

export function JobActions({ form, validPieces }: JobActionsProps) {
  const [generating, setGenerating] = useState(false);
  const [generateError, setGenerateError] = useState<string | null>(null);
  const [generateSuccess, setGenerateSuccess] = useState<string | null>(null);

  const [labelsBusy, setLabelsBusy] = useState(false);
  const [labelsError, setLabelsError] = useState<string | null>(null);

  const canGenerate = Boolean(form.jobId) && Boolean(form.client);

  async function handleGenerate() {
    setGenerating(true);
    setGenerateError(null);
    setGenerateSuccess(null);
    try {
      const blob = await generateDwo(form.jobId, form.client, validPieces, form.hSections, form.joiners);
      const filename = `${form.jobId} - BOX ORDER.xlsx`;
      downloadBlob(blob, filename);
      setGenerateSuccess(
        `Generated ${filename} - every formula in the template is untouched, only data cells were filled.`
      );
    } catch (e) {
      setGenerateError(e instanceof Error ? e.message : "Couldn't generate the DWO file.");
    } finally {
      setGenerating(false);
    }
  }

  function handleSave() {
    const json = JSON.stringify(
      {
        job_id: form.jobId,
        client: form.client,
        h_sections: form.hSections,
        joiners: form.joiners,
        pieces: validPieces,
      },
      null,
      2
    );
    downloadText(json, `${form.jobId || "job"} - saved.json`, "application/json");
  }

  async function handleLabels() {
    setLabelsBusy(true);
    setLabelsError(null);
    try {
      const { html, filename } = await getLabelsHtml(form.jobId || "JOB", validPieces);
      downloadText(html, filename, "text/html");
    } catch (e) {
      setLabelsError(e instanceof Error ? e.message : "Couldn't build the labels.");
    } finally {
      setLabelsBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <div>
        {canGenerate ? (
          <button
            type="button"
            onClick={handleGenerate}
            disabled={generating}
            className="rounded bg-brand-black px-4 py-2 text-xs font-medium uppercase tracking-wide text-white disabled:cursor-not-allowed disabled:opacity-40"
          >
            {generating ? "Generating..." : "Generate Dispatch Works Order"}
          </button>
        ) : (
          <p className="text-sm text-brand-gray">
            Fill in Job # and Client in the sidebar to generate the Dispatch Works Order file.
          </p>
        )}
        {generateError && <p className="mt-2 text-sm text-red-700">{generateError}</p>}
        {generateSuccess && <p className="mt-2 text-sm text-green-700">{generateSuccess}</p>}
      </div>

      <hr className="border-brand-border" />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <button
            type="button"
            onClick={handleSave}
            className="rounded border border-brand-border px-4 py-2 text-xs font-medium uppercase tracking-wide text-brand-black hover:bg-brand-surface"
          >
            Save this job
          </button>
          <p className="mt-2 text-xs text-brand-gray">
            Downloads job details + pieces as a file - reload it later via &quot;Or load a saved
            job&quot; in the sidebar.
          </p>
        </div>
        <div>
          <button
            type="button"
            onClick={handleLabels}
            disabled={labelsBusy}
            className="rounded border border-brand-border px-4 py-2 text-xs font-medium uppercase tracking-wide text-brand-black hover:bg-brand-surface disabled:cursor-not-allowed disabled:opacity-40"
          >
            {labelsBusy ? "Preparing..." : "Download printable box labels"}
          </button>
          <p className="mt-2 text-xs text-brand-gray">
            One label per box, sized for the Dymo (101x54mm placeholder) - open the file and
            print once, instead of per-box copy/paste.
          </p>
          {labelsError && <p className="mt-2 text-sm text-red-700">{labelsError}</p>}
        </div>
      </div>
    </div>
  );
}
