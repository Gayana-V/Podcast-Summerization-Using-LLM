export type ProcessingStage =
  | "uploaded"
  | "transcribing"
  | "diarizing"
  | "summarizing"
  | "tts"
  | "completed"
  | "failed";

export interface ProcessingStatus {
  job_id: string;
  stage: ProcessingStage;
  detail?: string | null;
  created_at: string;
  updated_at: string;
  errors: string[];
  assets: Record<string, string>;
}

export interface SpeakerTurn {
  speaker: string;
  start: number;
  end: number;
  text: string;
}

export interface TranscriptResult {
  language?: string;
  duration?: number;
  turns: SpeakerTurn[];
}

export interface SummarySection {
  speaker: string;
  highlights: string[];
}

export interface SummaryResult {
  overview: string;
  per_speaker: SummarySection[];
  key_points: string[];
}

export interface UploadResponse {
  job_id: string;
  status: ProcessingStatus;
}

export interface ProcessResponse {
  job_id: string;
  status: ProcessingStatus;
}

export interface ResultsResponse {
  job_id: string;
  status: ProcessingStatus;
  transcript?: TranscriptResult;
  summary?: SummaryResult;
  audio_url?: string;
  summary_audio_url?: string;
}


