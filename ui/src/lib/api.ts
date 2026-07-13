import type {
  EvidenceCatalogResponse,
  EvidenceLabelMap,
  PredictionRequest,
  PredictionResponse,
} from "./types";

const apiUrl = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

async function getErrorMessage(response: Response, fallback: string): Promise<string> {
  const body = await response.json().catch(() => null) as { detail?: string } | null;
  return body?.detail ?? fallback;
}

export async function getEvidenceLabels(): Promise<EvidenceLabelMap> {
  const response = await fetch(`${import.meta.env.BASE_URL}evidence-labels.json`);
  if (!response.ok) throw new Error("Unable to load evidence labels.");
  const body = await response.json() as { value_labels?: EvidenceLabelMap };
  return body.value_labels ?? {};
}

export async function getEvidences(): Promise<EvidenceCatalogResponse> {
  const response = await fetch(`${apiUrl}/api/v1/evidences`);
  if (!response.ok) {
    throw new Error(await getErrorMessage(response, "Unable to load the evidence catalog."));
  }
  return response.json() as Promise<EvidenceCatalogResponse>;
}

export async function createPrediction(request: PredictionRequest): Promise<PredictionResponse> {
  const response = await fetch(`${apiUrl}/api/v1/predictions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    throw new Error(await getErrorMessage(response, "Unable to generate orientation results."));
  }
  return response.json() as Promise<PredictionResponse>;
}
