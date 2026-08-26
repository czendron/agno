import { formatCurrency, formatWeight } from "@/lib/format";
import type { PalletsResponse } from "@/lib/types";

interface PalletStatsProps {
  totals: PalletsResponse["totals"];
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded border border-brand-border bg-brand-surface px-3 py-2">
      <div className="text-xs uppercase tracking-wide text-brand-gray">{label}</div>
      <div className="mt-0.5 whitespace-nowrap text-xl font-semibold text-brand-black">
        {value}
      </div>
    </div>
  );
}

export function PalletStats({ totals }: PalletStatsProps) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      <Metric label="Pallets" value={totals.pallets} />
      <Metric label="Boxes" value={totals.boxes} />
      <Metric label="Hoods" value={totals.hoods} />
      <Metric label="Est. weight" value={formatWeight(totals.weight_kg)} />
      <Metric label="Est. freight" value={formatCurrency(totals.freight_cost)} />
    </div>
  );
}
