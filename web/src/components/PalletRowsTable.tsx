import { formatNumber, formatPercent } from "@/lib/format";
import type { PalletsResponse } from "@/lib/types";

interface PalletRowsTableProps {
  data: PalletsResponse;
}

export function PalletRowsTable({ data }: PalletRowsTableProps) {
  const badRows = data.rows.filter((r) => !r.fits_truck).map((r) => r.row);

  return (
    <div>
      {badRows.length > 0 && (
        <p className="mb-3 rounded border border-brand-warning-bg bg-brand-warning-bg px-3 py-2 text-sm text-brand-warning">
          Row{badRows.length !== 1 ? "s" : ""} {badRows.join(", ")} {badRows.length !== 1 ? "are" : "is"} wider
          or taller than the truck dimensions set in the sidebar.
        </p>
      )}
      {data.lined_up_length_mm > data.truck_length_mm && (
        <p className="mb-3 text-xs text-brand-gray">
          ⚠ If every row were lined up end to end, that&apos;s {formatNumber(data.lined_up_length_mm)}
          mm - longer than the {formatNumber(data.truck_length_mm)}mm truck length. Rows can sit
          side-by-side across the truck&apos;s width instead, so this isn&apos;t a hard fail - just a
          rough signal, not a real loading plan.
        </p>
      )}
      <p className="mb-2 text-xs text-brand-gray">
        Per pallet row (a row = however many 1200mm pallets are joined end to end for that row&apos;s
        longest box):
      </p>
      <div className="overflow-x-auto rounded border border-brand-border">
        <table className="w-full min-w-[720px] border-collapse text-sm">
          <thead>
            <tr className="border-b border-brand-border bg-brand-surface text-left text-xs uppercase tracking-wide text-brand-gray">
              <th className="px-2 py-2 font-medium">Row</th>
              <th className="px-2 py-2 font-medium">Pallets</th>
              <th className="px-2 py-2 font-medium">Boxes</th>
              <th className="px-2 py-2 font-medium">Hoods</th>
              <th className="px-2 py-2 font-medium">L (mm)</th>
              <th className="px-2 py-2 font-medium">W (mm)</th>
              <th className="px-2 py-2 font-medium">H (mm)</th>
              <th className="px-2 py-2 font-medium">Weight (kg)</th>
              <th className="px-2 py-2 font-medium">Utilization</th>
              <th className="px-2 py-2 font-medium">Fits truck?</th>
            </tr>
          </thead>
          <tbody>
            {data.rows.map((r) => (
              <tr key={r.row} className="border-b border-brand-border last:border-b-0">
                <td className="px-2 py-1.5">{r.row}</td>
                <td className="px-2 py-1.5">{r.pallets}</td>
                <td className="px-2 py-1.5">{r.boxes}</td>
                <td className="px-2 py-1.5">{r.hoods}</td>
                <td className="px-2 py-1.5">{formatNumber(r.length_mm)}</td>
                <td className="px-2 py-1.5">{formatNumber(r.width_mm)}</td>
                <td className="px-2 py-1.5">{formatNumber(r.height_mm)}</td>
                <td className="px-2 py-1.5">{formatNumber(r.weight_kg)}</td>
                <td className="px-2 py-1.5">{formatPercent(r.utilization)}</td>
                <td className="px-2 py-1.5">
                  {r.fits_truck ? "Yes" : <span className="text-brand-warning">No</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
