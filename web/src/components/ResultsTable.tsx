import type { BoxResult } from "@/lib/types";

interface ResultsTableProps {
  boxes: BoxResult[];
}

export function ResultsTable({ boxes }: ResultsTableProps) {
  const flaggedCount = boxes.filter((b) => b.flagged).length;

  return (
    <div>
      <h2 className="text-lg font-semibold text-brand-black">
        Result: {boxes.length} box{boxes.length !== 1 ? "es" : ""}
      </h2>
      {flaggedCount > 0 && (
        <p className="mt-2 rounded border border-brand-warning-bg bg-brand-warning-bg px-3 py-2 text-sm text-brand-warning">
          {flaggedCount} box{flaggedCount !== 1 ? "es need" : " needs"} a human check before
          dispatch.
        </p>
      )}
      <div className="mt-3 overflow-x-auto rounded border border-brand-border">
        <table className="w-full min-w-[760px] border-collapse text-sm">
          <thead>
            <tr className="border-b border-brand-border bg-brand-surface text-left text-xs uppercase tracking-wide text-brand-gray">
              <th className="px-2 py-2 font-medium">Box</th>
              <th className="px-2 py-2 font-medium">Hoods</th>
              <th className="px-2 py-2 font-medium">Depth (mm)</th>
              <th className="px-2 py-2 font-medium">Length H1</th>
              <th className="px-2 py-2 font-medium">Length H2</th>
              <th className="px-2 py-2 font-medium">Returns</th>
              <th className="px-2 py-2 font-medium">Base (mm)</th>
              <th className="px-2 py-2 font-medium">Lid (mm)</th>
              <th className="px-2 py-2 font-medium">Notes</th>
              <th className="px-2 py-2 font-medium">⚠</th>
            </tr>
          </thead>
          <tbody>
            {boxes.map((box) => (
              <tr
                key={box.box_number}
                className={`border-b border-brand-border last:border-b-0 ${
                  box.flagged ? "bg-brand-warning-bg" : ""
                }`}
              >
                <td className="px-2 py-1.5">{box.box_number}</td>
                <td className="px-2 py-1.5">{box.label}</td>
                <td className="px-2 py-1.5">{box.depth_mm}</td>
                <td className="px-2 py-1.5">{box.length_h1}</td>
                <td className="px-2 py-1.5">{box.length_h2 || ""}</td>
                <td className="px-2 py-1.5">{box.returns}</td>
                <td className="px-2 py-1.5">{box.base_mm}</td>
                <td className="px-2 py-1.5">{box.lid_mm}</td>
                <td className="px-2 py-1.5 text-brand-gray">{box.reasons.join("; ")}</td>
                <td className="px-2 py-1.5 whitespace-nowrap text-brand-warning">
                  {box.flagged ? "⚠️ CONFIRM" : ""}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
