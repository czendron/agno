import type { GroupResponse, JobDetail, JobSummary, PalletsResponse, Piece } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function errorMessage(res: Response, fallback: string): Promise<string> {
  const text = await res.text().catch(() => "");
  if (!text) return fallback;
  try {
    const parsed = JSON.parse(text);
    if (parsed && typeof parsed.detail === "string") return parsed.detail;
  } catch {
    // not JSON - fall through to raw text
  }
  return text;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(await errorMessage(res, `Request failed: ${res.status}`));
  }
  return res.json();
}

export async function listJobs(): Promise<JobSummary[]> {
  const res = await fetch(`${API_URL}/api/jobs`);
  if (!res.ok) throw new Error(await errorMessage(res, "Couldn't load example jobs"));
  return res.json();
}

export async function getJob(jobId: string): Promise<JobDetail> {
  const res = await fetch(`${API_URL}/api/jobs/${encodeURIComponent(jobId)}`);
  if (!res.ok) throw new Error(await errorMessage(res, "Couldn't load that job"));
  return res.json();
}

export function groupPieces(pieces: Piece[]): Promise<GroupResponse> {
  return post("/api/group", { pieces });
}

export function computePallets(
  pieces: Piece[],
  freight_rate: number,
  truck_length_mm: number,
  truck_width_mm: number,
  truck_height_mm: number
): Promise<PalletsResponse> {
  return post("/api/pallets", { pieces, freight_rate, truck_length_mm, truck_width_mm, truck_height_mm });
}

export async function generateDwo(
  jobId: string,
  client: string,
  pieces: Piece[],
  hSections: number,
  joiners: number
): Promise<Blob> {
  const res = await fetch(`${API_URL}/api/generate-dwo`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_id: jobId, client, pieces, h_sections: hSections, joiners }),
  });
  if (!res.ok) {
    throw new Error(await errorMessage(res, "Couldn't generate the DWO file"));
  }
  return res.blob();
}

export function getLabelsHtml(
  jobId: string,
  pieces: Piece[]
): Promise<{ html: string; filename: string }> {
  return post("/api/labels", { job_id: jobId, client: "", pieces, h_sections: 0, joiners: 0 });
}

export async function analyzeJobCard(file: File): Promise<{ job_id: string; pieces: Piece[] }> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_URL}/api/analyze-job-card`, { method: "POST", body: form });
  if (!res.ok) {
    throw new Error(await errorMessage(res, "Couldn't analyze the job card"));
  }
  return res.json();
}
