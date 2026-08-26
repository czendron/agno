export interface Piece {
  id: string;
  depth_mm: number;
  length_mm: number;
  orientation: "regular" | "inverted";
  tapered: boolean;
  angle_deg: number;
  returns: number;
  uncertain: string | null;
}

export interface BoxResult {
  box_number: number;
  label: string;
  depth_mm: number;
  length_h1: number;
  length_h2: number;
  returns: number;
  base_mm: number;
  lid_mm: number;
  reasons: string[];
  flagged: boolean;
}

export interface GroupResponse {
  boxes: BoxResult[];
  flagged_count: number;
}

export interface PalletRowResult {
  row: number;
  pallets: number;
  boxes: number;
  hoods: number;
  length_mm: number;
  width_mm: number;
  height_mm: number;
  weight_kg: number;
  utilization: number;
  fits_truck: boolean;
}

export interface PalletsResponse {
  rows: PalletRowResult[];
  totals: {
    pallets: number;
    boxes: number;
    hoods: number;
    weight_kg: number;
    freight_cost: number;
  };
  lined_up_length_mm: number;
  truck_length_mm: number;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  plotly_figure: { data: any[]; layout: any };
}

export interface JobSummary {
  job_id: string;
  client: string;
}

export interface JobDetail extends JobSummary {
  pieces: Piece[];
}

export const EMPTY_PIECE: Piece = {
  id: "",
  depth_mm: 450,
  length_mm: 1200,
  orientation: "regular",
  tapered: false,
  angle_deg: 0,
  returns: 0,
  uncertain: null,
};

export interface JobFormState {
  jobId: string;
  client: string;
  hSections: number;
  joiners: number;
  pieces: Piece[];
  freightRate: number;
  truckLengthMm: number;
  truckWidthMm: number;
  truckHeightMm: number;
}

export const INITIAL_FORM_STATE: JobFormState = {
  jobId: "",
  client: "",
  hSections: 0,
  joiners: 0,
  pieces: [{ ...EMPTY_PIECE }],
  freightRate: 50,
  truckLengthMm: 13600,
  truckWidthMm: 2450,
  truckHeightMm: 2700,
};
