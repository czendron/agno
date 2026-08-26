"use client";

import dynamic from "next/dynamic";
import type { PalletsResponse } from "@/lib/types";

const Plot = dynamic(() => import("react-plotly.js"), {
  ssr: false,
  loading: () => (
    <div className="flex h-[480px] items-center justify-center text-sm text-brand-gray">
      Loading 3D view...
    </div>
  ),
});

interface Pallet3DViewProps {
  figure: PalletsResponse["plotly_figure"];
}

export function Pallet3DView({ figure }: Pallet3DViewProps) {
  return (
    <div className="rounded border border-brand-border">
      <Plot
        data={figure.data}
        layout={{ ...figure.layout, autosize: true, margin: { l: 0, r: 0, t: 10, b: 0 } }}
        useResizeHandler
        style={{ width: "100%", height: "480px" }}
        config={{ displaylogo: false, responsive: true }}
      />
    </div>
  );
}
