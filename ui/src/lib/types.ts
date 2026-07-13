export type EvidenceType = "boolean" | "single_choice" | "multiple_choice";

export interface Evidence {
  id: string;
  type: EvidenceType;
  question: string;
  is_antecedent: boolean;
  default_values: string[];
  allowed_values: string[];
}

export interface EvidenceCatalogResponse {
  items: Evidence[];
  total: number;
}

export type EvidenceLabelMap = Record<string, Record<string, string>>;

export type FriendlyAnswer =
  | { evidence_id: string; present: true }
  | { evidence_id: string; value: string }
  | { evidence_id: string; values: string[] };

export interface PredictionRequest {
  age: number;
  sex: "F" | "M";
  answers: FriendlyAnswer[];
  top_k: number;
}

export interface Prediction {
  rank: number;
  pathology: string;
  probability: number;
}

export interface PredictionResponse {
  predictions: Prediction[];
  confidence: {
    maximum_probability: number;
    low_confidence: boolean;
    threshold: number;
  };
  input_summary: {
    age: number;
    sex: string;
    answer_count: number;
    generated_token_count: number;
  };
  model: { name: string };
  disclaimer: string;
}
