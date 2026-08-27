"use client";

import { useEffect, useMemo, useState } from "react";
import { Header } from "@/components/Header";
import { Sidebar } from "@/components/Sidebar";
import { PiecesTable } from "@/components/PiecesTable";
import { ResultsTable } from "@/components/ResultsTable";
import { JobActions } from "@/components/JobActions";
import { PalletStats } from "@/components/PalletStats";
import { Pallet3DView } from "@/components/Pallet3DView";
import { PalletRowsTable } from "@/components/PalletRowsTable";
import { computePallets, groupPieces } from "@/lib/api";
import {
  INITIAL_FORM_STATE,
  type GroupResponse,
  type JobFormState,
  type PalletsResponse,
} from "@/lib/types";

export default function Home() {
  const [form, setForm] = useState<JobFormState>(INITIAL_FORM_STATE);
  const [groupResult, setGroupResult] = useState<GroupResponse | null>(null);
  const [palletsResult, setPalletsResult] = useState<PalletsResponse | null>(null);
  const [computeError, setComputeError] = useState<string | null>(null);
  const [computing, setComputing] = useState(false);

  function patch(partial: Partial<JobFormState>) {
    setForm((f) => ({ ...f, ...partial }));
  }

  const validPieces = useMemo(
    () => form.pieces.filter((p) => p.id.trim().length > 0),
    [form.pieces]
  );

  useEffect(() => {
    if (validPieces.length === 0) {
      // Nothing to compute - the JSX below already falls back to the
      // "add a piece" message before it would read stale group/pallet
      // results, so there's no state to reset here.
      return;
    }
    let cancelled = false;
    const timer = setTimeout(() => {
      setComputing(true);
      Promise.all([
        groupPieces(validPieces),
        computePallets(
          validPieces,
          form.freightRate,
          form.truckLengthMm,
          form.truckWidthMm,
          form.truckHeightMm
        ),
      ])
        .then(([group, pallets]) => {
          if (cancelled) return;
          setGroupResult(group);
          setPalletsResult(pallets);
          setComputeError(null);
        })
        .catch((e) => {
          if (cancelled) return;
          setComputeError(
            e instanceof Error ? e.message : "Couldn't reach the API - is it running?"
          );
        })
        .finally(() => {
          if (!cancelled) setComputing(false);
        });
    }, 300);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [validPieces, form.freightRate, form.truckLengthMm, form.truckWidthMm, form.truckHeightMm]);

  return (
    <div className="mx-auto max-w-[1400px] px-6 py-8">
      <Header />
      <div className="flex flex-col gap-8 md:flex-row">
        <Sidebar form={form} patch={patch} />

        <main className="min-w-0 flex-1">
          {computeError && validPieces.length > 0 && (
            <p className="mb-4 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {computeError}
            </p>
          )}

          <div className="grid grid-cols-1 gap-8 lg:grid-cols-5">
            <div className="space-y-6 lg:col-span-3">
              <div>
                <h2 className="text-lg font-semibold text-brand-black">Pieces</h2>
                <p className="mt-1 text-xs text-brand-gray">
                  One row per piece. Leave &quot;uncertain&quot; blank when you&apos;re confident
                  about a piece&apos;s shape/return/angle; fill it in if you&apos;re not sure -
                  that piece goes solo and gets flagged, instead of being silently grouped.
                </p>
                <div className="mt-3">
                  <PiecesTable pieces={form.pieces} onChange={(pieces) => patch({ pieces })} />
                </div>
              </div>

              {validPieces.length === 0 ? (
                <p className="rounded border border-brand-border bg-brand-surface px-3 py-2 text-sm text-brand-gray">
                  Add at least one piece above (or upload a job card) to see box groupings.
                </p>
              ) : groupResult ? (
                <>
                  <ResultsTable boxes={groupResult.boxes} />
                  <hr className="border-brand-border" />
                  <JobActions form={form} validPieces={validPieces} />
                </>
              ) : (
                computing && <p className="text-sm text-brand-gray">Computing...</p>
              )}
            </div>

            <div className="space-y-4 lg:col-span-2">
              <h2 className="text-lg font-semibold text-brand-black">Pallet load</h2>
              {palletsResult ? (
                <>
                  <PalletStats totals={palletsResult.totals} />
                  <Pallet3DView figure={palletsResult.plotly_figure} />
                  <PalletRowsTable data={palletsResult} />
                  <p className="text-xs text-brand-gray">
                    Box size = that box&apos;s hood depth + 200mm (width/depth), 170mm height, or
                    260mm if the box has a return. Max 2 boxes stacked per footprint, max 2 pallets
                    end to end per row (a longer box overhangs rather than getting a 3rd pallet).
                    Weight is a flat 15kg/box placeholder until a
                    real formula replaces it. Utilization = boxes&apos; volume / the row&apos;s
                    available pallet-footprint x max-stack-height volume - a low number means
                    that row is carrying less than it could. All placeholder numbers - tell me and
                    I&apos;ll change them.
                  </p>
                </>
              ) : (
                validPieces.length > 0 &&
                computing && <p className="text-sm text-brand-gray">Computing...</p>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
