"use client";

import { EMPTY_PIECE, type Piece } from "@/lib/types";

const inputClass =
  "w-full rounded border border-brand-border bg-white px-2 py-1 text-sm text-foreground " +
  "focus:border-brand-black focus:outline-none focus:ring-1 focus:ring-brand-black";

interface PiecesTableProps {
  pieces: Piece[];
  onChange: (pieces: Piece[]) => void;
}

export function PiecesTable({ pieces, onChange }: PiecesTableProps) {
  function update(index: number, patch: Partial<Piece>) {
    onChange(pieces.map((p, i) => (i === index ? { ...p, ...patch } : p)));
  }

  function remove(index: number) {
    onChange(pieces.filter((_, i) => i !== index));
  }

  function add() {
    onChange([...pieces, { ...EMPTY_PIECE }]);
  }

  return (
    <div>
      <div className="overflow-x-auto rounded border border-brand-border">
        <table className="w-full min-w-[900px] border-collapse text-sm">
          <thead>
            <tr className="border-b border-brand-border bg-brand-surface text-left text-xs uppercase tracking-wide text-brand-gray">
              <th className="px-2 py-2 font-medium">Hood ID</th>
              <th className="px-2 py-2 font-medium">Depth (mm)</th>
              <th className="px-2 py-2 font-medium">Length (mm)</th>
              <th className="px-2 py-2 font-medium">Orientation</th>
              <th className="px-2 py-2 text-center font-medium">Tapered</th>
              <th className="px-2 py-2 font-medium">Angle (°)</th>
              <th className="px-2 py-2 font-medium">Returns</th>
              <th className="px-2 py-2 text-center font-medium">Express</th>
              <th className="px-2 py-2 font-medium">Uncertain? (why, or blank)</th>
              <th className="px-2 py-2" />
            </tr>
          </thead>
          <tbody>
            {pieces.map((p, i) => (
              <tr key={i} className="border-b border-brand-border last:border-b-0">
                <td className="px-2 py-1.5">
                  <input
                    className={inputClass}
                    value={p.id}
                    onChange={(e) => update(i, { id: e.target.value })}
                    placeholder="e.g. 3A"
                  />
                </td>
                <td className="px-2 py-1.5">
                  <input
                    type="number"
                    min={0}
                    className={inputClass}
                    value={p.depth_mm}
                    onChange={(e) => update(i, { depth_mm: Number(e.target.value) || 0 })}
                  />
                </td>
                <td className="px-2 py-1.5">
                  <input
                    type="number"
                    min={0}
                    className={inputClass}
                    value={p.length_mm}
                    onChange={(e) => update(i, { length_mm: Number(e.target.value) || 0 })}
                  />
                </td>
                <td className="px-2 py-1.5">
                  <select
                    className={inputClass}
                    value={p.orientation}
                    onChange={(e) =>
                      update(i, { orientation: e.target.value as Piece["orientation"] })
                    }
                  >
                    <option value="regular">regular</option>
                    <option value="inverted">inverted</option>
                  </select>
                </td>
                <td className="px-2 py-1.5 text-center">
                  <input
                    type="checkbox"
                    className="h-4 w-4 accent-brand-black"
                    checked={p.tapered}
                    onChange={(e) => update(i, { tapered: e.target.checked })}
                  />
                </td>
                <td className="px-2 py-1.5">
                  <input
                    type="number"
                    min={0}
                    max={45}
                    className={inputClass}
                    value={p.angle_deg}
                    onChange={(e) => update(i, { angle_deg: Number(e.target.value) || 0 })}
                  />
                </td>
                <td className="px-2 py-1.5">
                  <input
                    type="number"
                    min={0}
                    max={2}
                    className={inputClass}
                    value={p.returns}
                    onChange={(e) => update(i, { returns: Number(e.target.value) || 0 })}
                  />
                </td>
                <td className="px-2 py-1.5 text-center" title="Express range (stock, not custom) - always 1 hood per box">
                  <input
                    type="checkbox"
                    className="h-4 w-4 accent-brand-black"
                    checked={p.is_express}
                    onChange={(e) => update(i, { is_express: e.target.checked })}
                  />
                </td>
                <td className="px-2 py-1.5">
                  <input
                    className={inputClass}
                    value={p.uncertain ?? ""}
                    onChange={(e) => update(i, { uncertain: e.target.value || null })}
                    placeholder=""
                  />
                </td>
                <td className="px-2 py-1.5">
                  <button
                    type="button"
                    onClick={() => remove(i)}
                    aria-label="Remove piece"
                    className="rounded px-2 py-1 text-brand-gray hover:bg-brand-surface hover:text-brand-black"
                  >
                    ×
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <button
        type="button"
        onClick={add}
        className="mt-2 rounded border border-brand-border px-3 py-1.5 text-sm text-brand-black hover:bg-brand-surface"
      >
        + Add piece
      </button>
    </div>
  );
}
