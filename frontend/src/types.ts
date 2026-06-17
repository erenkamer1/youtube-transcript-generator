export interface Segment {
  start: number;
  end: number;
  text: string;
}

export interface TranscriptResult {
  id: number;
  url: string;
  title: string;
  duration: number | null;
  language: string | null;
  segments: Segment[];
  full_text: string;
}

export interface HistoryItem {
  id: number;
  url: string;
  title: string;
  duration: number | null;
  language: string | null;
  created_at: string;
  segment_count: number;
}

export interface OllamaModel {
  name: string;
  size: number | null;
}

export type PromptTemplate =
  | "detailed_notes"
  | "bullet_summary"
  | "rules_tips"
  | "study_guide"
  | "quiz";

export const PROMPT_TEMPLATE_LABELS: Record<PromptTemplate, string> = {
  detailed_notes: "Detaylı not çıkar",
  bullet_summary: "Madde madde özet",
  rules_tips: "Kurallar / püf noktaları",
  study_guide: "Çalışma rehberi",
  quiz: "Soru-cevap (quiz)",
};

export const TARGET_LANGUAGES = [
  "Turkish",
  "English",
  "German",
  "French",
  "Spanish",
  "Arabic",
  "Japanese",
  "Korean",
  "Russian",
  "Chinese",
];
